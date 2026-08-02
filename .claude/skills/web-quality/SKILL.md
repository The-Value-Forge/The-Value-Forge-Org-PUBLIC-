---
name: web-quality
description: >-
  Audit and improve The Value Forge's web performance, Core Web Vitals, and
  deep accessibility (WCAG 2.2). Use when asked to improve Lighthouse scores,
  page speed, font loading, LCP/CLS/INP, or to run an accessibility audit that
  goes beyond the one-page pre-ship checklist. Companion to `ui-design`, which
  owns all visual/token decisions — this skill owns the measurement and
  optimisation method.
---

# Web quality — performance & deep accessibility

The method behind the numbers. The site holds Lighthouse 92/98/100/100; this skill is
the path from a pass/fail gate to a repeatable optimisation practice. Distilled from
Addy Osmani's `web-quality-skills` (github.com/addyosmani/web-quality-skills, MIT —
`performance`, `core-web-vitals`, `accessibility`), rebuilt for this site's reality:
a static Hugo build on Netlify, plain CSS, two small vanilla JS files, no frameworks,
no third-party scripts. Visual authority stays with `ui-design`; the static-copy and
decoupling rules stay with `article-writing`.

## Core Web Vitals — thresholds and where TVF stands

| Metric | Good (p75) | TVF reality |
|---|---|---|
| LCP (loading) | ≤ 2.5s | Hero text/panel; static HTML → usually fine. Watch card images on archive/gallery pages. |
| CLS (stability) | ≤ 0.1 | Two live risks: webfont swap on the mono register; card art loading without reserved space. |
| INP (interactivity) | ≤ 200ms | Near-immune — ~460 lines of vanilla JS total, no hydration. Keep it that way. |

## Font loading — the site's #1 open performance item

`layouts/partials/head.html` loads IBM Plex Mono via a **render-blocking Google Fonts
stylesheet** (preconnects exist, but the CSS request still gates first render, and the
swap can shift every pill, date, and label — the mono register carries all the site's
data furniture). The fix ladder, in order of preference:

1. **Self-host the two weights** (400/600) as WOFF2 in `static/fonts/`, declare
   `@font-face` with `font-display: swap`, and `<link rel="preload" as="font"
   type="font/woff2" crossorigin>` the regular weight. Removes the third-party
   round-trip entirely (and a tracking surface).
2. **Metrics-matched fallback** to kill the swap shift: a second `@font-face` over a
   local monospace with `size-adjust` / `ascent-override` / `descent-override` tuned
   to Plex Mono's metrics, inserted into the `--vf-font-mono` stack. Token-stack
   changes touch `tvf-tokens.css` → **Drive-first dual-home rule applies**.
3. Subset to Latin (`unicode-range: U+0000-00FF`) if self-hosting.

Georgia and the system sans are local — zero cost. Never add another webfont.

## LCP checklist (static-site subset)

- [ ] LCP element ships in the initial HTML (always true for Hugo — keep it true;
      never move hero content behind JS).
- [ ] If the LCP element is ever an image: `fetchpriority="high"`, `loading="eager"`,
      explicit `width`/`height`, WebP/AVIF.
- [ ] Below-fold images: `loading="lazy" decoding="async"`.
- [ ] CSS bundle stays small (it's concatenated + minified + fingerprinted — good;
      don't add render-blocking `<link>`s to `head.html`).
- [ ] Netlify serves Brotli + HTTP/2 by default — nothing to do, don't break it.

## CLS checklist

- [ ] Every `<img>` (card art, covers) carries `width`/`height` attributes or an
      `aspect-ratio` — the generative-SVG fallback must occupy the same box as the
      bitmap it replaces.
- [ ] Fonts: metrics-matched fallback (above) or `font-display: optional`.
- [ ] Animations remain `transform`/`opacity` only (ui-design rule — also a CLS rule:
      compositor animations never shift layout).
- [ ] Never inject content above existing content (the read-state marks and reveal
      animations are safe patterns — keep new JS to that standard).
- [ ] `content-visibility: auto` (already on `/feed/`) needs `contain-intrinsic-size`
      to avoid scrollbar jumps.

## INP — keep the immunity

No task > 50ms on the main thread. If a future feature ever needs heavy work: chunk it
and yield (`scheduler.yield()` with a `setTimeout(0)` fallback), give visual feedback
before computing, and push analytics-grade work to `requestIdleCallback`. The stronger
rule for this site: **question whether the JS is needed at all** — the house pattern is
build-time computation in Hugo templates, `:has()`/CSS state where possible, JS last.

## Instant-navigation pair (freeze-gated implementation)

Speculation Rules prerender + cross-document View Transitions make an MPA feel like one
continuous document. Both are sanctioned, spec'd, and sequenced in
`docs/design-system/DESIGN-FRONTIER-PLAN-2026-07.md` — implement from there, not here.

## Performance budget (TVF-calibrated)

| Resource | Budget | Now |
|---|---|---|
| Total page weight | < 1 MB | Well under (text + a few card WebPs) |
| JS (compressed) | < 50 KB | ~15 KB unminified source — huge headroom; guard it |
| CSS (compressed) | < 60 KB | One bundle — fine |
| Fonts | < 100 KB | Two Plex Mono weights — fine once self-hosted |
| Third-party requests | 0 | Google Fonts is the only one — removing it hits the target |

A budget line is a *review trigger*, not a hard wall: anything pushing past one needs a
named justification in the PR.

## Deep accessibility — the WCAG 2.2 delta

`docs/design-system/ACCESSIBILITY-CHECKLIST-v1.md` remains the pre-ship gate. This is
the deeper audit layer, including the 2.2 criteria the checklist predates:

- **Target size (2.5.8):** every interactive target ≥ 24×24 CSS px (checklist says
  ~44px for primary controls — keep that as the comfortable standard; 24px is the
  floor for dense furniture like pagination and taxonomy chips).
- **Focus not obscured (2.4.11):** keyboard focus must never be hidden under sticky
  chrome. Give focusable content `scroll-margin-top` clearing the masthead.
- **Consistent help / consistent navigation (3.2.6/3.2.3):** the feedback route and
  nav order stay in the same relative position on every page — template-driven, so
  verify after nav changes.
- **Redundant entry (3.3.7)** and **accessible authentication (3.3.8):** apply to the
  feedback form when the Google Form activates (the embed inherits Google's handling;
  verify the surrounding page still labels the iframe and offers a text alternative).
- **Contrast:** AA minima — 4.5:1 normal text, 3:1 large text and UI components, and
  3:1 for focus indicators against adjacent colours. Check any *new token pairing*
  once at introduction, then it's settled system-wide.
- **Triage order** when an audit finds multiple issues: (1) missing labels/alt,
  contrast failures, keyboard traps, missing focus states; (2) heading structure,
  link text, skip links; (3) icon labels, landmark regions.

## Measurement

```bash
# Build, serve, audit locally (freeze-safe — no Netlify build needed)
hugo --minify && npx pagefind --site public
python3 -m http.server 8080 --directory public &
npx lighthouse http://localhost:8080/ --output json --output-path /tmp/lh.json --quiet
```

Compare category scores before/after any optimisation; screenshot evidence via the
`site-verify` skill. Field data (CrUX) becomes relevant post-alpha when real traffic
exists — note it, don't chase it yet.

## Validation checklist

- [ ] No new render-blocking requests in `head.html`.
- [ ] Every image has dimensions or aspect-ratio; fallbacks occupy identical boxes.
- [ ] New JS justified against the "does this need JS?" bar; total JS within budget.
- [ ] WCAG 2.2 delta checked for any new interactive component (24×24, focus not
      obscured, scroll-margin under sticky chrome).
- [ ] Local Lighthouse run recorded before/after; Accessibility stays ≥ 95.
- [ ] Any token-stack/font change dual-homed (Drive-first) per the tokens rule.
