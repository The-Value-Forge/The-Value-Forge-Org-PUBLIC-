"""art_sync.py — syncs curated artwork from the Drive Art Pool into the repo.

Reads all posts in content/signal, content/synthesis, content/monthly that
don't already have a card_image: frontmatter key. Assigns an image from the
Art Pool (Drive) using title keyword matching against post content, falling
back to least-recently-uploaded (createdTime order) within the domain pool.
Downloads assigned images to assets/images/cards/<domain>/.
Updates data/card_art.json manifest.

data/card_art.json IS THE ASSIGNMENT RECORD. This script does NOT write
card_image: into content files, and must never be changed to do so.
`layouts/partials/card-art.html` resolves the manifest by slug at render time,
so an assignment is already fully effective without touching the post.

Why it matters (diagnosed 27 Jul 2026): content files under content/signal,
content/synthesis and content/monthly are owned by drive_sync.py, which
overwrites them wholesale from Drive. Drive originals carry no card_image, so
anything injected here was destroyed on the next run. The two scripts run in
the same workflow, so every real sync was followed by a *strip-only* commit
carrying zero new content — which still defeated the `git diff --staged
--quiet` guard, still pushed, and still triggered a full production build.
It roughly doubled the site's deploy count. Measured oscillation on `main`:
12 Jul +5 / 13 Jul −5, 19 Jul +13 / −13, 26 Jul +12 / 27 Jul −12.

A human-authored card_image: in a post is still honoured — it is priority 1 in
the render partial, and posts carrying one are skipped for assignment below.
drive_sync.py preserves it across overwrites so the pin is durable.

Images are shown as a SLUG-SEEDED CROP — background-position is calculated
from the post slug so every card shows a different section of its image.
This gives variety even when multiple posts share the same source image.

Assignment priority:
  1. card_image: in frontmatter — manual pin, never overwritten.
  2. Existing entry in data/card_art.json — stable once assigned.
  3. Keyword match: image title words scored against post title + description.
  4. LRU by createdTime: oldest-unassigned image in domain pool.
  5. Wrap: reuse least-recently-used when pool exhausted.

Required env vars:
  GDRIVE_SERVICE_ACCOUNT_KEY  JSON key for a GCP service account.
  ART_POOL_FOLDER_ID          Drive folder ID for the Art Pool root.
"""
import io
import json
import os
import re
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

CONTENT_DIRS = [
    Path("content/signal"),
    Path("content/synthesis"),
    Path("content/monthly"),
]
MANIFEST_PATH = Path("data/card_art.json")
ASSET_BASE = Path("assets/images/cards")

DOMAIN_FOLDERS = {
    "d01": "d01--acute-frailty",
    "d02": "d02--clinical-psychology",
    "d03": "d03--palliative-care",
    "d04": "d04--therapies-ahps",
    "d05": "d05--opat",
    "cross": "cross--synthesis-multi-domain",
}


# ── Frontmatter helpers ───────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    fm = {}
    in_fm = False
    for line in text.splitlines():
        if line.strip() == "---":
            if not in_fm:
                in_fm = True
                continue
            else:
                break
        if not in_fm:
            continue
        # Top-level keys only: indented lines belong to nested blocks (e.g. the
        # title:/container: sub-fields of sources: entries) and must not clobber
        # the post's own title/description used for art keyword matching.
        if line != line.lstrip() or line.lstrip().startswith("- "):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if val.startswith("["):
                items = re.findall(r'"([^"]+)"', val)
                fm[key] = items
            elif val:
                fm[key] = val
    return fm


# ── Scoring — image title keywords vs post content ────────────────────────────

def extract_words(text: str) -> set:
    stopwords = {"the","a","an","of","in","on","at","to","for","and","or","not",
                 "is","as","by","with","from","this","that","it","its","be","are",
                 "was","were","has","have","had","may","than","per","vs","no","nhs",
                 "d1","d2","d3","d4","d5","domain","acute","frailty"}
    words = set(re.split(r"[\s\-_,;:.()\[\]/]+", text.lower()))
    return {w for w in words if len(w) > 3 and w not in stopwords}


def score_image(post_words: set, image_title: str) -> int:
    """Score an image by how many of its title words appear in the post."""
    return len(post_words & extract_words(image_title))


# ── Safe filename: strip special chars for local storage ─────────────────────

def safe_filename(title: str) -> str:
    """Convert a Drive title like 'D1 - Functional and Physical.png' to a safe filename."""
    stem = Path(title).stem
    ext = Path(title).suffix.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return f"{slug}{ext}"


# ── Drive helpers ─────────────────────────────────────────────────────────────

def list_folder(service, folder_id: str) -> list[dict]:
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType, createdTime)",
            orderBy="createdTime asc",
            pageSize=500,
        )
        .execute()
    )
    return results.get("files", [])


def download(service, file_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = dl.next_chunk()
    dest.write_bytes(buf.getvalue())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    key_json = os.environ.get("GDRIVE_SERVICE_ACCOUNT_KEY")
    pool_folder_id = os.environ.get("ART_POOL_FOLDER_ID")
    if not key_json or not pool_folder_id:
        print("ART_SYNC: ART_POOL_FOLDER_ID or GDRIVE_SERVICE_ACCOUNT_KEY not set — skipping.")
        return

    creds = service_account.Credentials.from_service_account_info(
        json.loads(key_json),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    manifest = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}
    assignments = manifest.get("assignments", {})
    last_used = manifest.get("last_used", {k: None for k in DOMAIN_FOLDERS})

    # Build pool: { domain: [ {id, title, safe_name, created} ] }
    pool_items = list_folder(service, pool_folder_id)
    domain_folder_ids = {}
    for item in pool_items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            for domain, folder_name in DOMAIN_FOLDERS.items():
                if item["name"] == folder_name:
                    domain_folder_ids[domain] = item["id"]

    pool: dict[str, list[dict]] = {}
    for domain, fid in domain_folder_ids.items():
        images = []
        for f in list_folder(service, fid):
            if re.search(r"\.(webp|jpg|jpeg|png)$", f["name"], re.I):
                images.append({
                    "id": f["id"],
                    "title": f["name"],
                    "safe_name": safe_filename(f["name"]),
                    "created": f.get("createdTime", ""),
                })
        # Already sorted by createdTime asc from Drive
        pool[domain] = images
        print(f"ART_SYNC: pool {domain} — {len(images)} image(s)")

    if not any(pool.values()):
        print("ART_SYNC: Art Pool is empty — skipping.")
        return

    # Collect posts needing assignment
    posts = []
    for d in CONTENT_DIRS:
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md")):
            if md.name == "_index.md":
                continue
            text = md.read_text()
            fm = parse_frontmatter(text)
            if fm.get("card_image"):
                continue
            slug = md.stem
            posts.append({"path": md, "slug": slug, "fm": fm})

    assigned_count = 0
    downloaded_count = 0

    for post in posts:
        slug = post["slug"]
        fm = post["fm"]

        # Already in manifest — ensure downloaded
        if slug in assignments:
            entry = assignments[slug]  # "d01/safe-filename.png"
            domain = entry.split("/")[0]
            filename = entry.split("/")[1]
            dest = ASSET_BASE / domain / filename
            if not dest.exists():
                matching = [img for img in pool.get(domain, []) if img["safe_name"] == filename]
                if matching:
                    print(f"ART_SYNC: re-downloading {entry}")
                    download(service, matching[0]["id"], dest)
                    downloaded_count += 1
            continue

        # Determine domain
        domains_list = fm.get("domain", [])
        if isinstance(domains_list, str):
            domains_list = [domains_list]
        if len(domains_list) == 1 and domains_list[0] in DOMAIN_FOLDERS:
            primary = domains_list[0]
        else:
            primary = "cross"

        domain_pool = pool.get(primary, [])
        if not domain_pool:
            domain_pool = pool.get("cross", [])
            if domain_pool:
                primary = "cross"
            else:
                print(f"ART_SYNC: no images for {primary} — skipping {slug}")
                continue

        # Already-assigned safe names for this domain
        assigned_names = {
            v.split("/")[1]
            for k, v in assignments.items()
            if v.startswith(primary + "/")
        }
        unused = [img for img in domain_pool if img["safe_name"] not in assigned_names]

        # Score by title keyword match
        words = extract_words(f"{fm.get('title','')} {fm.get('description','')}")
        candidate = None
        if words and unused:
            scored = sorted(unused, key=lambda img: score_image(words, img["title"]), reverse=True)
            if score_image(words, scored[0]["title"]) > 0:
                candidate = scored[0]

        if candidate is None:
            # LRU: oldest unused, or wrap by rotating the pool
            if unused:
                candidate = unused[0]  # oldest by createdTime
            else:
                # Pool exhausted: continue the rotation from last_used — take the
                # NEXT image in createdTime order (wrapping), so repeats cycle
                # through the whole pool instead of pinning one image forever.
                lu = last_used.get(primary)
                names = [img["safe_name"] for img in domain_pool]
                if lu in names:
                    candidate = domain_pool[(names.index(lu) + 1) % len(domain_pool)]
                else:
                    candidate = domain_pool[0]

        entry = f"{primary}/{candidate['safe_name']}"
        assignments[slug] = entry
        last_used[primary] = candidate["safe_name"]
        assigned_count += 1

        dest = ASSET_BASE / primary / candidate["safe_name"]
        if not dest.exists():
            print(f"ART_SYNC: downloading {entry} for {slug}")
            download(service, candidate["id"], dest)
            downloaded_count += 1

        # Deliberately no write to the post file: the manifest below is the
        # record and the render partial reads it. See the module docstring.
        print(f"ART_SYNC: assigned {entry} → {slug}")

    manifest["assignments"] = assignments
    manifest["last_used"] = last_used
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"ART_SYNC: done — {assigned_count} new assignment(s), {downloaded_count} downloaded.")


if __name__ == "__main__":
    main()
