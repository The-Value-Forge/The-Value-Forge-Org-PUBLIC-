---
name: icon-design
description: >-
  Design marks, icons, and small SVG artwork for The Value Forge — domain marks,
  editorial devices, data-adjacent glyphs, favicon/brand marks — in the site's own
  seam-and-node drawing grammar, with a mandatory render-and-verify loop. Use whenever
  creating or revising any SVG mark or icon, choosing between a Lucide utility icon
  and a house identity mark, or iterating on visual concepts for page furniture.
---

# Designing marks and icons for The Value Forge

Never ship a mark you haven't looked at. This skill exists because pictogram clip-art
reads as someone else's site: TVF's identity marks are drawn in the site's own
**seam-and-node grammar**, verified by rendering at target size and iterating.
Workflow distilled from neonwatty's `logo-designer-skill` (iterate + preview at sizes)
and Anthropic's `canvas-design` (subtractive refinement, reference over literalism);
grammar is TVF's own. Companion to the `ui-design` skill (which owns page-level rules).

## The two species — choose deliberately

- **Utility icons** (nav, actions, wayfinding: search, chevrons, back, archive):
  **Lucide only**, per the `ui-design` skill. Never redraw what Lucide does well.
- **Identity marks** (domain marks, editorial devices, cover/brand artwork, favicon):
  **house grammar only** — a generic pictogram (syringe, brain, dumbbell) says the
  category; a house mark says *this publication's thesis about it*. Don't put
  clip-art where identity belongs, and don't hand-draw what a utility icon covers.

## The house grammar — seam and node

The site already draws one way (hero seam panel, monthly band, pattern
constellations, the ∞ read-mark). All identity marks use this vocabulary:

- **The seam** — a smooth cubic-bézier trajectory line, `stroke-width` ~1.6 in a
  24-grid, `currentColor`, round caps. It is the subject's *story over time*.
- **The node** — a filled circle (r ≈ 2 in a 24-grid) ON the seam. It marks the
  event the domain/pattern cares about: the intervention, the encounter, the
  crossing. One node per mark; the node is the point.
- **The context line** — optional second line at `stroke-opacity: .35`,
  `stroke-width` 1: the counterfactual, the baseline, the boundary (dashed for a
  boundary). Quiet by construction.
- **Meaning is the shape.** The trajectory must encode the thesis (lifted early /
  converging / settling / stepped / crossing out). If the shape would survive with
  its meaning swapped, it's decoration — redraw. Record each mark's one-line meaning
  in a comment beside it in the template.

Grid and rendering floors: 24×24 viewBox; nothing thinner than 1px at the *rendered*
size (at 30px render, a 1px stroke in-grid ≈ 1.25px — fine; at 16px it isn't — thicken
or simplify); centre optically, not geometrically (a rising diagonal sits low-left);
2px in-grid clearance to the viewBox edge; `fill="none"` + `currentColor` throughout.

**Small-size law (learned 5 Jul 2026, front-page domain marks):** below ~30px
rendered, hairline line-work loses to the bold mono labels beside it and sibling
marks blur together — prefer **fills and contained silhouettes** (solid shapes,
filled discs, tiles) over trajectories. The seam grammar excels at *artwork* scale
(hero panel, band backgrounds, covers); at icon scale, reach for weight first. A
size-strip render is not enough on its own: also screenshot the mark **in situ**
next to its real neighbours before judging.

## Process — directions, then refinement, always rendered

1. **Say what the mark must mean** in one sentence (the thesis, not the object).
   If the meaning sentence names a physical object, you're drawing the wrong thing.
2. **Draft 2–4 meaningfully different concepts** — different trajectories/structures,
   not nudges of one idea. Cheap: they're 3–5 paths each.
3. **Render before judging.** Build the size strip (below) and *look* at every
   candidate at final size, 2× size, and 16px. Kill anything ambiguous at final size.
4. **Refine subtractively.** Adjust curve tension, node position, optical centre;
   remove any element that doesn't carry meaning. Two rounds minimum — the first
   render always lies about weight and centring.
5. **Verify in place** — inject into a local copy of the real page (harness below)
   next to its real neighbours before proposing. Show before/after to the editor;
   nothing ships without his eye.

## The render harness (scratchpad, never committed)

Chromium + playwright-core are available in remote sessions
(`executablePath: '/opt/pw-browsers/chromium'`). Two patterns:

- **Size strip** — a throwaway HTML file: each candidate repeated at 16 / 22 / 30 /
  60px on both `--vf-surface` and `--vf-ink` backgrounds, in `--vf-teal-dark`;
  screenshot, read the image, judge.
- **In-page preview** — mirror the live site (`wget -p -k` via the session proxy;
  direct Chromium access to external hosts may be blocked — serve the mirror on
  localhost with `python3 -m http.server`), inject the candidate with
  `page.evaluate`, screenshot the component. This is the before/after evidence for
  any proposal. Keep all of it in the scratchpad.

## Integration rules (inherit from `ui-design`)

`currentColor` only — no hex in SVG attributes; colour comes from the parent's token.
Decorative marks: `aria-hidden="true"`; meaningful ones: an accessible name.
Inline in the template; no icon fonts; no external fetches. SVGO anything hand-drawn
(the browser tolerates sloppy markup; the repo shouldn't).

## Validation checklist

- [ ] Species right: Lucide for utility, house grammar for identity — not mixed.
- [ ] The mark's meaning stated in one sentence; the shape encodes it.
- [ ] ≥2 distinct concepts rendered and compared before refinement.
- [ ] Judged from *rendered images* at final size, 2×, and 16px — never from code.
- [ ] One node; context lines quiet; optical centring checked; clearance kept.
- [ ] `currentColor`, aria, inline; SVGO'd; meaning comment in the template.
- [ ] In-page before/after shown to the editor and approved before any site commit.
