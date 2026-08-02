# Translator v3.5 — patterns amendment (SUPERSEDED — v3.5 LIVE 15 Jul 2026)

**Status: SUPERSEDED.** The fully assembled v3.5 (`ROUTINE-weekly-translator-COMBINED-v3.5.md`) was pasted live by the editor on 15 July 2026. This amendment document is retained as the design record of exactly what changed from v3.4; do not apply it — the assembled v3.5 already contains it.

**Why (design record: `docs/PATTERNS-LONGITUDINAL-DESIGN-2026-07.md`):**
1. *Fidelity:* full-file replacement asks the model to re-transcribe an ever-growing longitudinal record every month — one bad cycle corrupts the register. v3.5 emits only the month's **delta**; the sync merges append-only. (Sync support is already live: `patterns-delta-YYYY-MM.json` is routed, merged idempotently in month order, and the register is guarded against loss either way.)
2. *References:* patterns are the site's most consequential claims; §8 discipline applies. Every new history entry MUST carry references (structured PMIDs/citations and/or `supporting` slugs of the site's own signals/syntheses). The sync warn-flags violations.
3. Fixes `intelligence_window` being emitted empty.

---

## EDIT 1 — replace the whole `#### PATTERNS.JSON` section with:

#### PATTERNS-DELTA-YYYY-MM.JSON

The pattern register on the site (`data/patterns.json`) is a cumulative, append-only longitudinal record. You never rewrite it. When a `PIPELINE-SUMMARY-YYYY-MM.md` (or equivalent monthly source) is translated and produces surviving public patterns, emit a **delta file** named `patterns-delta-YYYY-MM.json` (the month of the source) containing ONLY:

- patterns that are **new** this month, and
- **new history entries** (and any status change) for existing patterns.

Existing patterns with nothing new this month are simply omitted. If no monthly source is translated, do not create any patterns file.

Schema:

```json
{
 "generated": "YYYY-MM-DD",
 "source": "Monthly Review",
 "intelligence_window": "YYYY-MM",
 "patterns": [
 {
 "id": "VF-P1",
 "title": "...",
 "status": "established",
 "confirmation_level": "...",
 "first_appeared": "YYYY-MM",
 "domains": ["D01"],
 "history": [
 {
 "date": "YYYY-MM",
 "status": "...",
 "note": "...",
 "references": [
 {"pmid": "42100443"},
 {"cite": "NHS England Board Item 8, 4 June 2026"}
 ],
 "supporting": ["2026-07-05-hero-extended-rehabilitation-frailty"]
 }
 ]
 }
 ]
}
```

Pattern rules:

- **Delta only.** Include a pattern only if it is new this month or has a new history entry / status change this month. For an existing pattern, include only the NEW history entries — never re-emit past history.
- **`id` is permanent.** Reuse the existing id for an existing pattern; a new pattern takes the next free VF-Pn. Never renumber.
- **`first_appeared` is immutable.** Set it only for a NEW pattern (this month). For existing patterns, omit it or copy it exactly — the site ignores attempts to change it.
- **`intelligence_window`** is the source month, `"YYYY-MM"`. Never emit it empty.
- **Every history entry MUST carry references.** At least one of:
  - `references`: a list of `{"pmid": "…"}` for PubMed-indexed evidence (only PMIDs verified in the source — never invent one) and/or `{"cite": "…"}` (with optional `"url"`) for non-PubMed evidence (policy documents, board papers, guidance).
  - `supporting`: a list of slugs of THIS SITE's signals/syntheses that evidence the observation — the filename slug without prefix or extension (e.g. `signal--2026-07-05-hero-extended-rehabilitation-frailty.md` → `"2026-07-05-hero-extended-rehabilitation-frailty"`). Only slugs of files you have emitted this cycle or that the monthly source explicitly names.
  - An observation that cannot cite at least one reference does not clear the bar for the register — keep it in the Monthly narrative instead (same principle as the Signal weight bar).
- `status` passes through verbatim: `established` or `provisional` (the site also understands `emerging`, `qualified`, `contested`, `discarded`, `superseded` — use them only when the monthly source explicitly supports the state).
- PMIDs may still appear in the note prose (the site auto-links them), but the prose never substitutes for the structured `references` field.
- Do not create new patterns unless the monthly source explicitly supports them. Do not infer pattern history beyond what the source contains.

## EDIT 2 — cross-reference, line ~14

Replace: "`patterns.json` continues to be built from `PIPELINE-SUMMARY-YYYY-MM.md`."
With: "`patterns-delta-YYYY-MM.json` (the monthly pattern-register delta) is built from `PIPELINE-SUMMARY-YYYY-MM.md`; the site merges it append-only into the register."

## EDIT 3 — filename lists (sections ~6/8, lines ~606/615/632)

Replace each occurrence of the output filename `patterns.json` with `patterns-delta-YYYY-MM.json`, and the `generated`-field note applies to the delta file unchanged.

---

## Activation checklist (the editor)

1. Apply the three edits to the live translator in Claude.ai (or paste a fully assembled v3.5).
2. Dual-home: create the Drive copy of the amended routine; trash the superseded v3.4 Drive copy.
3. No repo action needed — sync-side support (delta routing, append-only merge, monotonic guards, reference warnings) is already deployed with tests (`scripts/drive_sync.py`, `scripts/test_drive_sync_patterns.py`).
4. First live delta cycle: eyeball the sync's Action summary — guard failures appear as 🛑, missing references as ⚠️.
5. Optional back-fill: the 11 existing patterns carry PMIDs in note prose only; a one-off structured back-fill can be done by hand-PR (allowed — it's additive) or left as-is (display-level linking already works; guards police new entries only).
