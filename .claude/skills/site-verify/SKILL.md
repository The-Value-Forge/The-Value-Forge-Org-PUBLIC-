---
name: site-verify
description: >-
  Verify The Value Forge visually without a Netlify build — render the built
  site in headless Chromium, screenshot pages at the house breakpoints, capture
  console errors, and compare before/after. Use when confirming any UI/layout/
  CSS change, when a deploy preview is unavailable (e.g. under a Netlify build
  freeze), or when asked to "check how it looks". Generalises the icon-design
  render-and-verify loop from single marks to whole pages.
---

# Site verify — local render-and-verify for whole pages

Never judge visual work from code. This skill renders the actual built site in the
environment's preinstalled Chromium and produces screenshot evidence — the same
mandatory look-before-you-ship discipline `icon-design` applies to marks, generalised
to pages. Under a Netlify build freeze this is the **only** visual check available;
with previews it's still the faster first pass. Pattern adapted from Anthropic's
`webapp-testing` skill (anthropics/skills, Apache-2.0), simplified for a static site.

## Setup facts (this environment)

- Chromium is preinstalled: launch `playwright` / `playwright-core` with
  `executablePath: process.env.PLAYWRIGHT_BROWSERS_PATH ? undefined : '/opt/pw-browsers/chromium'`
  — or just rely on `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`, which is set. **Never
  run `playwright install`.**
- A static site needs no dev server semantics: build once, serve `public/` with
  anything (`python3 -m http.server`). `hugo server` works too but rebuilds on
  watch — for verification, prefer the frozen `public/` build you're actually judging.
- Write harnesses and screenshots to the session scratchpad, never into the repo.
- **`hugo` may not be installed.** Several sessions have had no Hugo binary, which
  makes the "build once, serve `public/`" loop below impossible. That is not a reason
  to fall back to judging CSS by reading it — use the mirror loop instead.
- **Chromium cannot reach the internet here.** It fails with `ERR_CONNECTION_RESET`
  even against `example.com`, with or without `proxy: { server: process.env.HTTPS_PROXY }`.
  `curl` *does* work through the proxy. So: fetch with curl, render from localhost.

## Mirror loop — when there's no local Hugo (use this before giving up)

Renders a **deployed** page (preview or production) in the local browser, which is
the only way to see visual truth in a session with no Hugo. Cost: a handful of curls.

```bash
B="https://deploy-preview-N--thevalueforge.netlify.app"   # or https://thevalueforge.org
mkdir -p mirror && cd mirror && curl -s "$B/" -o index.html
python3 - <<PY
import re, os, subprocess
h = open('index.html').read()
for u in sorted(set(re.findall(r'(?:href|src)=["\']?(/[^"\'> ]+\.(?:css|js|png|svg|webp|woff2|jpg))', h))):
    p = u.lstrip('/'); os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    subprocess.run(['curl','-s',"$B"+u,'-o',p], check=False)
PY
python3 -m http.server 8231 &            # then point Playwright at localhost:8231
```

**⚠️ Serve it. Never open the mirror with `file://`.** The site's assets are
referenced by absolute path (`href=/css/bundle.min.….css`), and under `file://`
those resolve to the *filesystem root* — so nothing loads, the page renders in
Times New Roman on a transparent background, and it looks exactly like a
catastrophic CSS regression. Wasted a cycle on 27 Jul verifying a dead-CSS
removal that was in fact fine. The tell is `getComputedStyle(document.body)
.backgroundColor` returning `rgba(0, 0, 0, 0)` instead of the paper colour
`rgb(244, 242, 236)` — check that before believing any visual verdict.

**⚠️ Strip `integrity` attributes if you edit any mirrored asset.** Hugo emits
Subresource Integrity hashes on the CSS bundle. Patch the mirrored CSS to try a fix
and the hash no longer matches, so the browser silently *refuses the whole
stylesheet* — the page renders completely unstyled and every measurement is garbage,
with no console error that names the cause. Cost an hour on 26 Jul. Either
`re.sub(r'\sintegrity="[^"]*"','',html)` before serving, or check
`document.styleSheets` lists the bundle before trusting any number.

**Measure, don't eyeball, for alignment work.** `getBoundingClientRect()` on the
elements that should share an axis, print the centres, and compare. This is what
finally located a masthead bug three rounds of CSS-reading had missed:

```js
const c = s => { const r = document.querySelector(s)?.getBoundingClientRect();
                 return r ? r.top + r.height/2 : null; };
// then diff the centres — a non-zero spread IS the bug, and its size names the cause
```

## Standard loop

```bash
hugo --minify && npx pagefind --site public
python3 -m http.server 8123 --directory public >/dev/null 2>&1 &
```

```js
// verify.mjs — node verify.mjs <path> [more paths...]
import { chromium } from 'playwright-core';
const exe = '/opt/pw-browsers/chromium';
const widths = [375, 768, 1120];               // the house breakpoints
const browser = await chromium.launch({ executablePath: exe, headless: true });
for (const path of process.argv.slice(2)) {
  const slug = path.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home';
  for (const width of widths) {
    const page = await browser.newPage({ viewport: { width, height: 1200 } });
    const errors = [];
    page.on('console', m => m.type() === 'error' && errors.push(m.text()));
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto(`http://localhost:8123${path}`, { waitUntil: 'networkidle' });
    await page.screenshot({ path: `${slug}-${width}.png`, fullPage: true });
    if (errors.length) console.log(`CONSOLE ERRORS ${path} @${width}:`, errors);
    await page.close();
  }
}
await browser.close();
```

Then **read the screenshots** (they are the evidence — actually look at them) and kill
the server (`pkill -f "http.server 8123"`).

## What to verify (per changed page)

- **All three widths** — 375 / 768 / 1120. Most regressions live at 375.
- **Console clean** — zero JS errors (the timeline and cards scripts must initialise;
  a template change that breaks their expected DOM shows up here, not in the build).
- **No horizontal scroll** at 375 (`page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)`).
- **Before/after when polishing:** screenshot `main`'s build first (git stash or a
  worktree), then the change, and compare side by side. Judge against the `ui-design`
  hard rules — registers, gold, hairlines — not just "does it render".
- **States, not just the happy path:** empty sections (they collapse by design),
  a card with broken art (SVG fallback must fill the box), long titles, the
  reduced-motion variant (`page.emulateMedia({ reducedMotion: 'reduce' })`).

## Page set for a sweep

When a change is global (tokens, main.css, head/masthead/footer partials), verify this
minimum set: `/` (home) · `/signal/` (list + pager) · one signal single ·
`/monthly/` · `/archive/` and `/archive/browse/` · `/patterns/timeline/` (the JS-heavy
page) · `/feedback/` · one domain page. Otherwise: the changed page(s) plus home.

## Boundaries

- This skill **verifies**; it does not decide. Visual judgement lives in `ui-design`
  (and `icon-design` for marks); accessibility gates in `web-quality` and the
  checklist. Report what the screenshots show against those rules.
- Screenshot diffs here are evidence for a human decision, not an automated
  pass/fail pixel gate — don't build a brittle CI pixel-diff without being asked.
- Verifying is freeze-safe (nothing is committed); the *change being verified* may
  still be build-gated — sequencing lives with the PR, not this skill.

## Validation checklist

- [ ] Screenshots taken at 375/768/1120 and actually read.
- [ ] Console errors: zero (or explained and fixed).
- [ ] No horizontal scroll at 375; hit targets ≥ 24px (44px for primary controls).
- [ ] Empty/fallback/reduced-motion states checked where the change touches them.
- [ ] Server killed; artefacts stayed in the scratchpad.
