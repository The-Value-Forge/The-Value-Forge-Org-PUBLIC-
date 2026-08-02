"""drive_sync.py — downloads translated content from TVF-PUBLIC-OUTPUT Drive folder
into the Hugo content tree.

File routing (translator must follow this naming convention):
  signal--YYYY-MM-DD-slug.md     → content/signal/YYYY-MM-DD-slug.md
  synthesis--YYYY-MM-DD-slug.md  → content/synthesis/YYYY-MM-DD-slug.md
  monthly--YYYY-MM-slug.md       → content/monthly/YYYY-MM-slug.md
  patterns.json                  → data/patterns.json (full replacement, GUARDED — see below)
  patterns-delta-YYYY-MM.json    → merged into data/patterns.json (translator v3.5+)

The pattern register (data/patterns.json) is the site's only cumulative,
irreplaceable dataset — a longitudinal record that is append-only by nature.
Two protections (docs/PATTERNS-LONGITUDINAL-DESIGN-2026-07.md):

  MONOTONIC GUARDS — a full patterns.json that loses an existing pattern id,
  shrinks or drops any pattern's history entries, rewrites first_appeared, or
  carries an older `generated` date than the current file is HELD (not
  written), loudly, in the Action log + step summary. Prevents one bad
  regeneration cycle from silently corrupting a year of record.

  DELTA MERGE — translator v3.5+ emits patterns-delta-YYYY-MM.json (new
  patterns / new history entries / status updates only) instead of re-writing
  the whole file. Deltas are merged append-only and idempotently; multiple
  deltas apply in month order. Full-file replacement stays supported (guarded)
  for v3.4 compatibility.

Required env vars:
  GDRIVE_SERVICE_ACCOUNT_KEY  JSON key for a GCP service account with Drive read access.
  GDRIVE_FOLDER_ID            ID of the Drive folder to sync from.
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

ROUTING = {
    "signal--":    Path("content/signal"),
    "synthesis--": Path("content/synthesis"),
    "monthly--":   Path("content/monthly"),
}

PATTERNS_PATH = Path("data/patterns.json")
PATTERNS_DELTA_RE = re.compile(r"^patterns-delta-\d{4}-\d{2}\.json$")
PMID_RE = re.compile(r"\bPMID[:\s]*\d{7,9}\b|\bPMIDs?[^)]*\d{7,9}", re.I)

# Frontmatter fields the translator must emit per artefact type (charter §6).
# Checked warn-only after download: the site degrades gracefully, but a missing
# domain/domains makes the post invisible on domain pages and the Evidence
# Timeline (the 19 Jun 2026 batch defect), so surface it loudly in the Action
# log rather than shipping it silently.
FRONTMATTER_REQUIRED = {
    "signal--":    ["domains", "domain", "evidence_label", "finding_status"],
    "synthesis--": ["domains", "domain", "evidence_label"],
}

# Known-bad Drive originals: the 19 Jun 2026 batch with uncorrected frontmatter.
# Corrected same-name copies were uploaded 3 Jul 2026; until the originals are
# trashed in Drive they must never overwrite the corrected copies (CLAUDE.md
# action 2a). Safe to remove this list once they are trashed.
DENYLIST_IDS = {
    "1PU9OcPM5G3r-l9vcEvkluM-U7Q6sizgj",  # signal--2026-06-19-acp-gap-severe-frailty-convergence.md
    "11Bl_25VJvsVITH8xMDKZK9OvWTugREYa",  # signal--2026-06-19-homehealth original
    "1jGKl_tXuP-IZKCzJmyNOiAoI3V-oMzGn",  # signal--2026-06-19-opat-oral-switch original
    "1DgwRZbrjXN3hYdQ5cuRy5uOXFDhJs9DF",  # synthesis--2026-06-19-week-ending-19-june.md
}


def check_frontmatter(name: str, data: bytes) -> list[str]:
    """Return warnings for missing or scalar-shaped required frontmatter fields."""
    required = next((v for k, v in FRONTMATTER_REQUIRED.items() if name.startswith(k)), None)
    if not required:
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [f"{name}: content is not valid UTF-8"]
    fm_block = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not fm_block:
        return [f"{name}: no YAML frontmatter block found"]
    warnings = []
    for field in required:
        m = re.search(rf"^{field}:\s*(.*)$", fm_block.group(1), re.M)
        if not m:
            detail = " — post will be INVISIBLE on domain pages and the timeline" \
                if field in ("domain", "domains") else ""
            warnings.append(f"{name}: missing '{field}:'{detail}")
        elif not m.group(1).strip().startswith("["):
            warnings.append(
                f"{name}: '{field}:' is a scalar, expected a [list] "
                "(site tolerates it; the translator should emit a list)"
            )
    return warnings


def _entry_has_reference(entry: dict) -> bool:
    """True if a history entry carries any reference: structured references,
    supporting site-content slugs, or a PMID in the note prose."""
    if entry.get("references") or entry.get("supporting"):
        return True
    return bool(PMID_RE.search(entry.get("note", "") or ""))


def reference_warnings(incoming: dict, current: dict | None) -> list[str]:
    """Warn for history entries NEW relative to `current` that carry no
    reference of any kind. Patterns are the site's most consequential claims;
    an unreferenced register entry violates the static-copy rule in spirit
    (charter §8; docs/PATTERNS-LONGITUDINAL-DESIGN-2026-07.md §2)."""
    existing: set[tuple[str, str]] = set()
    if current:
        for p in current.get("patterns", []):
            for h in p.get("history", []):
                existing.add((p.get("id", ""), h.get("date", "")))
    warnings = []
    for p in incoming.get("patterns", []):
        for h in p.get("history", []):
            if (p.get("id", ""), h.get("date", "")) in existing:
                continue
            if not _entry_has_reference(h):
                warnings.append(
                    f"patterns: {p.get('id', '?')} history {h.get('date', '?')} has NO references "
                    "(no PMID, no structured references, no supporting slugs) — v3.5 requires them"
                )
    return warnings


def validate_patterns_full(data: bytes, current_path: Path) -> tuple[list[str], list[str]]:
    """Monotonic guards for a FULL patterns.json replacement.
    Returns (errors, warnings); any error means HOLD the file."""
    errors: list[str] = []
    try:
        incoming = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return [f"patterns.json: not valid JSON ({e}) — HELD"], []
    pats = incoming.get("patterns")
    if not isinstance(pats, list) or not all(isinstance(p, dict) and p.get("id") for p in pats):
        return ["patterns.json: 'patterns' must be a list of objects each carrying an 'id' — HELD"], []

    current = None
    if current_path.exists():
        try:
            current = json.loads(current_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = None  # unreadable current file: nothing to guard against

    if current:
        inc_by_id = {p["id"]: p for p in pats}
        if incoming.get("generated") and current.get("generated") \
                and incoming["generated"] < current["generated"]:
            errors.append(
                f"patterns.json: generated {incoming['generated']} is OLDER than current "
                f"{current['generated']} (stale file) — HELD"
            )
        for cp in current.get("patterns", []):
            pid = cp.get("id")
            ip = inc_by_id.get(pid)
            if ip is None:
                errors.append(f"patterns.json: existing pattern {pid} DISAPPEARED — HELD")
                continue
            cur_hist = cp.get("history", [])
            inc_dates = {h.get("date") for h in ip.get("history", [])}
            lost = [h.get("date") for h in cur_hist if h.get("date") not in inc_dates]
            if lost:
                errors.append(
                    f"patterns.json: {pid} would LOSE history entr{'y' if len(lost) == 1 else 'ies'} "
                    f"{', '.join(map(str, lost))} — the record is append-only — HELD"
                )
            if cp.get("first_appeared") and ip.get("first_appeared") != cp.get("first_appeared"):
                errors.append(
                    f"patterns.json: {pid} first_appeared would change "
                    f"{cp['first_appeared']} → {ip.get('first_appeared')} — HELD"
                )
    return errors, reference_warnings(incoming, current)


def merge_patterns_delta(current: dict, delta: dict) -> tuple[dict, list[str], list[str]]:
    """Append-only, idempotent merge of a patterns-delta file into the register.
    New patterns are appended; new history entries (unseen (id, date)) are
    appended and sorted; status/confirmation_level/domains/title update to the
    delta's values; first_appeared is immutable once set. Returns
    (merged, errors, warnings) — errors are per-entry and skip that entry only."""
    errors: list[str] = []
    dpats = delta.get("patterns")
    if not isinstance(dpats, list) or not all(isinstance(p, dict) and p.get("id") for p in dpats):
        return current, ["patterns-delta: 'patterns' must be a list of objects each carrying an 'id' — delta SKIPPED"], []

    merged = json.loads(json.dumps(current))  # deep copy; never mutate caller's dict
    by_id = {p["id"]: p for p in merged.get("patterns", [])}
    for dp in dpats:
        pid = dp["id"]
        cp = by_id.get(pid)
        if cp is None:
            if not dp.get("first_appeared") or not dp.get("history"):
                errors.append(f"patterns-delta: new pattern {pid} missing first_appeared/history — entry skipped")
                continue
            merged.setdefault("patterns", []).append(dp)
            by_id[pid] = dp
            continue
        if dp.get("first_appeared") and dp["first_appeared"] != cp.get("first_appeared"):
            errors.append(
                f"patterns-delta: {pid} attempts to change first_appeared "
                f"{cp.get('first_appeared')} → {dp['first_appeared']} — ignored (immutable)"
            )
        seen_dates = {h.get("date") for h in cp.get("history", [])}
        for h in dp.get("history", []):
            if h.get("date") not in seen_dates:
                cp.setdefault("history", []).append(h)
                seen_dates.add(h.get("date"))
        cp["history"] = sorted(cp["history"], key=lambda h: h.get("date", ""))
        for field in ("status", "confirmation_level", "domains", "title"):
            if dp.get(field):
                cp[field] = dp[field]
    for field in ("generated", "source", "intelligence_window"):
        if delta.get(field):
            merged[field] = delta[field]
    return merged, errors, reference_warnings(delta, current)


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def compare_citation(local: dict, pubmed: dict) -> list[str]:
    """Diff one local sources: entry against its PubMed record. Pure function
    (unit-testable). Returns human-readable mismatch strings; empty = clean."""
    issues = []
    lt, pt = _norm_title(local.get("title", "")), _norm_title(pubmed.get("title", ""))
    if lt and pt:
        l_tokens, p_tokens = set(lt.split()), set(pt.split())
        overlap = len(l_tokens & p_tokens) / max(len(p_tokens), 1)
        if overlap < 0.6:
            issues.append(f"title mismatch (PubMed: \"{pubmed.get('title','')[:80]}\")")
    ly, py = str(local.get("year", "")), str(pubmed.get("year", ""))
    if ly and py and ly != py:
        issues.append(f"year {ly} != PubMed {py}")
    la = (local.get("authors") or "").split(",")[0].strip().split(" ")[0].lower().rstrip(".")
    pa = (pubmed.get("first_author") or "").split(" ")[0].lower()
    if la and pa and la != pa and la not in ("", "et"):
        issues.append(f"first author '{la}' != PubMed '{pa}'")
    return issues


def parse_sources(text: str) -> list[dict]:
    """Extract pmid-bearing sources: entries from markdown frontmatter."""
    fm = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not fm:
        return []
    entries = []
    for block in re.split(r"(?=^\s*- authors:)", fm.group(1), flags=re.M)[1:]:
        e = {}
        for field in ("authors", "title", "pmid"):
            m = re.search(rf'^\s*{field}:\s*"?([^"\n]*)"?\s*$', block, re.M)
            if m:
                e[field] = m.group(1).strip()
        m = re.search(r"^\s*year:\s*(\d{4})", block, re.M)
        if m:
            e["year"] = m.group(1)
        if e.get("pmid"):
            entries.append(e)
    return entries


def verify_sources(name: str, data: bytes) -> list[str]:
    """Citation fidelity check (contract §4.9: 'bibliographic fields pass through
    exactly'; the 10 Jul 2026 cycle shipped a composed title + truncated author
    lists, so the translator's self-check demonstrably needs a machine backstop).
    Batch-resolves the artefact's PMIDs against PubMed esummary and warn-flags
    mismatches. Warn-only and failure-tolerant: an API outage never blocks sync."""
    try:
        entries = parse_sources(data.decode("utf-8"))
    except UnicodeDecodeError:
        return []
    if not entries:
        return []
    ids = ",".join(e["pmid"] for e in entries)
    try:
        import urllib.request
        url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
               f"?db=pubmed&retmode=json&id={ids}")
        with urllib.request.urlopen(url, timeout=20) as r:
            result = json.loads(r.read()).get("result", {})
    except Exception as e:  # noqa: BLE001 — any network/API failure: skip, loudly
        print(f"  citation check skipped for {name} (PubMed unreachable: {e})", file=sys.stderr)
        return []
    warnings = []
    for e in entries:
        d = result.get(e["pmid"])
        if not d or d.get("error"):
            warnings.append(f"{name}: PMID {e['pmid']} NOT FOUND on PubMed — possible fabricated identifier")
            continue
        pubmed = {
            "title": (d.get("title") or "").rstrip("."),
            "year": (d.get("pubdate") or "")[:4],
            "first_author": (d.get("sortfirstauthor") or (d.get("authors") or [{}])[0].get("name", "")),
        }
        for issue in compare_citation(e, pubmed):
            warnings.append(f"{name}: PMID {e['pmid']} {issue}")
    return warnings


def resolve_dest(name: str) -> Path | None:
    """Return the destination path for a given Drive filename, or None to skip."""
    if name == "patterns.json":
        return Path("data/patterns.json")
    for prefix, directory in ROUTING.items():
        if name.startswith(prefix):
            slug = name[len(prefix):]
            # Drive filenames may contain path separators; never let a slug
            # escape its routing directory.
            if "/" in slug or "\\" in slug or ".." in slug:
                print(f"  refusing unsafe filename: {name}", file=sys.stderr)
                return None
            return directory / slug
    return None


def main():
    key_json = os.environ.get("GDRIVE_SERVICE_ACCOUNT_KEY")
    folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not key_json or not folder_id:
        print("ERROR: GDRIVE_SERVICE_ACCOUNT_KEY and GDRIVE_FOLDER_ID must be set.", file=sys.stderr)
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_info(
        json.loads(key_json),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    files = []
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, modifiedTime)",
                orderBy="modifiedTime desc",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    if not files:
        print("No files found in Drive output folder — nothing to sync.")
        return

    def download(file_id: str) -> bytes:
        request = service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()

    synced = 0
    skipped = 0
    fm_warnings: list[str] = []
    guard_errors: list[str] = []
    seen_names: set[str] = set()
    delta_files: list[tuple[str, str]] = []  # (name, drive id) — processed after the loop
    for f in files:
        name = f["name"]
        if f["id"] in DENYLIST_IDS:
            print(f"  skipping {name} (denylisted stale original — CLAUDE.md action 2a)")
            skipped += 1
            continue
        # The listing is modifiedTime desc; without this guard an OLDER same-named
        # file is written after (and silently overwrites) the newest one. Newest wins.
        if name in seen_names:
            print(f"  skipping older duplicate of {name} (newest copy already synced)")
            skipped += 1
            continue
        if PATTERNS_DELTA_RE.match(name):
            seen_names.add(name)
            delta_files.append((name, f["id"]))
            continue
        if name == "patterns.json":
            seen_names.add(name)
            data = download(f["id"])
            errors, warnings = validate_patterns_full(data, PATTERNS_PATH)
            fm_warnings.extend(warnings)
            if errors:
                guard_errors.extend(errors)
                print(f"  HOLDING {name} — monotonic guard failure (register protected, file NOT written)")
                skipped += 1
                continue
            PATTERNS_PATH.parent.mkdir(parents=True, exist_ok=True)
            print(f"  syncing {name} → {PATTERNS_PATH} (guards passed)")
            PATTERNS_PATH.write_bytes(data)
            synced += 1
            continue
        dest = resolve_dest(name)
        if dest is None:
            print(f"  skipping {name} (no routing rule)")
            skipped += 1
            continue
        seen_names.add(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  syncing {name} → {dest}")
        data = download(f["id"])
        dest.write_bytes(data)
        fm_warnings.extend(check_frontmatter(name, data))
        fm_warnings.extend(verify_sources(name, data))
        synced += 1

    # Deltas merge in month order (filename-sorted ascending) so a later month's
    # status update wins. The merge is idempotent — re-processing old deltas that
    # remain in Drive is a no-op.
    for name, file_id in sorted(delta_files):
        try:
            delta = json.loads(download(file_id).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            guard_errors.append(f"{name}: not valid JSON ({e}) — delta SKIPPED")
            skipped += 1
            continue
        current = {"patterns": []}
        if PATTERNS_PATH.exists():
            current = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
        merged, errors, warnings = merge_patterns_delta(current, delta)
        guard_errors.extend(f"{name}: {e}" for e in errors)
        fm_warnings.extend(warnings)
        if merged != current:
            PATTERNS_PATH.parent.mkdir(parents=True, exist_ok=True)
            print(f"  merging {name} → {PATTERNS_PATH} (append-only)")
            PATTERNS_PATH.write_text(
                json.dumps(merged, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            synced += 1
        else:
            print(f"  {name}: already merged (no-op)")
            skipped += 1

    print(f"Sync complete: {synced} file(s) routed to Hugo content tree; {skipped} skipped.")

    # Expose the guard verdict to the workflow so a register-protection event
    # turns the run RED (GitHub only emails on failure; ::error:: alone leaves
    # the run green and silent — the 19-Jun lesson).
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as fh:
            fh.write(f"guard_failures={len(guard_errors)}\n")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if guard_errors:
        print(f"\n::error::PATTERN REGISTER GUARDS ({len(guard_errors)}) — data/patterns.json protected:")
        for e in guard_errors:
            print(f"::error::  {e}")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write("## 🛑 Pattern register guard failures\n\n")
                fh.writelines(f"- `{e}`\n" for e in guard_errors)
                fh.write(
                    "\nThe longitudinal register is append-only; the incoming file would have "
                    "lost or rewritten existing record and was HELD. Fix the file in "
                    "TVF-PUBLIC-OUTPUT. If the change is genuinely intended (e.g. an editorial "
                    "retraction), apply it by hand in a PR with the reasoning in the commit.\n"
                )

    if fm_warnings:
        print(f"\n::warning::FRONTMATTER WARNINGS ({len(fm_warnings)}) — translator output deviates from charter §6:")
        for w in fm_warnings:
            print(f"::warning::  {w}")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write("## ⚠️ Drive sync frontmatter warnings\n\n")
                fh.writelines(f"- `{w}`\n" for w in fm_warnings)
                fh.write("\nFix the file in TVF-PUBLIC-OUTPUT (the Drive original) — repo edits are overwritten by this sync.\n")


if __name__ == "__main__":
    main()
