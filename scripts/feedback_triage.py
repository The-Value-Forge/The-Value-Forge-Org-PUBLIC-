#!/usr/bin/env python3
"""feedback_triage.py — stage Google Form feedback responses for triage.

Reads raw feedback responses (CSV export of the Form-responses Sheet, or — when wired —
the Sheet directly via the Drive API) and writes a GITIGNORED staging file of candidate
ledger entries for Claude/the editor to anonymise and curate.

It deliberately does NOT touch data/feedback.json. The public ledger is curated by hand
(anonymised, themed) from the staging file — never auto-populated. See
docs/design-system/FEEDBACK-PROCESS-MAP-v1.md.

Privacy: the form asks for no email at all (dropped 28 Jul 2026). Any email COLUMN is still
detected and dropped in case one is ever re-added, and — the case that now matters — any
address typed into the free-text answer is REDACTED before staging. It stays in the Sheet
only. Only anonymised, themed entries — written by hand into data/feedback.json —
ever reach the site.

Usage:
    python scripts/feedback_triage.py --csv responses.csv
    python scripts/feedback_triage.py --csv responses.csv --out data/_feedback_staging.json

Drive direct-read (FEEDBACK_SHEET_ID env) is stubbed below for when the connector is wired.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import sys

STAGING_DEFAULT = "data/_feedback_staging.json"
LEDGER_PATH = "data/feedback.json"  # guard target — this script must never write it

# header keyword -> candidate field.
#
# KEYWORDS ARE ORDERED MOST-SPECIFIC-FIRST, and map_columns tries them in that
# order. This is load-bearing, not tidiness.
#
# On 28 Jul 2026 the editor retitled question 1 to "Category of Feedback". That
# header contains the word "feedback" — which was `raw`'s first keyword — so the
# category column captured the `raw` slot and the ACTUAL free-text answer was
# dropped. Every submission would have staged the dropdown word ("A suggestion")
# as the feedback text and silently lost what the person wrote. Nothing would
# have errored; the staging file would just have been quietly worthless.
#
# Two changes stop it, deliberately belt-and-braces:
#   1. "category" is a `type` keyword, and `type` is resolved before `raw`, so
#      that column is claimed by the right field first.
#   2. `raw` now tries "tell us" and "your feedback" BEFORE the bare "feedback",
#      so even with no type match it still finds the real answer column.
# Either alone fixes today's form. Both together fix the class: a question that
# merely MENTIONS feedback can no longer outrank the one that asks for it.
FIELD_KEYWORDS = {
    "type": ["type of feedback", "category", "type"],
    "page": ["page", "domain", "where"],
    "raw": ["tell us", "your feedback", "comment", "message", "feedback"],
    "severity": ["severity", "how serious", "priority"],
    "role": ["role", "you are", "describe yourself"],
}
EMAIL_KEYWORDS = ["email", "e-mail", "contact"]
TIMESTAMP_KEYWORDS = ["timestamp", "time", "date"]

# Addresses typed INTO the free-text answer, which is the only route left.
#
# The form lost its email question on 28 Jul 2026 — the editor does not reply
# individually, so an address is data collected for a purpose that never
# happens. That removed the column this script was built to drop, and quietly
# moved the risk: the one place an address can now appear is the free-text
# answer, and that field IS staged. The column guard would sail straight past
# it.
#
# It is not hypothetical. /legal/ now instructs anyone making a data-protection
# request to put their subscribed address in that box, because the mailing list
# is keyed on it and a request we cannot match is one we cannot action. So the
# staging file would otherwise accumulate exactly the addresses of the people
# who asked to be forgotten.
#
# Hence redaction at the point of staging. The address stays in the Sheet, where
# the request is actioned from; it never reaches the file we work out of.
EMAIL_IN_TEXT = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]*[a-zA-Z]\b")


def redact_emails(text: str) -> tuple[str, int]:
    """Replace any email-shaped substring with a marker. Returns (text, count).

    Deliberately a little greedy: over-redacting a string that merely looks like
    an address costs a triage note some legibility, while under-redacting puts
    personal data in a file this publication promised would not hold any.
    """
    n = len(EMAIL_IN_TEXT.findall(text))
    return (EMAIL_IN_TEXT.sub("[email redacted]", text), n) if n else (text, 0)


def _match(header: str, keywords: list[str]) -> bool:
    h = header.strip().lower()
    return any(k in h for k in keywords)


def map_columns(headers: list[str]) -> dict[str, str]:
    """Return {candidate_field: header}. Email/timestamp handled separately.

    Loops KEYWORDS on the outside and headers on the inside — the opposite of
    the original, and the point of the fix. Header-first meant the earliest
    COLUMN matching any keyword won, so a vague header beat a precise one purely
    by sitting to its left. Keyword-first means the most specific phrasing wins
    regardless of column order, which is what "Category of Feedback" sitting
    before the real answer column needed.
    """
    mapping: dict[str, str] = {}
    for field, kws in FIELD_KEYWORDS.items():
        for kw in kws:                      # specificity order — see FIELD_KEYWORDS
            for h in headers:
                if kw in h.strip().lower() and h not in mapping.values():
                    mapping[field] = h
                    break
            if field in mapping:
                break
    return mapping


def find_special(headers: list[str], keywords: list[str]) -> str | None:
    for h in headers:
        if _match(h, keywords):
            return h
    return None


def load_csv(path: str) -> tuple[list[dict], int, dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return parse_rows(list(csv.DictReader(fh)))


def parse_rows(rows: list[dict]) -> tuple[list[dict], int, dict[str, str]]:
    """Shared parser for both intake paths (CSV export and direct Sheet read),
    so the two can never drift in how they anonymise or map columns."""
    if not rows:
        return [], 0, {}
    headers = list(rows[0].keys())
    colmap = map_columns(headers)
    if "raw" not in colmap:
        sys.exit(
            "ERROR: could not find a feedback/comment column. Headers seen: "
            + ", ".join(headers)
        )
    email_col = find_special(headers, EMAIL_KEYWORDS)
    ts_col = find_special(headers, TIMESTAMP_KEYWORDS)

    candidates: list[dict] = []
    left_email = 0
    for row in rows:
        raw = (row.get(colmap["raw"]) or "").strip()
        if not raw:
            continue  # skip blank submissions
        if email_col and (row.get(email_col) or "").strip():
            left_email += 1  # counted, never stored
        raw, redacted = redact_emails(raw)
        left_email += redacted  # an address in the free text counts the same way
        candidates.append(
            {
                "received": (row.get(ts_col) or "").strip() if ts_col else "",
                "type": (row.get(colmap.get("type", "")) or "").strip(),
                "page": (row.get(colmap.get("page", "")) or "").strip(),
                "severity": (row.get(colmap.get("severity", "")) or "").strip(),
                "role": (row.get(colmap.get("role", "")) or "").strip(),
                "raw": raw,
                # triage fields — filled by hand during anonymise/curate:
                "status": "Received",
                "theme": "",
                "response": "",
                "domains": [],
                "link": "",
            }
        )
    return candidates, left_email, colmap


def load_sheet(sheet_id: str) -> tuple[list[dict], int, dict[str, str]]:
    """Read the Form-responses Sheet directly, via the same service account
    drive_sync.py already uses (GDRIVE_SERVICE_ACCOUNT_KEY).

    Note the API difference from drive_sync.py: that script pulls plain files
    with files().get_media(). A Google Sheet is not a plain file — get_media
    returns a 403 for Google-native types — so this exports it as CSV with
    files().export_media() and feeds the result through the same parser the
    --csv path uses.

    The service account needs read access to the Sheet: share the responses
    Sheet with the service account's client_email (Viewer is enough). The
    Sheet ID is NOT committed — it lives in FEEDBACK_SHEET_ID, the same
    pattern as GDRIVE_FOLDER_ID.
    """
    if not sheet_id:
        sys.exit(
            "ERROR: FEEDBACK_SHEET_ID is not set. Provide the Form-responses Sheet ID, "
            "or use --csv with an exported file."
        )
    key_json = os.environ.get("GDRIVE_SERVICE_ACCOUNT_KEY")
    if not key_json:
        sys.exit(
            "ERROR: GDRIVE_SERVICE_ACCOUNT_KEY is not set (same secret drive_sync.py uses)."
        )

    # Imported here, not at module top: the --csv path must keep working on a
    # machine with no Google client libraries installed.
    import io

    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        json.loads(key_json),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    data = service.files().export_media(fileId=sheet_id, mimeType="text/csv").execute()
    text = data.decode("utf-8-sig") if isinstance(data, bytes) else str(data)
    return parse_rows(list(csv.DictReader(io.StringIO(text))))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="Path to the Form-responses CSV export")
    src.add_argument(
        "--sheet",
        action="store_true",
        help="Read the Sheet directly via FEEDBACK_SHEET_ID env (not yet wired)",
    )
    ap.add_argument("--out", default=STAGING_DEFAULT, help=f"Staging output (default {STAGING_DEFAULT})")
    args = ap.parse_args()

    # Hard guard: never write the public ledger.
    if os.path.abspath(args.out) == os.path.abspath(LEDGER_PATH):
        sys.exit(f"REFUSING to write the public ledger ({LEDGER_PATH}). Staging only.")

    if args.sheet:
        candidates, left_email, colmap = load_sheet(os.environ.get("FEEDBACK_SHEET_ID", ""))
    else:
        candidates, left_email, colmap = load_csv(args.csv)

    payload = {
        "generated": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "source": args.csv or "sheet:FEEDBACK_SHEET_ID",
        "column_map": colmap,
        "count": len(candidates),
        "left_email_count": left_email,  # how many wished follow-up (emails NOT stored here)
        "candidates": candidates,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"Staged {len(candidates)} candidate(s) → {args.out}")
    print(f"  {left_email} respondent(s) left an email for follow-up (kept in the Sheet, not staged).")
    print("Next: anonymise + theme each candidate, then hand-write curated entries into data/feedback.json.")


if __name__ == "__main__":
    main()
