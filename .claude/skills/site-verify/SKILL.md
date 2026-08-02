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
