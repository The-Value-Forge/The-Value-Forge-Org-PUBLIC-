---
name: ui-design
description: >-
  Design and polish The Value Forge's UI — Hugo templates, CSS, cards, galleries,
  pills, page furniture, motion — inside the locked TVF design system. Use whenever
  creating or editing anything visual: files under layouts/ or assets/css/, card art,
  new components, hero/landing work. Enforces tokens-only colour, the three type
  registers, gold-as-VAT-only, hairlines over shadows, restrained compositor-only
  motion, and the pre-ship accessibility checklist.
---

# Designing UI for The Value Forge

Execute visual work with an editor's eye inside a design direction that is already
**locked** — warm paper, ink, a teal analytical layer, one gold VAT moment, and a mono
intelligence register. The job is never to find a new aesthetic; it is to make every
pixel encode something true about the content. Distilled from Anthropic's
`frontend-design` skill (anthropics/skills) and the `baseline-ui` quality gates in
`ibelick/ui-skills` (MIT), rebuilt for this site's stack: Hugo templates + plain CSS,
no Tailwind, no React.

Read before touching visuals: the design-system section of `CLAUDE.md`,
`assets/css/tvf-tokens.css` (canonical tokens), and
`docs/design-system/TVF-DESIGN-SYSTEM-reference-v1.md` (component-level spec).
Run `docs/design-system/ACCESSIBILITY-CHECKLIST-v1.md` before any UI change merges.
The sanctioned modern-CSS technique set (view transitions, `color-mix` derived tones,
scroll-driven progress, container queries, subgrid, print/offprint) lives in
`docs/design-system/DESIGN-FRONTIER-PLAN-2026-07.md` — implement from that plan, in
its ship order, rather than reintroducing techniques it has already ranked or SKIPped.

## When to use

- Editing or creating anything in `layouts/` or `assets/css/`.
- Card gallery / card art / archive / pills / nav / hero / landing work.
- Adding a new component, page type, or piece of page furniture.
- Any motion, hover, reveal, or interaction work.

## Hard rules (non-negotiable, from CLAUDE.md)

1. **Never invent hex values.** Every colour is a `--vf-*` token from `tvf-tokens.css`.
   A new colour means a new token there first (docs + assets copies stay identical).
2. **Three type registers — the register *is* the meaning:** body/prose →
   `--vf-font-body`; editorial headlines → `--vf-font-head` (Georgia); all data,
   labels, dates, nav, tags → `--vf-font-mono` (IBM Plex Mono). Never blur them, and
   never fake hierarchy with size alone.
3. **Gold is VAT-only.** `--vf-gold*` appears only in `.vat-callout` and
   Provisional/Updated pills — the single most consequential VAT moment per view.
   Decorative gold is forbidden.
4. **No NHS blue anywhere.** "Confirmed" maps to `--vf-teal-dark`.
5. **Hairlines over shadows.** 1–2px `--vf-rule` borders for structure; no box-shadow
   separation. Border-radius 4px default, 999px pills only.
6. **No new uses of the legacy `main.css` names** (`--ink`, `--teal`, `--gold`) — they
   are pending migration to `--vf-*`; don't grow the debt.

## Craft principles (the editorial eye)

- **Structure is information.** Numbering, eyebrows, dividers, labels must encode
  something true about the content — a domain ID, an evidence state, a date — never
  decorate. If a structural device would survive with its content shuffled, cut it.
- **Spend boldness in one place.** One signature moment per view (in this system,
  usually the gold VAT callout or the inverted Monthly card); everything around it
  stays quiet and disciplined. Two competing accents means one is wrong.
- **Typography carries the meaning through register, not novelty.** Distinctiveness
  here comes from the mono intelligence layer sitting against the serif editorial
  voice — sharpen that contrast; don't import new faces or weights.
- **Restraint is the house style.** Remove any decoration that encodes nothing.
  Extra animation and ornament read as AI-generated; hairlines and precision read
  as edited.
- **Match complexity to editorial purpose.** The flagship earns richer treatment;
  a signal card stays terse. Don't give a minor element a major element's dressing.

## Two-pass process

1. **Plan against the tokens.** Before writing CSS, name the tokens, register(s), and
   structural devices the change will use, and what each one encodes. If the plan
   needs a colour, weight, or effect the system doesn't have, the plan is wrong —
   redesign within the system (or, rarely, propose a token change explicitly).
2. **Critique before coding.** Re-read the plan against the hard rules: anything
   blurring registers, inventing colour, decorating without encoding, or double-
   spending boldness gets revised. Only then build.

## Baseline quality gates (adapted from `baseline-ui`, MIT)

**Motion** — only where it serves the content, never by default. Animate compositor
properties only (`transform`, `opacity`) — never `width`/`height`/`top`/`left`.
Interaction feedback ≤ 200ms. Everything respects `prefers-reduced-motion` (the site's
reveal animations and the ∞ read-mark already no-op under it — keep that true for any
new motion). No looping animation that runs off-screen.

**Surfaces** — no gradients, no glow effects as affordances. Elevation is
`--vf-surface-raised` + a `--vf-rule` hairline, not shadow.

**Type & data** — `font-variant-numeric: tabular-nums` for aligned numbers and data
columns (the mono register makes this near-automatic; keep it explicit in tables).
`text-wrap: balance` on headings, `text-wrap: pretty` on prose, as progressive
enhancement. No justified body text; no ultra-low-contrast "elegant" greys.

**Layout** — a fixed z-index scale (reuse the existing steps; no arbitrary values).
Prefer `dvh` over `vh` for full-height sections; respect `safe-area-inset` on any
fixed element.

**Interaction** — visible focus states on everything interactive (token-based ring;
never bare `outline: none`). Icon-only controls carry an `aria-label`. Errors render
next to the action that caused them. Empty states offer one clear next action. Never
block paste in inputs.

## Typography mechanics (the craft under the locked registers)

The three registers fix *which* faces; these mechanics fix *how they're set*.
(Distilled from `wondelai/skills` `web-typography`, MIT — Jason Santa Maria's
*On Web Typography*. Typeface choice is locked; only mechanics transfer.)

- **Measure:** prose containers `max-width: 65ch` (keep 45–75ch); beyond 75ch the eye
  loses the return sweep. Card standfirsts and wall-label captions count as prose.
- **Line-height by register:** body 1.5–1.7; Georgia headlines 1.1–1.25; mono
  labels/UI 1.3–1.4. Longer measures need more leading.
- **Body floor:** 16px minimum, prefer ~18px for article pages; must survive 200% zoom
  without overflow or truncation.
- **Hierarchy:** vary at most two of size/weight/colour between adjacent levels; keep
  a consistent modular ratio (~1.2–1.333) between heading sizes; never skip heading
  levels. Squint test: structure should survive blurring.
- **Fluid type** via `clamp()` (already the house pattern) — derive min from the 375px
  view and max from 1120px; no breakpoint jumps for type.
- **Font loading is a typography decision:** the mono register must not reflow on
  swap — self-hosting + a metrics-matched fallback (`size-adjust`/`ascent-override`)
  is spec'd in the `web-quality` skill; any change to the `--vf-font-mono` stack is a
  tokens-file change (Drive-first dual-home).

## Data graphics (charts, sparklines, the evidence timeline)

Data graphics are UI: **tokens-only colour applies in full.** Any chart, SVG plot, or
sparkline draws exclusively from `--vf-*` tokens — this explicitly **overrides the
generic `dataviz` skill's placeholder palette** whenever that skill is also active
(its method — form choice, encoding hierarchy, legends — is welcome; its hex values
are not). House precedents to follow: the Evidence Timeline (`assets/js/timeline.js`)
encodes evidence *type* as node radius and domain as lane — extend those encodings
rather than inventing parallel ones; gold in a data graphic means VAT-consequential
and nothing else; colour is never the sole signal (shape/label redundancy per the
accessibility checklist). Fake/illustrative data in a real chart is forbidden — the
front page's decorative sparkline was removed for exactly this (5 Jul); every plotted
point must be true of the content.

## Icons — Lucide for utility, house marks for identity

**Utility icons** (nav, actions, wayfinding) are **Lucide** (ISC) — hand-inlined 24×24
stroke SVGs (search, chevrons, back arrow are verbatim Lucide paths). **Identity marks**
(domain marks, editorial devices, brand artwork) are drawn in the house seam-and-node
grammar instead — see the `icon-design` skill, which owns that grammar and its
mandatory render-and-verify loop. For the Lucide side:

- **Source every new UI icon from Lucide** (lucide.dev). Never mix icon sets — no
  Heroicons/Material/Font Awesome one-offs. If Lucide genuinely lacks a motif, compose
  one in its grammar: 24×24 grid, 2px-class stroke, `stroke-linecap`/`join: round`.
- **Inline the SVG in the template.** No icon fonts, no external fetches, no JS icon
  components. Optimise anything hand-composed (SVGO); Lucide's copy is already clean.
- **`stroke="currentColor"` always** — colour comes from the parent's token-driven CSS.
  Never hardcode a hex inside an SVG attribute. (Legacy hex fills/strokes exist in
  `layouts/index.html` SVGs — token *values*, hex-inlined; they're pending migration
  alongside the `main.css` token cleanup. Don't add more.)
- **Established sizes:** 9px nav chevrons (stroke 2.5); 16–22px UI icons (stroke
  1.75–2). Keep stroke weight optically consistent at the rendered size.
- **Accessibility:** decorative icons carry `aria-hidden="true"`; icon-only controls
  carry an accessible name (existing pattern — keep it).
- **Icons are wayfinding, not decoration.** A new icon must encode something — a
  domain, an action, a state. Sparklines/charts are data graphics (different rules);
  card art stays the slug-seeded generative system — don't iconify either.

## Verification (before done)

- `hugo --minify && npx pagefind --site public` builds clean.
- Tab through the changed page start-to-finish, no mouse.
- Run `docs/design-system/ACCESSIBILITY-CHECKLIST-v1.md`; keep Lighthouse
  Accessibility ≥ 95 on the preview build.
- Check the page at a narrow viewport (~360px) and a wide one; nothing scrolls
  horizontally, hit targets stay ~≥ 44px.

## Validation checklist

- [ ] No new hex values, fonts, or weights; every colour is a `--vf-*` token.
- [ ] Registers intact: mono for data/labels, Georgia for editorial heads, sans body.
- [ ] Gold appears only in VAT callouts / Provisional–Updated pills; no NHS blue.
- [ ] Structure encodes content (labels, IDs, states) — no decorative devices.
- [ ] One boldness moment per view; hairlines not shadows; radius 4px / 999px only.
- [ ] Motion: compositor-only, ≤ 200ms feedback, reduced-motion respected.
- [ ] Icons: Lucide only, inlined, `currentColor`, sized to the established scale.
- [ ] Accessibility checklist run; keyboard pass done; build green.
