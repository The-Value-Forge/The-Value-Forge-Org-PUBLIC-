"""drive_sync.py — downloads translated content from TVF-PUBLIC-OUTPUT Drive folder
into the Hugo content tree.

File routing (translator must follow this naming convention):
  signal--YYYY-MM-DD-slug.md     → content/signal/YYYY-MM-DD-slug.md
  synthesis--YYYY-MM-DD-slug.md  → content/synthesis/YYYY-MM-DD-slug.md
  monthly--YYYY-MM-slug.md       → content/monthly/YYYY-MM-slug.md
  patterns.json                  → IGNORED (legacy; the register is delta-driven)
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
  deltas apply in month order. Full-file replacement FROM DRIVE is disabled
  (10 Aug 2026): once a delta advances the register, any full file left in the
  folder can only regress it, and four legacy copies turned the daily sync red
  every morning. The monotonic guards below are unchanged and still apply to a
  deliberate, hand-reviewed full replacement made in a PR.

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
    # No `monthly--` entry on purpose: this check asserts list-shaped taxonomy
    # fields, and the flagship's required fields (`month:`, `featured:`) are
    # correctly scalars — adding it here fires on every Monthly forever. The
    # flagship's real exposure is citation reachability, which
    # check_citation_integrity covers directly.
}

# NOTE — the four-ID denylist that stood here is GONE, deliberately, 7 Sep 2026.
# It named the uncorrected 19 Jun 2026 originals so they could never overwrite
# the corrected 3 Jul same-name copies. All four were trashed in Drive on
# 7 Sep 2026 and the folder now returns exactly the four corrected copies for
# `2026-06-19`, so the list could only go stale from here.
#
# The general guard is the newest-wins dedupe in the sync loop below, which is
# what would have covered this case anyway; the IDs were belt-and-braces for a
# window that has closed. Do not reintroduce a per-file ID list — fix the Drive
# folder, or fix the dedupe rule.


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


# Aggregate artefacts (synthesis, monthly) don't discover citations of their
# own — they inherit them from the signals they synthesise. So an empty
# `sources:` is not a shape error the way a missing `domain:` is; it is
# indistinguishable from a correct one unless you read the body. That is
# precisely how the 7 Aug 2026 synthesis AND the August flagship both reached
# production with `sources: []` and every evidence claim in them unreachable,
# on a green run, while the eight syntheses before them carried 12–22 sources
# each. Cause: the translator's own SYNTHESIS and MONTHLY frontmatter templates
# used `sources: []` as their literal worked example, while the SIGNAL template
# showed a populated entry — so signals kept their references and only the
# aggregates lost them (fixed in translator v3.8).
#
# The rule encoded here is the routine's own (§4.9 + the Monthly
# cross-reference discipline): every restated finding is either cited in
# `sources:` or cross-referenced to the site artefact that carries the
# citation. An aggregate with NEITHER has no reachable evidence at all, which
# breaks the static-copy rule outright. That fails the run RED rather than
# adding a fourth line to a warnings block nobody reads — the 19-Jun lesson
# was that GitHub only emails on failure.
CROSSREF_RE = re.compile(r"\]\(/(?:signal|synthesis|monthly)/")


def check_citation_integrity(name: str, data: bytes) -> list[str]:
    """Error when any artefact carries no reachable evidence at all.

    Covers every routed artefact type, not just the two that failed in August.
    A Signal is one study and has no cross-reference escape — its `sources:`
    must be populated outright. An aggregate may satisfy reachability either
    way. Signals were undamaged in August only because their template happened
    to show a populated entry; that is luck, not protection.
    """
    if not name.startswith(("signal--", "synthesis--", "monthly--")):
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []  # check_frontmatter already reports undecodable content
    fm = re.match(r"^---\s*\n(.*?)\n---(.*)$", text, re.S)
    if not fm:
        return []  # check_frontmatter already reports a missing block
    front, body = fm.group(1), fm.group(2)
    # `sources:` is populated either inline (`sources: [ ... ]`) or, far more
    # commonly, as a YAML block list whose own line is empty and whose entries
    # are the indented lines that follow — so both shapes must count as present.
    m = re.search(r"^sources:[ \t]*(.*)$((?:\n[ \t]+.*)*)", front, re.M)
    if m and (m.group(1).strip() not in ("", "[]") or "- " in m.group(2)):
        return []
    if name.startswith("signal--"):
        return [
            f"{name}: `sources:` is empty — a Signal reports one study and MUST "
            "carry its citation (charter §4.9). Fix the Drive original: a "
            "repo-side fix is reverted by the next sync."
        ]
    if CROSSREF_RE.search(body):
        return []  # claims reachable via the site's own artefacts instead
    return [
        f"{name}: `sources:` is empty AND the body carries no /signal/ or "
        "/synthesis/ cross-reference — every evidence claim in this artefact is "
        "unreachable to the reader (charter §4.9). Fix the Drive original: a "
        "repo-side fix is reverted by the next sync."
    ]


def check_sources_reachable(name: str, data: bytes) -> list[str]:
    """Error on any single source entry a reader cannot actually follow.

    `check_citation_integrity` above asks whether an artefact has ANY reachable
    evidence, which is the August failure it was written for. It cannot see a
    populated `sources:` list in which one entry carries no pmid, no doi and no
    url — and measured 13 September 2026 across all 124 published artefacts,
    SIX entries are in exactly that state: a Written Ministerial Statement, a
    letter to a named peer, two NHS England best-practice guides, a workforce
    survey and a services listing. Each is named, none is followable.

    That matters more for policy sources than for papers, not less. A journal
    article can be found from its title; "Healthcare Services (Acute, Primary
    and Community)" cannot, and a reader who cannot reach the source cannot
    check the claim — which is the whole contract this publication runs on.
    Needs no network, so unlike verify_sources it is a hard check rather than a
    best-effort one.
    """
    if not name.startswith(("signal--", "synthesis--", "monthly--")):
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    fm = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not fm:
        return []
    block = re.split(r"^sources:\s*$", fm.group(1), flags=re.M)
    if len(block) < 2:
        return []
    out, cur, n = [], None, 0

    def _flush(entry, idx):
        if entry is None:
            return
        if any(entry.get(k, "").strip() for k in ("pmid", "doi", "url")):
            return
        out.append(f"{name}: source {idx} carries no pmid, no doi and no url — "
                   f"unreachable to the reader: "
                   f"{entry.get('title') or entry.get('citation') or '?'!r:.70}. "
                   "Add a url. Fix the Drive original: a repo-side fix is "
                   "reverted by the next sync.")

    for line in block[1].splitlines():
        # STOP at the next top-level key. Without this the reader runs straight
        # out of `sources:` and into `tags:`, whose `  - frailty` items match
        # the list-item pattern and become sources with no identifiers at all —
        # so a clean artefact reported four unreachable entries that do not
        # exist. Found 13 September 2026 by reading the file the count pointed
        # at, which is the only reason it was caught.
        if line.strip() and not line[:1].isspace():
            break
        if re.match(r"^\s*-\s", line):
            _flush(cur, n)
            cur, n = {}, n + 1
            line = re.sub(r"^\s*-\s", "  ", line)
        if cur is None:
            continue
        m = re.match(r'\s*(\w+):\s*"?(.*?)"?\s*$', line)
        if m:
            cur[m.group(1)] = m.group(2)
    _flush(cur, n)
    return out


# A routine's Drive upload can silently land a tiny placeholder instead of the
# artefact — a parameter error at the connector call. Three observed instances
# by 7 Sep 2026: the August edition, evidence-watch Issue 19, and the 6 Sep
# flagship, where a 24-byte stub took the place of MONTHLY-REVIEW-2026-09.md.
#
# Each was caught in-run by the routine that made it, which is the create-only
# discipline working. This guard exists because that catch is not structural:
# a 24-byte file is a VALID file. It parses, it routes, and — carrying no
# frontmatter and no claims — it has nothing for check_frontmatter or
# check_citation_integrity to fail on. A routine that is interrupted, runs out
# of turn, or simply does not re-read its own write leaves a well-named,
# complete-looking stub where the flagship should be.
#
# The floor is set from the artefacts that actually exist rather than guessed:
# the smallest published signal is 1,384 bytes, the smallest synthesis 4,833,
# the smallest monthly 31,128. 1KB therefore sits below every genuine artefact
# and 42x above the observed stub. It is deliberately NOT scaled per type —
# the depth rule now lets a thin month produce a short monthly, and a floor
# that fails a legitimately brief artefact would be worse than the stub.
MIN_ARTEFACT_BYTES = 1024


def check_artefact_size(name: str, data: bytes) -> tuple[list[str], list[str]]:
    """Return (warnings, errors) for an implausibly small routed artefact.

    A monthly is the landing hero and the publication's most-read page, so a
    stub there fails the run RED — same reasoning as check_citation_integrity,
    that GitHub only emails on failure and a warnings block goes unread. A
    signal or synthesis warns: losing a week to a hard failure is worse than
    publishing one flagged file, which is the trade the sync already makes.
    """
    if not name.startswith(("signal--", "synthesis--", "monthly--")):
        return [], []
    if len(data) >= MIN_ARTEFACT_BYTES:
        return [], []
    msg = (
        f"{name}: {len(data)} bytes — below the {MIN_ARTEFACT_BYTES}-byte floor, "
        "so this is almost certainly a failed upload rather than a short "
        "artefact (smallest real one to date: 1,384 bytes). Fix the Drive "
        "original: a repo-side fix is reverted by the next sync."
    )
    return ([], [msg]) if name.startswith("monthly--") else ([msg], [])


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


# Words too common in journal names to carry any identifying weight. Without
# stripping these, "European Journal of X" and "American Journal of Y" share
# half their tokens and any threshold becomes meaningless.
_JOURNAL_STOP = {"the", "of", "and", "a", "an", "for", "in", "on", "journal",
                 "international", "european", "american", "british", "annals",
                 "archives", "review", "reviews", "research", "open", "science"}


def _sig_words(s: str) -> set:
    return {w for w in _norm_title(s).split() if w not in _JOURNAL_STOP}


def _title_recall(cited: str, actual: str) -> tuple[float, float]:
    """Delegate to verify_citations, which owns the measurement and its tests.

    Imported lazily and by path: drive_sync runs inside the GitHub Action where
    scripts/ is not necessarily on sys.path, and a failure to import must never
    take the sync down over a warn-only check.
    """
    try:
        import importlib.util
        import pathlib
        spec = importlib.util.spec_from_file_location(
            "_vcit", pathlib.Path(__file__).resolve().parent / "verify_citations.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.title_recall(cited, actual)
    except Exception:
        return 1.0, 1.0   # unverified, never a false alarm


def compare_citation(local: dict, pubmed: dict) -> list[str]:
    """Diff one local sources: entry against its PubMed record. Pure function
    (unit-testable). Returns human-readable mismatch strings; empty = clean."""
    issues = []
    # TITLE, measured against the record's MAIN CLAUSE with acronyms expanded.
    #
    # This check has always divided the overlap by the RECORD's tokens, which is
    # the right direction -- it asks whether the citation reproduces the paper's
    # title, not merely whether it overlaps it. But measured across the whole
    # published corpus on 13 September 2026 it flagged five citations of which
    # TWO were innocent, and missed a sixth that was not:
    #
    #   false positive  "Telehome-Based Palliative Care in Nursing Practice: An
    #                   Integrative Review" -- the real subtitle continues "of
    #                   Care Delivery, Caregiver Involvement and Service
    #                   Coordination". The main clause is reproduced exactly.
    #   false positive  "...anxiety and HRQoL in rheumatoid arthritis" for
    #                   "...anxiety, and health-related quality of life in
    #                   adults with rheumatoid arthritis". An acronym.
    #   false NEGATIVE  "Clinical Frailty Scale and outcomes in elderly heart
    #                   failure" for "...for risk stratification in elderly
    #                   patients with heart failure" -- the study's stated
    #                   purpose swapped for a vaguer one, propped above the
    #                   threshold by the shared ": a meta-analysis" tail.
    #
    # A 40% false-positive rate is how a checker stops being read, and the
    # September lesson is that a checker crying wolf is worse than none. So the
    # comparison is now against the main clause only (journals hang the design
    # on a subtitle and dropping it is legitimate practice, dropping the subject
    # is not), acronyms are expanded from the record itself rather than a
    # hand-kept table, and a low score is exonerated by character-level
    # similarity -- because PubMed records sometimes arrive with capitals or
    # italicised genus names stripped, and there the CITATION is right and the
    # record is corrupt. Shared with verify_citations.py so the sync guard and
    # the audit script cannot drift apart; that they had drifted is how each
    # missed what the other caught.
    if local.get("title") and pubmed.get("title"):
        recall, char = _title_recall(local["title"], pubmed["title"])
        if recall < 0.75 and char < 0.80:
            issues.append(f"title mismatch — reproduces only {recall:.0%} of the "
                          f"record's main clause (PubMed: "
                          f"\"{pubmed.get('title','')[:80]}\")")
    ly, py = str(local.get("year", "")), str(pubmed.get("year", ""))
    if ly and py and ly != py:
        issues.append(f"year {ly} != PubMed {py}")
    la = (local.get("authors") or "").split(",")[0].strip().split(" ")[0].lower().rstrip(".")
    pa = (pubmed.get("first_author") or "").split(" ")[0].lower()
    if la and pa and la != pa and la not in ("", "et"):
        issues.append(f"first author '{la}' != PubMed '{pa}'")
    # JOURNAL, added 13 September 2026 — the hole in this guard.
    #
    # This function has checked title, year and first author since 10 July, when
    # a cycle shipped a composed title. It has never looked at `container:`, and
    # `parse_sources` did not even extract it. Measured that day across all 124
    # published artefacts: SIX citations name the wrong journal — among them
    # Sensors (Basel) published as "International Journal of COPD", European
    # Urology Open Science as "BMJ Supportive & Palliative Care", and Annals of
    # Medicine as "Journal of Antimicrobial Chemotherapy". Every one has the
    # right PMID, the right DOI and the right first author, so title/year/author
    # checking passed them all and would pass an identical artefact today.
    #
    # A wrong journal is not cosmetic. It is the field a reader uses to judge
    # weight before opening anything, and a general-medicine journal presented
    # as the field's flagship silently inflates the evidence.
    #
    # Matched on significant-word overlap against both the full title and the
    # ISO abbreviation, because journals are cited in human form and PubMed
    # stores several variants — the question is whether it is recognisably the
    # same publication, not whether it is byte-equal.
    lc = local.get("container") or ""
    if lc:
        cand = [pubmed.get("journal", ""), pubmed.get("journal_abbrev", "")]
        lw = _sig_words(lc)
        if lw and any(_sig_words(c) for c in cand):
            if not any(_sig_words(c) and len(lw & _sig_words(c)) / len(lw) >= 0.5
                       for c in cand):
                issues.append(f"journal '{lc}' != PubMed "
                              f"'{pubmed.get('journal', '')}'")
    return issues


def parse_sources(text: str) -> list[dict]:
    """Extract pmid-bearing sources: entries from markdown frontmatter."""
    fm = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not fm:
        return []
    entries = []
    for block in re.split(r"(?=^\s*- authors:)", fm.group(1), flags=re.M)[1:]:
        e = {}
        for field in ("authors", "title", "pmid", "container"):
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
            "journal": d.get("fulljournalname") or "",
            "journal_abbrev": d.get("source") or "",
        }
        for issue in compare_citation(e, pubmed):
            warnings.append(f"{name}: PMID {e['pmid']} {issue}")
    return warnings


def preserve_card_image(incoming: bytes, dest: Path) -> bytes:
    """Carry a repo-side `card_image:` pin across a Drive overwrite.

    Content files are owned by this sync and rewritten wholesale from Drive.
    Drive originals never carry `card_image:`, so an editorially-pinned card
    image was silently destroyed on the next run. A pin is a deliberate
    editorial act (priority 1 in layouts/partials/card-art.html), so it
    survives the overwrite.

    This is NOT how routine art assignment works — that lives in
    data/card_art.json and is resolved at render time (art_sync.py). Nothing
    writes card_image: into content automatically any more; two jobs owning
    one field is what produced the 12/19/26 July strip-restore oscillation and
    a phantom production build after every real sync.

    Idempotent by construction: re-running against an unchanged pair returns
    byte-identical output, so it can never itself become a source of churn.
    """
    if not dest.exists():
        return incoming
    try:
        current = dest.read_text(encoding="utf-8")
        text = incoming.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return incoming  # binary or unreadable: never guess

    cur_fm = re.match(r"^---\s*\n(.*?)\n---", current, re.S)
    inc_fm = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not cur_fm or not inc_fm:
        return incoming
    pin = re.search(r"^card_image:.*$", cur_fm.group(1), re.M)
    if not pin:
        return incoming
    if re.search(r"^card_image:", inc_fm.group(1), re.M):
        return incoming  # incoming states its own value: Drive wins

    # Re-insert immediately before the closing delimiter of the incoming block.
    insert_at = inc_fm.end(1) + 1  # start of the closing "---" line
    return (text[:insert_at] + pin.group(0) + "\n" + text[insert_at:]).encode("utf-8")


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
    # Citation-integrity failures still sync the file — losing a week of content
    # is worse than publishing it flagged — but they turn the run red so the
    # failure arrives by email instead of dying in a step summary.
    #
    # SEVERITY DEPENDS ON WHETHER THIS RUN TOUCHED THE ARTEFACT (14 Sep 2026).
    # `check_sources_reachable` shipped on 13 September and its first execution
    # in production — the next morning — turned the sync RED on seven entries in
    # five artefacts published in MAY AND JUNE. The check is right and the
    # entries are real; the SEVERITY was wrong, and wrong in the one way this
    # pipeline cannot afford. A sync that is red every morning on a backlog
    # nobody can clear from the sync trains everyone to ignore a red sync, and
    # the red sync is the only alarm the pipeline has: it is how the 7 Aug
    # referencing loss would have been caught, and it is what the nine-day
    # content-freshness heartbeat rides on. CLAUDE.md already records this exact
    # reasoning about the hold-path 403 — "a red sync that needs a human on
    # every hold will train people to ignore red syncs" — and then the next
    # check shipped did it anyway.
    #
    # So the rule is accountability, not tolerance: THIS RUN IS ANSWERABLE FOR
    # WHAT IT PUBLISHES, NOT FOR WHAT WAS PUBLISHED BEFORE IT. An artefact this
    # run created or changed must be clean (hard error, red). An artefact it
    # rewrote byte-identically is a pre-existing backlog item: still counted,
    # still named in full every single run, never hidden — but it does not
    # redden a run that introduced nothing.
    #
    # This is deliberately NOT an allowlist. The repo has already been bitten by
    # one: CANONICAL_DOMAINS carried three legacy spellings so a check would not
    # fire on the archive, and the tolerance outlived its cases, which meant a
    # NEW artefact could ship any of them and pass. There is nothing here to
    # maintain and nothing to go stale — the moment anything touches a
    # defective artefact, every defect in it becomes blocking again.
    integrity_errors: list[str] = []
    integrity_backlog: list[str] = []
    seen_names: set[str] = set()
    delta_files: list[tuple[str, str]] = []  # (name, drive id) — processed after the loop
    for f in files:
        name = f["name"]
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
            # A full patterns.json from Drive is IGNORED, by design (10 Aug 2026).
            #
            # Since translator v3.5 the register is delta-driven: the translator
            # emits patterns-delta-YYYY-MM.json and never a whole file. So any
            # full patterns.json appearing here is, by definition, a legacy
            # artefact frozen at some past date — and once a delta has advanced
            # the register past it, it can only ever REGRESS it. Four such files
            # sat in the folder and turned the 08:10 sync red every morning with
            # four guard failures each time.
            #
            # Denylisting their IDs was the first fix and it was the wrong shape:
            # it treats a class of problem as four instances, so the next stray
            # file starts the cycle again. Ignoring the filename outright means
            # nothing that lands in that folder can regress the register, with no
            # ID list to maintain.
            #
            # The monotonic guards are NOT relaxed — validate_patterns_full and
            # its tests stay exactly as they were. A genuine full restore is a
            # deliberate act: do it by hand in a PR, where a human reviews the
            # diff. It is not something a file dropped in a shared folder should
            # be able to trigger.
            seen_names.add(name)
            print(f"  ignoring {name} — the register is delta-driven "
                  "(patterns-delta-YYYY-MM.json); full-file replacement from "
                  "Drive is disabled by design")
            skipped += 1
            continue
        dest = resolve_dest(name)
        if dest is None:
            print(f"  skipping {name} (no routing rule)")
            skipped += 1
            continue
        seen_names.add(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  syncing {name} → {dest}")
        before = dest.read_bytes() if dest.exists() else None
        data = download(f["id"])
        written = preserve_card_image(data, dest)
        dest.write_bytes(written)
        # `touched` is measured on the bytes that actually land in the tree, not
        # on the bytes Drive returned — preserve_card_image rewrites one field,
        # so comparing the download would call every artefact changed forever.
        touched = before is None or written != before
        fm_warnings.extend(check_frontmatter(name, data))
        fm_warnings.extend(verify_sources(name, data))
        citation_errors = check_citation_integrity(name, data)
        citation_errors += check_sources_reachable(name, data)
        (integrity_errors if touched else integrity_backlog).extend(citation_errors)
        size_warnings, size_errors = check_artefact_size(name, data)
        fm_warnings.extend(size_warnings)
        # A SIZE ERROR IS ALWAYS HARD, TOUCHED OR NOT — and this exception is
        # the whole reason the backlog split is scoped to the citation checks.
        # The first version of the split routed size errors through it too, and
        # test_size_guard_is_wired_into_the_sync_loop caught it immediately.
        # It was right to: a stub is not an imperfection IN an artefact, it is
        # the artefact missing — a 24-byte placeholder where the September
        # flagship should be. If an unfixed stub in Drive re-synced identically
        # every morning, it would go red once and then quietly green forever,
        # which is the precise failure the size guard exists to prevent. The
        # citation backlog is a long tail of historical imperfection on pages
        # that otherwise work; a stub is the page not being there.
        integrity_errors.extend(size_errors)
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
            fh.write(f"integrity_failures={len(integrity_errors)}\n")
            fh.write(f"integrity_backlog={len(integrity_backlog)}\n")

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

    if integrity_errors:
        print(f"\n::error::CITATION INTEGRITY ({len(integrity_errors)}) — artefact published with unreachable claims:")
        for e in integrity_errors:
            print(f"::error::  {e}")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write("## 🛑 Citation integrity failures\n\n")
                fh.writelines(f"- `{e}`\n" for e in integrity_errors)
                fh.write(
                    "\nThe file WAS synced (losing the cycle's content is worse than "
                    "publishing it flagged), but every evidence claim in it is currently "
                    "unreachable to the reader, which breaks the static-copy rule. Fix the "
                    "Drive original in TVF-PUBLIC-OUTPUT — a repo-side fix is reverted by "
                    "the next sync — then re-run this workflow.\n"
                )

    # Reported in full on EVERY run, and never allowed to become a number
    # without names: a backlog you cannot read is a backlog nobody works.
    if integrity_backlog:
        print(
            f"\n::warning::CITATION INTEGRITY BACKLOG ({len(integrity_backlog)}) — "
            "pre-existing, NOT introduced by this run:"
        )
        for e in integrity_backlog:
            print(f"::warning::  {e}")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write("## 📌 Citation integrity backlog (pre-existing)\n\n")
                fh.writelines(f"- `{e}`\n" for e in integrity_backlog)
                fh.write(
                    "\nThis run rewrote each of these artefacts byte-identically, so it "
                    "introduced none of them — which is why the run is not red for them. "
                    "They are real defects in already-published artefacts and they are "
                    "listed here every run until the Drive originals are fixed. The moment "
                    "any run CHANGES one of these artefacts, every defect in it becomes a "
                    "hard failure again.\n"
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
