# Front page design review — July 2026

_5 Jul 2026 session, run under the `ui-design` skill against the rendered production
page (screenshotted at 1440px and 390px). Findings ranked; each item a decision for
the editor._

**Status (later same session):** the editor picked direction C (seam marks) for the
icons and approved the batch. Implemented on PR #26: #1 (sparkline removed,
constellation data-true), #3 (hero annotations live, centred against `slice`
cropping), #4 (all five seam marks, refined through the `icon-design` skill's
size-strip loop), #5 (strip icon `currentColor` + mono pattern-ID pill; patviz/qcover
hexes → token vars; heroviz gradient/rgba artwork left for the `main.css` migration).
**#2 (gold VAT strip) implemented** (the editor delegated the call, 5 Jul): the flag
lives in repo-owned **`data/vat_patterns.yaml`** — *not* `patterns.json`, which is
pipeline-owned and must never be hand-edited. The strip renders `.strip--vat`
(gold-light band, gold-dark label/glyph, `VF-P1 · VAT` pill) only when the pinned
pattern's id is in that list; VF-P1 seeded. CLAUDE.md's gold rule updated to name
this third (gated) gold surface. Also corrected en route: CLAUDE.md rule 6 was
stale — the `main.css` legacy names are already bridge aliases to `--vf-*` (PR #24).
Verified with a local Hugo 0.147.0 build (PyPI `hugo` wheels — GitHub binary
downloads are blocked in remote sessions).

**Icon revision (same day):** the seam marks failed the editor's eye in situ — hairline
trajectories at 26px are too light next to the bold mono labels, and the five read
too alike. Five replacement sets were mocked on the real page; the editor picked
**Set 2: numbered roundels** (mono `01`–`05` on a `--vf-teal-light` disc,
`--vf-surface-raised` on row hover) — implemented as `.dom-roundel`. "For now": the
solid-geometric Set 3 (thesis-as-filled-shape) is the recorded candidate if a more
expressive mark is ever wanted. Lesson folded into the `icon-design` skill: at small
sizes prefer fills and contained silhouettes over hairline line-work.

## What's working (don't touch)

- **The hero reads like a broadsheet front.** Three-column structure (thesis headline /
  featured synthesis / dark seam panel) with the registers doing their jobs — mono
  eyebrow-date, Georgia headline with the teal *forged* italic and hero-dot, sans
  standfirst. The seam panel is the page's signature dark moment and bookends nicely
  with the inverted Monthly band.
- **Section numbering 01–05** encodes reading order; `All X →` affordances are
  consistent; hairline discipline holds throughout; the domain list pairs icon +
  `D0x · NAME` mono code + a genuinely editorial one-line thesis per domain — that
  copy is excellent.
- Mobile fold is acceptable: nav wraps to three rows but the headline still lands.

## Findings (ranked)

### 1. The signal-card sparkline is fake data — the publication's own anti-pattern

Every signal card renders the **same hardcoded polyline** (`2,20 22,17 42,19 62,13
82,8` — always trending up) styled as a data graphic next to a real status pill.
A chart-shaped decoration that encodes nothing is precisely the "fake stat" tell the
craft rules ban — and on an *evidence* card it quietly contradicts the static-copy
ethic (nothing data-shaped without a source). The pattern-card mini-constellation
(`patviz`) has the same defect: identical node graph for every pattern.

**Options:** (a) remove both graphics — the cards are strong without them;
(b) make them true: seed the constellation from the pattern's actual `domains` count
and the sparkline from real history (`patterns.json` `history`/`first_appeared`) —
only where data exists, no fabricated shape.
**Recommendation:** (b) for the constellation (cheap: node count = domain count),
(a) for the sparkline unless/until a real per-signal time series exists.

### 2. The front page never spends its one licensed boldness — there is no VAT moment

Gold is reserved for the single most consequential VAT statement, and the front page
uses **zero gold**. The system's signature move is absent from the page that defines
the publication. The cross-domain pattern strip is the natural candidate: the pinned
pattern ("Earlier specialist input → better outcomes… more value-added patient time")
*is* a VAT statement.

**Options:** (a) give the strip the VAT treatment (gold-light fill, gold-dark label)
**only when** the pinned pattern is explicitly VAT-consequential — an editorial flag
(`vat: true`) in `patterns.json`, not a blanket restyle; (b) add a one-line VAT
ledger/callout elsewhere (e.g. under the hero standfirst) stating the lens itself.
**Recommendation:** (a) — it keeps gold meaning something, driven by an editorial
decision per pattern. Needs the editor's call on the flag semantics.

### 3. Hero seam panel: make its annotations true

The contour/seam artwork is good signature art, but its mono annotations (`D01—D05`,
year) are static while sitting on a panel labelled "Continuous synthesis". Cheap win:
drive the small annotations from real state (live pattern count, latest pattern ID,
current month) so the intelligence layer is honest all the way down. Keep the art
itself exactly as is.

### 4. Domain icons — two of five don't encode their domain

Rendered at 22px teal, reviewed against each domain's own thesis line:

| Domain | Current icon | Verdict |
|---|---|---|
| D01 Acute Frailty | `person-standing` | **Weak.** Reads "generic person/wayfinding figure"; says nothing about function, falls, deconditioning. Least-bad in Lucide; a composed figure-with-cane (Lucide grammar, via Lucide Studio) would be honest and distinctive. |
| D02 Clinical Psychology | bloom/Ψ-like composed glyph | **Ambiguous at size** — reads as a flower/tulip. Better: a conversation motif (`messages-square`/`message-circle`) — the domain's thesis is *effective therapeutic contact*, the encounter, not the organ. (A brain is the biomedical abstraction; the dialogue is the lived encounter — the foundation's own Kleinman distinction, made visible.) |
| D03 Palliative Care | `hand-heart` | **Keep.** Care/holding; right register, clear at size. |
| D04 Therapies & AHPs | `activity` (pulse trace) | **Wrong register.** A vitals trace reads acute monitoring, not rehabilitation/function — and collides with the sparkline graphics elsewhere on the page. Better: `dumbbell` (rehab/strength, honest if gym-flavoured) or a composed movement/gait glyph. |
| D05 OPAT | `syringe` | **Keep.** Parenteral therapy is the domain's subject — still true even as the editorial line evolves toward "don't give IV antibiotics at all". Optional later refinement: a composed home+infusion mark (out-of-hospital is the point). |

Any swap stays Lucide-only / Lucide-grammar per the `ui-design` skill; icons also
hard-code nothing (they're already `currentColor` — the good pattern on this page).

### 5. Housekeeping (already logged, fold into the same session)

- ~12 hex-inlined token values in `index.html` SVGs (strip icon, sparkline, patviz,
  heroviz, qcover) → `currentColor`/CSS variables, with the `main.css` migration.
- The pattern strip could carry the pattern's mono ID (`VF-P1`) alongside the title —
  the intelligence layer should name its objects.
- Two "How we work →" links on one page (hero + method block) — harmless; if the hero
  link ever changes, point it at the archive or patterns instead.

## Suggested sequencing

One site-touching session (single Netlify preview): #1 remove/true-up the fake data
graphics · #4 icon swaps the editor approves · #5 hex migration + strip ID. Then #2 (VAT
strip) as its own small change once the `vat:` flag semantics are agreed, and #3
alongside whichever lands second.
