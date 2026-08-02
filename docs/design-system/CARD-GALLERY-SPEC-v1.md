# Card Gallery + Snap-Scroll Reader — spec v1

Status: **v1 — first build (placeholders live).** Owner: Claude Code session 6 (14 Jun 2026).
Supersedes the deferred sketch in CLAUDE.md ("procedural SVG card art seeded from slug").

## Purpose

Turn the flat list views on `/signal/` and `/archive/` into a browsable **card gallery**
with an Instagram/TikTok-style **snap-scroll single-card reader**, plus a per-article
**read-state indicator** built from the brand ∞ mark. The card art is generated at Hugo
build time and seeds off the article slug, so the pipeline needs **zero changes**.

## Design constraints (non-negotiable — from CLAUDE.md design system)

1. **No invented hex.** All colour from `--vf-*` tokens. Card art uses `--vf-teal`,
   `--vf-ink`, `--vf-surface`, `--vf-teal-light` only.
2. **Gold is VAT-only.** No gold in card art, indicators, or chrome.
3. **No NHS blue.** "Confirmed" → `--vf-teal-dark`.
4. **Three type registers.** Card title → `--vf-font-head` (Georgia). All dates, tags,
   read-time, badges → `--vf-font-mono`. Description → `--vf-font-body`.
5. **Hairlines over shadows.** 1px `--vf-rule` borders; radius 4px (cards), 999px (pills).
6. **No new domain colours.** Domains are differentiated by *motif*, not hue — the palette
   stays monochrome-teal. (Five new domain colours were considered and rejected: they would
   break the "gold is the only accent" discipline.)

## Card art — generative, slug-seeded

`layouts/partials/card-art.html`. One inline SVG per card, `viewBox 0 0 400 500`,
`preserveAspectRatio="xMidYMid slice"` so the same art crops cleanly into both the grid
thumbnail (landscape) and the reader (portrait/full-bleed).

- **Seed:** `hash.FNV32a` of `.File.ContentBaseName` (the slug). Falls back to `urlize .Title`
  for generated pages. Deterministic → **same art every build, every time.**
- **No-repeat guarantee:** distinct slug → distinct seed → distinct parameters. Two posts
  cannot generate identical art unless they share a slug (Hugo forbids that anyway). This is
  the "don't repeat the same image" rule, enforced by construction rather than bookkeeping.
- **Motif by domain** (primary domain = first entry in `.Params.domain`):

  | Domain | Code | Motif | Editorial rationale |
  |---|---|---|---|
  | Acute Frailty | d01 | Strata seams (stacked arcs) | the "seam" hero language; layered reserve |
  | Clinical Psychology | d02 | Interference waves | overlapping signal, normalisation |
  | Palliative Care | d03 | Radial rings | concentric care, continuity outward |
  | Therapies & AHPs | d04 | Woven lattice (crosshatch) | function, structure, rehabilitation |
  | OPAT | d05 | Orbital ellipses | dose cycles, course over time |
  | (multi / none) | — | ∞ seam | cross-domain = the synthesis loop |

  Seed-derived parameters (count, rotation, phase, curvature) vary the motif *within* a
  domain so two frailty signals look related but never identical.

### The curated image archive (future — the override hook)

When the real per-domain image archive is built, it plugs in here with **no template change**:

- Add `card_image: "cards/d01/seam-03.webp"` to a post's frontmatter → `card-art.html`
  renders that image (from `static/images/`) instead of the generative SVG.
- **No-repeat rule for curated images** (to implement when the archive exists): images live
  under `static/images/cards/<domain>/`. Auto-assignment (for posts without an explicit
  `card_image`) walks the gallery in date order and pulls the next unused image from the
  domain pool, recording it in a build-time used-set so no image repeats until the pool is
  exhausted; only then does it wrap. Explicit `card_image` always wins and is excluded from
  the auto pool. Until then, generative art is the universal fallback and is already unique.

## Read-state indicator — "the ∞ completes itself"

The active-nav infinity mark is reused as a **reading-progress glyph**.

- `layouts/partials/read-mark.html` emits the ∞ as inline SVG with `pathLength="100"`, so
  `stroke-dashoffset` maps linearly to progress: `offset = 100 × (1 − progress)`.
  Empty loop = unread; half-drawn = started; complete loop = read.
- **On an article** (`single.html`): a small fixed `.read-progress` widget (∞ + mono
  "X min"). As the reader scrolls the article body, the ∞ draws itself. At ≥ 98 % scrolled the
  loop closes, pulses once, and the article is marked **read**. Partial progress is stored too.
- **On cards:** the ∞ in each card footer reflects stored state — empty / partial / complete —
  and the card gets `.is-read` (subtle: reduced art opacity + a completed mark) or
  `.is-reading`.
- **Read-time:** Hugo `.ReadingTime` (whole minutes), mono, subordinate to the ∞ so it informs
  without shouting. (the editor's "maybe too much info" note: read-time is deliberately quiet.)

### Storage

`localStorage` key `tvf:read:v1` → `{ "<slug>": { "p": 0..1, "done": bool, "t": <epoch ms> } }`.
~40 lines, no login. Slug = `data-slug` on the card / `body[data-slug]` on the article.
Degrades safely: no JS → cards render fully, just without read-state; reader toggle hidden.

## Snap-scroll reader (the Instagram/TikTok cards — priority)

- The grid `<ul.card-gallery>` and the reader are the **same DOM**; a toggle button flips
  `.is-reader` on the container and CSS does the rest (no duplicate markup).
- Reader = `scroll-snap-type: y mandatory`, each card `scroll-snap-align: center`, one card per
  viewport, full-bleed art behind, text overlaid in a legible scrim. Swipe / arrow / wheel
  moves card to card. `Esc` or the toggle returns to grid; scroll position preserved.
- Entering a card in the reader marks it `.is-reading`; finishing the article (via its page)
  marks it read. The reader is a browse surface — full read-state still comes from the article.

## Files

| File | Role |
|---|---|
| `layouts/partials/card-art.html` | generative SVG / `card_image` override |
| `layouts/partials/read-mark.html` | reusable ∞ progress glyph |
| `layouts/partials/card-grid.html` | gallery + reader markup (takes `pages` dict) |
| `layouts/signal/list.html` | `/signal/` → card grid |
| `layouts/archive/list.html` | `/archive/` → card grid (signal ∪ synthesis ∪ monthly) |
| `layouts/_default/single.html` | adds the ∞ reading-progress widget |
| `assets/js/cards.js` | read-state, grid⇄reader toggle, scroll→∞ progress |
| `assets/css/main.css` | `.card-gallery`, `.gallery-card`, `.snap-*`, `.read-*` (namespaced) |

**Namespacing:** the home-page briefing already owns `.card`. New components use
`.gallery-card` / `.card-gallery` / `.read-*` to avoid collision.

## Out of scope for v1 (follow-ups)

- The real curated image archive + its auto-assignment loop (hook is in place).
- Synthesis list adopting the gallery (partial is generic; one line when wanted).
- Reader "unread only" filter; keyboard help overlay.
