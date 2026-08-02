# Translator v3.6 — Monthly cross-reference discipline (DRAFT, not yet live)

**Status: DRAFT awaiting the editor.** Surgical amendment to the LIVE v3.5 translator's **Monthly review (flagship)** section. Nothing else changes. Not urgent-today, but **should be live before the August monthly cycle** so Edition Two publishes referenced.

**Why (found by the editor, 15 Jul):** the July flagship carries 2 `sources:` across 3,679 words — against 13–14 sources per ~1,800-word weekly synthesis — with zero PMIDs in the body and six evidence labels attached to unnamed studies ("a length-of-stay prediction tool outperformed… [Primary Study]"). Root cause: the Monthly is translated from the monthly meta-synthesis, which synthesises the month's *already-cited* weekly artefacts without re-carrying their citations; the Monthly schema's `sources: []` plus no restated cross-reference rule let it sail through the self-checks. The evidence exists — it lives in the month's signals and syntheses — but the flagship gives the reader no path to it. Same disease as the pattern-register gap fixed in v3.5; this is the remaining limb.

## EDIT — append to the "Monthly review (flagship)" section of the live routine, after the Body paragraph:

**Monthly cross-reference discipline (the flagship is the synthesis of synthesis — every claim stays reachable):**

- **Every finding restated in the Monthly must be traceable by the reader.** For each finding carried from the month's intelligence, do ONE of:
  1. **Carry the citation.** Copy the full `sources:` entry from the weekly artefact that first published it (you translated those artefacts; their `sources:` blocks are the citation source of truth — never re-derive from memory), and keep the inline reference in the body; or
  2. **Cross-reference the site's own artefact.** Link inline to the signal or synthesis that carries the full citation, as a relative link: `[the week's signal on structured coding](/signal/2026-06-12-specialist-palliative-care-coding/)`. The linked artefact's reference list then satisfies the reachability rule for that claim.
- **Evidence labels never float.** A `[Primary Study]` / `[Audit/Data]` / `[Guidance]` / `[Synthesis]` label in the Monthly body must sit adjacent to a named, cited source or an internal cross-reference link — never against an unnamed study.
- **Policy and governance facts** (settlements, mandates, targets, board items, statutory instruments) carry a `sources:` entry with publisher reference / URL, exactly as in a Signal.
- **The self-check extends:** §7.6 citation cross-check applies to the Monthly in full — every body-referenced study/guidance/policy/audit either has a `sources:` entry or an internal cross-reference to the artefact that does. A Monthly that cannot meet this for a claim drops that claim's specificity (state the pattern without the unnamed study) or drops the passage, under the degrade-loudly rule.
- `sources:` order remains first-mention; internal cross-reference links do not create `sources:` entries.

## Retro-fix option for the July edition (the editor's call, separate from activation)

The July flagship can be brought up to this standard by producing a corrected same-name `monthly--2026-07-….md` in TVF-PUBLIC-OUTPUT (a Claude.ai session task: re-run the Monthly translation against the same source with the discipline above; newest-wins sync replaces the current copy). Repo hand-edits are NOT the route — the daily sync overwrites them. If left as-is, Edition One stands as pre-discipline; the register applies from Edition Two.

## Activation checklist (the editor)

1. Paste the EDIT block into the live v3.5 translator's Monthly section (or ask for a fully assembled v3.6 to paste whole).
2. Dual-home per the rule; supersede the Drive copy.
3. Watch Edition Two (August): `sources:` count and inline cross-links are the tell.
