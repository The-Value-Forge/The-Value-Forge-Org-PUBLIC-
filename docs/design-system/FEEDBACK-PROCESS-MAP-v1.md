# Feedback process map — receive → triage → action → publish (v1)

_Drafted 28 June 2026 (during the June park). Operational companion to
`FEEDBACK-FEATURE-SPEC-v1.md`. Where the two differ, **this file is current** on the
intake mechanism: the editor chose a **Google Form embed** (not Netlify Forms) to avoid
spending Netlify credits — the v1 spec listed Google Form as an alternative; it is now
the decision._

## Principles (unchanged from the feature spec)

- **Close the loop in the open.** The "You said, we did" ledger is the differentiator —
  most sites collect feedback into a void.
- **Curated, never auto-published.** Raw responses are private; only anonymised, themed
  entries reach `data/feedback.json` and the public page.
- **Anonymise hard.** Publish themes + our response, never identities, raw quotes with
  identifying detail, or emails.
- **Static-copy rule applies** to any wording that ships in a ledger entry.

## The pipeline

```
 ┌──────────┐   submits    ┌───────────────┐   linked     ┌──────────────────────┐
 │  Tester  │ ───────────▶ │  Google Form  │ ───────────▶ │  Form-responses Sheet │
 └──────────┘   (embed on  │  (intake)     │  (auto)      │  (Google Drive)       │
                /feedback/) └───────────────┘              └──────────┬───────────┘
                                                                      │ read (MCP / export)
                                                                      ▼
                                                        ┌──────────────────────────┐
                                                        │  TRIAGE  (Claude + the editor)│
                                                        │  • anonymise              │
                                                        │  • dedupe → theme         │
                                                        │  • classify + set status  │
                                                        │  • decide action          │
                                                        └───────┬───────────┬───────┘
                                          actionable work?      │           │  no action / not now
                                              ┌─────────────────┘           └─────────────────┐
                                              ▼                                                ▼
                                   ┌────────────────────┐                        ┌──────────────────────┐
                                   │ priority in CLAUDE/  │                        │ ledger entry, status  │
                                   │ TODO or GitHub issue │                        │ Declined / Out of     │
                                   │  → build → ship       │                        │ scope (logged, not    │
                                   └─────────┬────────────┘                        │ silently dropped)     │
                                             │ when shipped                         └───────────┬──────────┘
                                             ▼                                                  │
                                   ┌──────────────────────────────────────────────────────────▼──────┐
                                   │  data/feedback.json  (curated ledger; entry + status + link)      │
                                   └───────────────────────────────┬──────────────────────────────────┘
                                                                   │ commit (batched) → Netlify build
                                                                   ▼
                                                        /feedback/  "You said, we did"
```

## Roles

| Stage | Owner | Surface |
|---|---|---|
| Intake | Tester | Google Form embedded on `/feedback/` |
| Raw store | Google (automatic) | Form-responses Google Sheet in Drive |
| Receive + triage | **Claude Code** (+ the editor approve) | reads the Sheet; drafts entries |
| Action (site/content work) | Claude Code | `CLAUDE.md`/`TODO.md` priority or GitHub issue |
| Publish | Claude Code | `data/feedback.json` → commit → build |
| Sign-off | the editor | approves anonymised wording before commit |

## Intake — the Google Form (the editor to create; spec below)

I can't create a Google Form from here (no Forms API in this session's tools), so build it
in Google Forms (~5 min) with these fields, then **link a responses Sheet** (Responses →
link to Sheets) and paste the form's **embed `src`** into `form_url:` in
`content/feedback/_index.md`.

Recommended fields (chosen so triage maps cleanly to ledger fields):

1. **Feedback type** — multiple choice: *Content accuracy · Bug / broken thing · Suggestion / feature · Praise · Other*. → maps to triage routing.
2. **Which page or domain?** — short answer (optional). → maps to ledger `domains` / link target.
3. **Your feedback** — long answer (required). → the raw text to anonymise into `theme`.
4. **Severity** (for bugs) — linear scale 1–3 or *Low/Med/High* (optional).
5. **Role** — *Clinician · Commissioner · Researcher · Other* (optional; helps weight, never published verbatim).

> **There is no email field. Removed 28 Jul 2026** (the editor: no individual replies), so the
> form holds no personal data at all and generates no subject-access or erasure obligation of
> its own. The response is the public ledger, not a private message. Consequence for this
> flow: an address can now only arrive inside the free-text answer — and `/legal/` deliberately
> asks for one there when the submission is a data-protection request about the email list.
> `feedback_triage.py` redacts email-shaped text at staging (`redact_emails`), so the request
> is actioned from the Sheet and the address never reaches the file triage works from.

Keep it short — six fields max, two required at most. The Form's own confirmation message
should say responses are read and that themes + responses appear publicly on `/feedback/`,
identities never.

## Receive — how Claude gets the responses

Two supported paths; primary first:

1. **Direct Sheet read — IMPLEMENTED (24 Jul), `--sheet`.** `scripts/feedback_triage.py
   --sheet` reads the Form-responses Sheet using the **same service account
   `drive_sync.py` already uses** (`GDRIVE_SERVICE_ACCOUNT_KEY`), not the MCP connector —
   so it works headlessly, in CI, and in any session regardless of which connectors are
   wired. Per the decoupling rule the Sheet ID is **not committed**: it lives in
   `FEEDBACK_SHEET_ID`, the same pattern as `GDRIVE_FOLDER_ID`.
   *Implementation note:* a Google Sheet is not a plain file — `files().get_media()`
   returns 403 for Google-native types — so this uses `files().export_media(mimeType=
   "text/csv")` and feeds the result through the identical parser the `--csv` path uses
   (`parse_rows`), so the two intake paths cannot drift.
   **Setup, one-time:** share the responses Sheet with the service account's
   `client_email` (Viewer is enough), and set `FEEDBACK_SHEET_ID`.
2. **CSV export (fallback):** the editor downloads the responses as CSV; Claude runs
   `scripts/feedback_triage.py --csv <file>`. Same parser, same output.

**Tested:** `scripts/test_feedback_triage.py` (7 tests, run with plain `python3`) covers
column mapping against the exact headers Google Forms generates from the six questions
below — including the near-collision between *"Feedback type"* and *"Your feedback"* —
blank-submission dropping, CSV/Sheet parser equivalence, and the hard privacy contract
that **no respondent email can reach the staging file**.

Either path lands raw responses in a **gitignored staging file** (`data/_feedback_staging.json`)
— never straight into the public ledger.

## Triage — staging → curated ledger

For each staged response:
1. **Anonymise** — strip names, employer, location, any identifying detail. Addresses are
   already redacted by the script, but check: automated redaction is a floor, not a
   substitute for reading. If a quote can't be de-identified, paraphrase the theme.
2. **Dedupe + theme** — fold similar items into one themed entry (the synthesis ethos
   applied to feedback). One ledger row per theme, not per submission.
3. **Classify + status** — set `status` from the editorial vocabulary:
   `Received` → `Planned` → `Done` (link), or `Declined` (with reason) / `Out of scope`
   (named, not dropped).
4. **Decide action** — if it implies site/content work, open a priority in `CLAUDE.md` /
   `TODO.md` (or a GitHub issue) and link it; otherwise resolve to Declined/Out of scope
   with an honest one-line reason.
5. **the editor signs off** the anonymised wording, then it's committed.

## Action + publish — the ledger contract

Curated entries live in `data/feedback.json` (`entries: []`), schema documented in that
file's `note`:

```json
{ "date": "YYYY-MM-DD",
  "theme": "what was said, aggregated/anonymised",
  "status": "Received|Planned|Done|Declined|Out of scope",
  "response": "what we did (may contain inline HTML)",
  "link": "/optional/path/to/the/change/",
  "domains": ["d01"] }
```

As work progresses, flip the entry's `status` (e.g. `Planned` → `Done`) and add the `link`.
The `/feedback/` page (`layouts/responses/list.html`) renders the rest automatically.

## Netlify-credit discipline (ties to the minimise-deploys rule)

Ledger updates are commits → production builds. **Batch them**: curate a set of entries and
commit once, not one entry per push. Doc/triage-only commits (this file, staging notes) are
auto-skipped by the `netlify.toml` `ignore` rule, so only real `data/feedback.json` changes
build. See `PARK-CHECKLIST-2026-06.md` for the full deploy-minimisation levers.

## Dependencies before this runs live

1. the editor creates the Google Form (fields above) + links a responses Sheet.
2. Embed `src` pasted into `form_url:` (`content/feedback/_index.md`).
3. `FEEDBACK_SHEET_ID` provisioned (secret/env) for the direct-read path — or use CSV.
4. Netlify credits restored so the ledger actually publishes.
