#!/usr/bin/env python3
"""feedback_triage.py — stage Google Form feedback responses for triage.

Reads raw feedback responses (CSV export of the Form-responses Sheet, or — when wired —
the Sheet directly via the Drive API) and writes a GITIGNORED staging file of candidate
ledger entries for Claude/the editor to anonymise and curate.

It deliberately does NOT touch data/feedback.json. The public ledger is curated by hand
(anonymised, themed) from the staging file — never auto-populated. See
docs/design-system/FEEDBACK-PROCESS-MAP-v1.md.

Privacy: any email column is detected and DROPPED from the staging output (it stays in the
Sheet only). Only anonymised, themed entries — written by hand into data/feedback.json —
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
import sys

STAGING_DEFAULT = "data/_feedback_staging.json"
LEDGER_PATH = "data/feedback.json"  # guard target — this script must never write it

# header keyword -> candidate field. First keyword that appears (case-insensitive,
# substring) in a column header wins that field.
FIELD_KEYWORDS = {
    "type": ["type"],
    "page": ["page", "domain", "where"],
    "raw": ["feedback", "comment", "message", "your feedback", "tell us"],
    "severity": ["severity", "how serious", "priority"],
    "role": ["role", "you are", "describe yourself"],
}
EMAIL_KEYWORDS = ["email", "e-mail", "contact"]
TIMESTAMP_KEYWORDS = ["timestamp", "time", "date"]


def _match(header: str, keywords: list[str]) -> bool:
    h = header.strip().lower()
    return any(k in h for k in keywords)


def map_columns(headers: list[str]) -> dict[str, str]:
    """Return {candidate_field: header}. Email/timestamp handled separately."""
    mapping: dict[str, str] = {}
    for field, kws in FIELD_KEYWORDS.items():
        for h in headers:
            if _match(h, kws) and h not in mapping.values():
                mapping[field] = h
                break
    return mapping


def find_special(headers: list[str], keywords: list[str]) -> str | None:
    for h in headers:
        if _match(h, keywords):
            return h
    return None


def load_csv(path: str) -> tuple[list[dict], int, dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
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


def load_sheet(sheet_id: str):  # pragma: no cover - stub until connector wired
    raise NotImplementedError(
        "Direct Drive/Sheets read not wired yet. Export the responses as CSV and use "
        "--csv, or implement this with the same service-account pattern as "
        "scripts/drive_sync.py reading FEEDBACK_SHEET_ID."
    )


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
