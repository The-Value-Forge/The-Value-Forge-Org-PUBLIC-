# Feedback feature — "You said, we did" (spec v1)

_Drafted 19 June 2026 (session 9). A design proposal to develop with the editor._

> **STATUS (28 Jun 2026): BUILT + parked.** The feature was built on `claude/brave-mccarthy-xyoowa`.
> **Intake decision changed: Google Form embed, NOT Netlify Forms** (to save Netlify credits) —
> so the "Half 1 — Intake" recommendation below is superseded. For the current intake + the
> receive→triage→action mechanism, see **`FEEDBACK-PROCESS-MAP-v1.md`**. The half-2 ledger
> design below still holds and was built as specified.

## Why

A transparent feedback loop for alpha/beta testers. It is the publication's
own ethos — **name the gap, honest scope, close the loop** — turned on the
product itself. Two halves: **intake** (collect feedback) and a public
**"You said, we did" ledger** (respond, in the open). The ledger is the
differentiator; most sites collect feedback into a void.

## Half 1 — Intake (collect)

**Recommendation: Netlify Forms.** Native to the stack (no backend, no new
infra), free tier covers alpha volume, built-in spam protection (honeypot +
optional challenge), submissions land in the Netlify dashboard and can notify
by email or Slack webhook.

- Hugo + Netlify Forms: add a plain HTML `<form data-netlify="true">` (Netlify's
  build bot detects it in the static output). A hidden honeypot field for spam.
- Suggested fields: role (optional — clinician / commissioner / researcher /
  other), feedback type (content accuracy / bug / suggestion / praise), the
  comment, page-context (hidden field, auto-filled with the referring URL),
  optional email for follow-up (kept private, Netlify only).
- Routing: Netlify notification → a Slack channel (e.g. `#tvf-feedback`) and/or
  email. Optionally pulled into Drive later via a routine.

**Alternatives considered:** Google Form (fits the Google ecosystem but is an
off-site embed, weaker visual integration); GitHub Issues (too technical for
clinical testers); Formspree/Tally (extra dependency). Netlify Forms wins on
fit + zero new infra.

## Half 2 — The "You said, we did" ledger (respond, publicly)

A content/data-driven page, like the pattern register — curated, not a raw
comment dump.

- Source: `data/feedback.json` (manifest-driven, edited in-repo by Claude Code —
  like `card_art.json`), so entries are curated and anonymised before they go
  public.
- Each entry: date, **theme** (what was said, aggregated/anonymised — never
  tester identities or raw identifying text), **status**, **response/action**
  (with a link to the change when shipped).
- **Status vocabulary mirrors the editorial finding-status discipline:**
  - `Received` — logged, not yet triaged
  - `Planned` — accepted, on the roadmap
  - `Done` — actioned (link to the page/commit)
  - `Declined` — with a stated reason (honesty, like a DISCARDED finding)
  - `Out of scope` — named, not silently ignored
- Aggregate similar feedback into themes so the ledger reads as patterns, not
  noise — the synthesis ethos applied to product feedback.

## Page & placement

- A single `/feedback/` page: intake form at the top, the ledger below.
- Design-system compliant: reuse status pills, hairlines, mono labels.
  **Gold stays VAT-only** — map feedback states to teal / neutral / red per the
  existing pill conventions, never gold.
- Optional: a subtle **Alpha** affordance in the header/footer — _"This is an
  alpha. Your feedback shapes it — see what's changed →"_ linking to `/feedback/`.
- Optional later: a per-page "Feedback on this page" link that deep-links the
  form with the page context prefilled.

## Triage workflow

1. Tester submits via `/feedback/` → Netlify Forms → notify Slack/email.
2. the editor + Claude triage: dedupe, theme, set status + response.
3. Curated entries added to `data/feedback.json` (in-repo) → rebuild → ledger
   updates automatically. Curated, not auto-published, to keep it anonymised
   and themed.
4. When an item ships, flip status → `Done` with a link.

## Privacy / decoupling

- Publish themes + responses, never tester identities or raw comments that
  contain identifying detail. The optional follow-up email stays private
  (Netlify only).
- No NHS-org identifiers, consistent with the standing decoupling rule.

## Decisions

- **Ledger is PUBLIC from alpha** (decided 19 Jun 2026, the editor). The
  "you said, we did" ledger is visible to everyone from the alpha cut — not
  tester-gated. Transparency is the point; gating it would defeat it.

## Open decisions (next session)

1. Intake channel — confirm **Netlify Forms** (recommended) + routing target
   (which Slack channel?).
2. Single `/feedback/` page vs also per-page feedback links.
3. Anonymity/curation wording (the public note explaining how feedback is
   handled).

## Build order (when greenlit)

1. `/feedback/` page + Netlify form (intake) + Slack/email routing.
2. `data/feedback.json` schema + ledger layout (status pills, themed entries).
3. Alpha affordance + (optional) per-page feedback links.
