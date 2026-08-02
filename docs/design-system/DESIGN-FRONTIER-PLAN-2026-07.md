# Design Frontier Plan — sanctioned modern-web techniques (July 2026)

**Status:** ADOPTED as the sanctioned technique set, 14 Jul 2026 (skills board session — minutes: `docs/SKILLS-BOARD-2026-07-14.md`). **Freeze rule clarified by the editor same day: deploy PREVIEWS don't cost credits — only production deploys (merges to `main`) do.** So implementation may build + preview on draft PRs freely; merging remains gated on the editor.

**Wave 1 progress (14 Jul, draft PR #37):** items 1–4 IMPLEMENTED and preview-staged (speculation rules · view-transition crossfade · `color-mix` sweep, verified pixel-identical against `main`'s build · print/offprint stylesheet, verified via print-media render) plus the `head-meta.html` SEO partial. Item 5 split: **5b (reading-progress hairline) CLOSED as redundant** — the site already has the ∞ read-mark that fills with scroll progress (`cards.js`), a more distinctive solution to the same need; **5a (timeline spine draw) deferred** — the timeline is JS-rendered SVG and needs its own pass.

**Provenance:** design-frontier research pass over elite editorial sites (The Pudding, FT visual journalism, Stripe Press, Works in Progress, Asterisk), museum/collection digital experiences (Rijksmuseum, Wellcome Collection/Cardigan, Public Domain Review, MoMA), and the 2026 CSS platform. Filter applied: TVF's locked token system, three registers, gold-is-VAT-only, hairlines, compositor-only motion, vanilla-only stack. The unifying finding: what the best of these sites share is not spectacle but **continuity, typographic finish, and object-dignity** — pages that feel like one continuous space, type set with print-grade care, artefacts with persistent identity. Awwwards-register maximalism (WebGL, cursor followers, scroll-hijack) fails the restraint filter and the reduced-motion ethic; per the project's own McGilchrist framing, spectacle is the instrument grasping attention away from the content. **The restraint is the brand.**

## Ship order — wave 1 (first unfrozen UI PR)

| # | Technique | Effort | What it is |
|---|---|---|---|
| 1 | **Speculation Rules prerender** | S | `<script type="speculationrules">` in `head.html`: prerender likely-next pages on hover (`eagerness: moderate`). Near-instant navigations; invisible; Chromium-only progressive enhancement (Safari/Firefox ignore it). Exclude search/feed via `where` matchers. |
| 2 | **Cross-document View Transitions — root crossfade** | S | `@view-transition { navigation: auto; }` in `main.css` + ~200ms root crossfade; hard opt-out under `prefers-reduced-motion` (`navigation: none`). The site becomes one continuous exhibition space. Degrades to normal navigation (Chrome/Edge 126+, Safari 18.2+; Firefox flagged). |
| 3 | **`color-mix()` sweep** | S | Replace every remaining raw-hex/rgba straggler (hero seam panel gradient/rgba artwork in `layouts/index.html`, any `main.css` alpha variants) with `color-mix(in oklab, var(--vf-…) N%, transparent)`. **Ratifies the rule: derived tones via `color-mix` from `--vf-*` tokens are legal; raw hex stays forbidden.** Recurring mixes may become `--vf-*-wash` tokens (tokens file → Drive-first). Closes CLAUDE.md's declared hex-straggler debt. |
| 4 | **Print/offprint stylesheet** | S–M | Upgrade `print.css` into a designed artefact: Georgia body ~10.5–11pt/1.4, sources list forced visible, pills as bordered text, card art suppressed, `break-inside: avoid` on figures/VAT callouts, `orphans/widows: 3`, printed citation line ("The Value Forge · CC BY 4.0 · retrieved …"), `@page` margin boxes where supported. NHS readers circulate PDFs by email — the Monthly flagship as a printable offprint is a credibility feature. |
| 5 | **Scroll-driven progress (informational motion only)** | S–M | (a) Evidence-timeline spine "draws" on scroll (`animation-timeline: view()`, scaleY, `@supports`-wrapped); (b) 2px `--vf-teal-dark` reading-progress hairline on the Monthly flagship only (`animation-timeline: scroll(root)`). Compositor-only, zero JS, motion that tells you where you are. Reduced-motion: none. |

## Wave 2 — "gallery finish" PR

| # | Technique | Effort | Notes |
|---|---|---|---|
| 6 | **Container-query card refactor** | M | `container-type: inline-size` on card slots; one card partial self-composes across gallery/featured/Previously/domain contexts via `@container`; card-title type in `cqi`. Baseline 2023. Sets up Phase 4 exhibition contexts for free. |
| 7 | **`:has()` state styling** | S each | Gallery hover-dim (`.card-grid:has(.gallery-card:hover) .gallery-card:not(:hover) { opacity: .85 }` — gallery-lighting attention, compositor-safe); facet-active states in the archive catalogue; ledger empty state. Replaces would-be JS. |
| 8 | **Subgrid catalogue alignment** | S–M | Meta lines/hairlines align across cards in mixed rows — the difference between a grid and a *ledger*. Baseline 2023. |
| 9 | **Named view-transition morphs** | M | Card title/art morphs into article header (`view-transition-name` stamped per page from Hugo's page identity). The one flourish; ship after #2 proves quiet. |

## Wave 3 — timed to editorial moments

| # | Technique | Effort | Notes |
|---|---|---|---|
| 10 | **Tufte-style sidenotes** | M | `sidenote` shortcode + prose grid gaining a `minmax(0,18rem)` margin column ≥~1100px, collapsing to bordered inline notes below. Mono register, CSS counters, zero JS. Surfaces the `sources:` discipline typographically. Time with a Monthly flagship edition. |
| 11 | **`initial-letter` drop caps** | S | Monthly flagship + Editorial lane only (never signals). Georgia, ink — **never gold**. Graceful Firefox fallback; no float hacks. |
| 12 | **Popover evidence-label definitions** | M | Reader-key definitions on tap/hover of evidence pills via native `popover` (Baseline 2024). Anchor positioning inside `@supports` only. |
| 13 | **Plex Mono metrics-matched fallback + self-host** | S | Spec lives in `.claude/skills/web-quality/SKILL.md` (font section). Tokens-stack change → Drive-first. |
| 14 | **`text-box-trim`** | S | Cap-height-true Georgia headline alignment against hairlines. Chrome 133+/Safari 18.2+, degrades silently. Ride along with any wave. |

## SKIPPED — decided, don't relitigate

- **CSS-only carousels** (`::scroll-marker`) — wrong grammar; the exhibition register is "featured object + Previously rows", not a swipe rail. Revisit only if Phase 4 needs a horizontal wall.
- **Deep-zoom object viewers** (Leaflet/Micrio) — our objects are arguments, not gigapixel paintings; a JS map library for decoration violates the weight budget. The transferable idea (object-dignity, permalinked object pages) is already built.
- **Awwwards-register motion** — WebGL heroes, cursor effects, scroll-hijack, text scramble: fails compositor-only, fails reduced-motion ethics, fails the register.

## Standing guards (apply to every item)

1. Motion ships inside `@supports` + full `prefers-reduced-motion: reduce` opt-out.
2. Tokens-only colour; `color-mix` derivations from `--vf-*` are the only legal tints; tokens-file changes are Drive-first dual-homed.
3. Zero framework bytes; progressive enhancement only — every technique degrades to today's site.
4. Nothing threatens Lighthouse 92/98/100/100 (items 1, 2, 13 should improve it); verify with `web-quality` measurement + `site-verify` screenshots before/after.
5. Gold appears in none of the above except where a VAT semantic already owns it.
