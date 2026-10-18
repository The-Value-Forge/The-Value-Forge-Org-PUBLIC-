# Feedback Google Form — exact build spec (v1)

_Written 24 July 2026. Build this in Google Forms exactly as written, then do the three
handover steps at the bottom. Companion to `FEEDBACK-PROCESS-MAP-v1.md` (the pipeline)
and `scripts/feedback_triage.py` (the backend that reads the responses)._

> **⚠️ The question wording is an integration contract, not just copy.**
> Google Forms uses each question's text **verbatim** as the column header in the
> responses Sheet, and `feedback_triage.py` maps columns by matching keywords in those
> headers. The load-bearing words are marked **`like this`** below. You can freely edit
> help text, options and ordering — but if you change a load-bearing word, the parser
> will mis-map or drop that column. `scripts/test_feedback_triage.py` pins the exact
> wording below; if you do change it, tell me and I'll update both together.

---

## Form-level settings

**Title:** `Feedback — The Value Forge`

**Description (shown under the title):**

```
This publication is in early build, and the fastest way to make it better is to
tell us what's wrong with it.

There is no reply to this form and no email field — we don't write back. Where
something sent here leads to a change, it appears on the site's feedback page:
what was said, and what we did. That record is the answer, and it's public.

Nothing here identifies you. Don't include your name or anyone else's.
```

**Settings — these matter:**

| Setting | Value | Why |
|---|---|---|
| Collect email addresses | **Off** | Forms' built-in collection is automatic and mandatory, and would identify every respondent. There is no optional email question either (see below) — the form is designed to hold no personal data at all. |
| Limit to 1 response | **Off** | Would force Google sign-in, which identifies respondents and blocks anyone without an account. |
| Allow response editing | Off | Not needed; adds confusion. |
| Show progress bar | Off | It's one short page. |

---

## ⚠️ WHAT IS ACTUALLY LIVE (28 Jul 2026) — read before using this spec

The form is **built and wired**: `form_url` is set in `content/feedback/_index.md`.
It has **TWO** questions, not the five below. the editor's call, and the right one —
*"I'm only asking a couple of questions. Otherwise it gets too complicated."* A short
form that gets filled in beats a thorough one that doesn't.

| | Live question | Type | Maps to |
|---|---|---|---|
| Q1 | **"Category of Feedback"** — Something looks factually wrong · Something's broken or won't load · A suggestion · Praise or encouragement | Multiple choice, required | `type` (via the "category" keyword) |
| Q2 | **"What Would You Like to Tell Us?"** | Paragraph, required | `raw` (via the "tell us" keyword) |

**Q1's title changed twice on 28 Jul, and the second change broke the parser** —
worth recording, because it is the clearest possible illustration of the warning at
the top of this file.

It began as "Untitled Question", which matched no keyword: the category was dropped
but the free text still mapped, so the failure degraded. the editor then retitled it
"Category of Feedback" — better for the reader, and worse for the code, because that
header contains the word **feedback**, which was `raw`'s first keyword. The dropdown
column captured the free-text slot, so every submission would have staged
"A suggestion" as the feedback and silently discarded what the person actually wrote.
No error. Just a worthless staging file.

`feedback_triage.py` now resolves keywords most-specific-first (and loops keywords
rather than headers), so a question that merely *mentions* feedback can no longer
outrank the one that asks for it. **The wording is the editor's to choose; the parser
adapts.** Four tests pin it, including the two earlier titles, and they were proved
to fail against the old code.

The five questions below are kept as the **menu**, not the plan — if a field is ever
added, take its wording from here so the keyword mapping still works.

## The questions

Six questions, one required. Aim is under 60 seconds to complete.

### 1. What **`type`** of feedback is this?

- **Type:** Multiple choice
- **Required:** Yes
- **Options** (in this order):
  - `Something looks factually wrong`
  - `Something's broken or won't load`
  - `A suggestion`
  - `Praise or encouragement`
  - `Something else`

> *Why "factually wrong" is first:* for an evidence publication it is the most
> consequential thing a reader can report, and it routes to the corrections process
> rather than the ordinary backlog.

### 2. Which **`page`** or **`domain`** is this about?

- **Type:** Short answer
- **Required:** No
- **Help text:**
  ```
  A URL, a page name, or a domain (D01–D05) — whatever's easiest. Leave blank if it's about the publication generally.
  ```

### 3. Your **`feedback`**

- **Type:** Paragraph (long answer)
- **Required:** Yes
- **Help text:**
  ```
  If you're flagging a factual error, please say what source you're going by — a PMID, DOI or link makes it much faster to check and correct.
  ```

> *Why the source prompt lives here rather than as its own question:* it keeps the form
> to six fields while still getting the one piece of information that makes an accuracy
> report actionable under the static-copy rule.

### 4. **`How serious`** is it?

- **Type:** Multiple choice
- **Required:** No
- **Options:**
  - `Blocks me from using the site`
  - `Annoying but I worked around it`
  - `Minor / cosmetic`
  - `Not applicable`

> **There is deliberately no email question. Do not add one.**
> Removed 28 Jul 2026 on the editor's decision: he is not replying to submissions
> individually, so an address would be personal data collected for a purpose that
> never happens. With no email field the form holds **no personal data at all** —
> nothing to disclose, nothing to secure, nothing to erase, and no subject-access
> request it can generate. That is a materially smaller obligation than "we hold
> an address but promise to be careful with it", and it is bought simply by not
> asking.
>
> The one thing it costs: no way to come back on a vague correction and ask which
> paragraph. Accepted — the answer is to make the feedback question itself good
> enough to stand alone, which is why Q3 asks for specifics.
>
> If a submission is a **data-protection request about the email list** (erasure,
> subject access), the person needs to state their subscribed address in the
> free-text answer. `/legal/` tells them to. That address arrives as text, is
> acted on, and is not staged — `feedback_triage.py` drops anything email-shaped
> wherever it appears.

### 5. Your **`role`**

- **Type:** Multiple choice
- **Required:** No
- **Options:**
  - `Clinician`
  - `Commissioner or manager`
  - `Researcher`
  - `Patient, carer or member of the public`
  - `Other`
  - *(tick "Add 'Other'" off — the explicit Other option above covers it)*

> Used only to weight and understand feedback in triage. Never published, not even
> in aggregate, unless it becomes genuinely informative and is stated as such.

---

## Confirmation message

Settings → Presentation → "Confirmation message":

```
Thank you — that's genuinely useful.

We won't write back. There's no email field and no correspondence: submissions are
collected and reviewed, in part automatically, and there's no timescale.

The answer, when there is one, is public. Where something sent here changes what we
do, it goes on the feedback page — what was said, what we did — anonymised. That
record is how you find out, and it's the same record everyone else sees.

If you've shown us a published claim is factually wrong, that's the one thing we hold
ourselves to: verified errors are corrected in the open, dated, at /corrections/.
```

**Do not soften this into a promise of a reply.** The wording matches
`content/terms/_index.md` and `content/feedback/_index.md` deliberately — the form's
confirmation screen is the *first* thing a submitter reads, so if it sets a higher
expectation than the site's terms, the terms are the thing that looks like small print.
the editor, 28 Jul: "we really need to keep expectations very low."

---

## Handover — three steps, then I can take over

1. **Link a responses Sheet.** Responses tab → the green Sheets icon → *Create a new
   spreadsheet*. This is what the backend reads.
2. **Share that Sheet with the service account.** Open the Sheet → Share → paste the
   `client_email` from the `GDRIVE_SERVICE_ACCOUNT_KEY` credentials (the same service
   account the daily Drive sync already uses) → **Viewer** is enough → Send.
   *Without this the backend gets a 404/403 — the Sheet ID alone is not access.*
3. **Send me two things:**
   - the **Sheet ID** (the long string in the Sheet's URL between `/d/` and `/edit`) —
     I'll set it as `FEEDBACK_SHEET_ID`, never committed, same pattern as
     `GDRIVE_FOLDER_ID`
   - the **form's embed `src`** (Send → `<>` → copy the `src="..."` value) — goes into
     `form_url:` in `content/feedback/_index.md` and activates the page

Then I run `python3 scripts/feedback_triage.py --sheet` and the pipeline is live.

## What happens after that (so you know what you're agreeing to)

Responses land in the Sheet. The script stages them into a **gitignored** file with
emails stripped out — the script physically refuses to write the public ledger. I then
anonymise and theme them, and you sign off the wording before anything is committed to
`data/feedback.json` and appears on the site. Nothing auto-publishes.

## Optional next step — a house-styled form

Once the Form exists I can replace the Google iframe on `/feedback/` with a form styled
like the rest of the site that posts to the same endpoint: same Sheet, same backend, no
third-party frame on a site that states it runs no analytics. It needs the form's
`entry.NNNN` field IDs, which I can read off the live form. Caveat: those IDs change if
you later edit the questions, so it's worth doing only once the wording is settled.
