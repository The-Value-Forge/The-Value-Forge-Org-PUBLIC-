# Accessibility & anti-pattern checklist (v1)

_Pre-ship reference for The Value Forge. One page, run it before merging any UI/markup
change. Adapted to TVF's stack from the checklist idea in the `ui-ux-pro-max-skill` repo
(nextlevelbuilder, MIT) — generalised design data not adopted; only the checklist concept._

TVF already scores ~98 on Lighthouse accessibility — this keeps it there. Pair it with the
design-system rules in `CLAUDE.md` (tokens, three type registers, gold-is-VAT-only).

## Perceivable

- [ ] **Contrast** — body text ≥ 4.5:1, large text/UI ≥ 3:1, against its actual background.
      Use `--vf-*` tokens (which are tuned for this); never hand-pick a hex.
- [ ] **Colour is never the only signal.** Status pills (teal/neutral/red) and finding
      states must also carry **text** (e.g. "Confirmed", "Declined") — don't rely on hue.
      Same for domain card art (motif differs, not just colour).
- [ ] **Images/SVG** — meaningful images have `alt`; decorative SVG card art is
      `aria-hidden="true"` / `role="presentation"` so it's skipped by screen readers.
- [ ] **Iframes have a `title`** — the Google Form embed on `/feedback/` carries
      `title="The Value Forge feedback form"`. Any new embed needs one.

## Operable

- [ ] **Keyboard** — every interactive thing (nav dropdowns, the card-gallery reader,
      back button, search modal, pager) is reachable and usable by Tab/Enter/Esc. Test the
      Domains dropdown and the snap-scroll reader with no mouse.
- [ ] **Visible focus** — a clear focus ring on links, buttons, form fields, cards. Don't
      remove outlines without a token-based replacement.
- [ ] **Focus order & traps** — modal/search open → focus moves in, Esc closes and returns
      focus; no keyboard traps in the reader or dropdowns.
- [ ] **`prefers-reduced-motion`** respected — reveal animations and the ∞ read-mark draw
      must no-op under reduced motion (already wired; keep it that way for new motion).
- [ ] **Targets** — interactive targets ~≥ 44px; whole-card stretched links keep a large
      hit area (already the pattern for signal/pattern cards).

## Understandable

- [ ] **One `<h1>` per page**, headings nest in order (no skipping levels) — they carry the
      document outline, not just visual size. Mind the three type registers but don't fake
      hierarchy with font alone.
- [ ] **Link text is self-describing** — no bare "click here"/"read more" without context
      (screen-reader users navigate by link list).
- [ ] **Form fields have real `<label>`s** (applies if any native form is added; the Google
      Form handles its own).
- [ ] **`lang` set** on `<html>` (en-GB) and on any inline language shifts.

## Robust

- [ ] **Semantic HTML first** — `<nav> <main> <article> <button> <time>` over `<div>`s;
      ARIA only to fill genuine gaps, never to paper over non-semantic markup.
- [ ] **`aria-current`** on the active nav item (already in place — keep it on new sections).
- [ ] **Landmarks** — one `<main id="main-content">`, a skip link to it, header/footer
      roles intact.

## Anti-patterns — don't ship these

- [ ] Meaning by colour alone · removing focus outlines · placeholder text used as a label ·
      auto-playing motion that ignores reduced-motion · icon-only controls with no
      accessible name · `tabindex` > 0 · justified body text / ultra-low-contrast "elegant"
      greys · headings chosen for size not structure · a new `<iframe>` with no `title` ·
      a colour pill with no text label.

## Quick verification

- Run `hugo --minify && npx pagefind --site public`, then the Netlify Lighthouse run (on a
  real build) — keep Accessibility ≥ 95.
- Tab through the changed page start-to-finish with no mouse.
- Spot-check contrast on any new token/background pairing.
