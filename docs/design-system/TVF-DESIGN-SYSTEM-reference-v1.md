# The Value Forge — Design System & Layout Reference (for Claude Code)

Version: 1.0 — June 2026  
Status: Canonical for the WEBSITE build (Hugo → Netlify, repo the-value-forge/tvf-pipeline-spike)  
Companion files: `tvf-tokens.css` (same folder), `TVF-WEBSITE-design-principles-v1.md` (the "why")

---

## How to use this document

This is the implementation-facing spec: exact tokens, the three type registers, and the
DOM/CSS **layout structure** of the standing components — written so they can be rebuilt in
the site's existing stack (Hugo templates + plain CSS), not copied from React.

**Canonical token values are in `tvf-tokens.css`.** They match what the site already ships
(the 6 Jun correction). Do not invent new hex values or swap fonts. If a token must change,
change it in `tvf-tokens.css` and let every page consume it.

> Note on the HTML design kit: a separate high-fidelity prototype of these components exists
> (built in the Claude design environment) using **Spectral** for headlines and **IBM Plex Sans**
> for body. Those are the nearest *licensed-font* substitutes for prototyping only. The website's
> binding choices are **Georgia** (headlines) and **system sans** (body) as below. Where the
> prototype and this doc disagree, **this doc wins for the website.**

---

## 1. Colour tokens

| Token | Hex | Use |
|---|---|---|
| `--vf-ink` | `#1B2D3A` | Primary text, borders, inverted Monthly card background |
| `--vf-ink-mid` | `#3D5466` | Standfirst / secondary prose |
| `--vf-ink-muted` | `#6B7F8E` | Labels, dates, metadata, footer text |
| `--vf-surface` | `#F4F2EC` | Warm paper page background (never pure white) |
| `--vf-surface-raised` | `#FFFFFF` | Cards, elevated elements |
| `--vf-teal` | `#1B8694` | Domain IDs, section labels, links — all analytical/navigational colour |
| `--vf-teal-light` | `#E1F5EE` | Domain tag backgrounds, "Established" pill fill |
| `--vf-teal-dark` | `#0F6E56` | Pattern status text, deep teal accents |
| `--vf-gold` | `#B8945A` | VAT callout accent — **the single most consequential VAT moment per domain section. Nowhere else.** |
| `--vf-gold-light` | `#FAF0E0` | VAT callout block background |
| `--vf-gold-dark` | `#8B6020` | VAT label text |
| `--vf-contested` / `-light` | `#A32D2D` / `#FCEBEB` | "Contested" evidence pill |

**No NHS blue, anywhere.** Map a "Confirmed" state to `--vf-teal-dark`, not blue.

---

## 2. Typography — three registers, each load-bearing

The register *is* the meaning; do not blur them.

- **Body & prose** → `--vf-font-body` (system sans: `-apple-system, Helvetica Neue`). Clean, platform-native.
- **Editorial headlines** → `--vf-font-head` (**Georgia** serif). Entry titles, Monthly card headline, hero headline — anywhere prose is making an argument.
- **All structured information** → `--vf-font-mono` (**IBM Plex Mono**): dates, domain IDs, evidence labels, URLs, nav links, tags, signal-field labels and values. This makes the intelligence layer (mono) visibly distinct from the editorial voice (serif/sans).

---

## 3. Evidence & finding vocabulary (shared across the whole site)

**Evidence status pills** (how strong is the finding):
- `Established` — fill `--vf-teal-light`, text `--vf-teal-dark`
- `Provisional` — fill `--vf-gold-light`, text `--vf-gold-dark`
- `Contested` — fill `--vf-contested-light`, text `--vf-contested`

**Finding status markers** (what changed since last quarter): `NEW` · `CONFIRMED` · `UPDATED` · `DISCARDED`.
Pill fills: NEW → teal-light/teal-dark; CONFIRMED → teal-light/teal-dark (no blue); UPDATED → gold-light/gold-dark; DISCARDED → neutral grey on paper-warm.

**Inline evidence labels** (in body copy): `[Meta-analysis]` `[Primary Study]` `[Guidance]` `[Audit/Data]` `[Synthesis]` `[Unverified]`.

All pills: `font: --vf-font-mono; font-size: 11px; letter-spacing: 0.04em; padding: 3px 9px; border-radius: 999px;`

---

## 4. The five domains (fixed)

`D01 Acute Frailty` · `D02 Clinical Psychology` · `D03 Palliative Care` · `D04 Therapies & AHPs` · `D05 OPAT`

Five perspectives on one population (the city and its surrounding county); the key insights live at their intersections.

---

## 5. Component layout — the Reader Key ("How to read this publication")

A **standing orientation section that appears in every edition**, immediately after the cover.
Single column, ~880px max content width, generous vertical rhythm (≈52px between sections).
Page background `--vf-surface`. Order of blocks, top to bottom:

**5.1 Section opener**
- Row 1 (flex, space-between, baseline): left = mono eyebrow `THE VALUE FORGE QUARTERLY · READER KEY` in `--vf-teal`; right = mono edition stamp (`Edition · Quarter` over `Partnership`) in `--vf-ink-muted`.
- 2px solid `--vf-ink` rule beneath.
- `h1` in `--vf-font-head` (Georgia), ~40px, `--vf-ink`.
- Standfirst in `--vf-font-head` italic OR system-sans, ~19–22px, `--vf-ink-mid`.

**5.2 Section-label pattern (repeats before every block below)**
- Mono eyebrow, uppercase, ~11px, letter-spacing 0.08em, `--vf-ink-muted` — followed by a 1px `--vf-rule` hairline. (Quiet; not teal-on-teal.)

**5.3 VAT — the central lens (the one gold moment)**
- Block with `background: --vf-gold-light` and a `--vf-gold` accent (left border 3px OR top+bottom 2px rules — site uses the filled-block treatment).
- Definition: system-sans ~15–19px, `--vf-ink`; the term "Value added time" in `--vf-gold-dark`, weight 600.
- Note line beneath in mono ~11–12px, `--vf-ink-muted`.

**5.4 Five domains grid**
- `display:grid; grid-template-columns: repeat(5,1fr); gap:12px` (collapse to 2-up under ~720px).
- Each chip: `--vf-surface-raised`, 1px `--vf-rule` border, 2px `--vf-teal` top border, radius `0 0 4px 4px`, centered. Mono `D0n` ID in `--vf-teal`; domain name system-sans ~13px `--vf-ink`.

**5.5 Evidence-status table**
- Full-width table, 2px `--vf-ink` top border. Columns: Status (pill) · What it means (sans label + muted meaning) · Typical basis (mono, right-aligned). Rows separated by 1px `--vf-rule`.

**5.6 Finding-status table**
- Same table style. Columns: Marker (NEW/CONFIRMED/UPDATED/DISCARDED pill) · What it means.

**5.7 Signal card — four fields**
- `display:grid; grid-template-columns: repeat(2,1fr); gap:12px` (1-up on mobile).
- Each card: `--vf-surface-raised`, 1px `--vf-rule`, radius 4px, padding ~16–18px.
  - Field label: mono uppercase ~11px `--vf-teal`.
  - Value: mono ~17px weight 600 `--vf-ink` (e.g. `1 ↑`, `P4`, `PRN02404`, `Absent`).
  - Description: system-sans ~13px `--vf-ink-muted`.
- The four fields, in order: **Pattern fit · New caution · Policy force · Local data.** ("Local data: Absent" is a named gap in the system, not a gap in the publication.)

**5.8 Pattern recognition block**
- Intro prose (system-sans) + a small mono legend (Strengthened = teal dot; Confirmed = ink dot).
- Pattern card: `--vf-surface-raised`, 1px `--vf-rule`, radius 4px. Header row (`--vf-surface` bg): mono number · Georgia ~18px title · mono status (`↑ Strengthened`, `→ Confirmed`). Body: system-sans ~14px `--vf-ink-muted`.

**5.9 Footer**
- 1px `--vf-rule` top border; mono ~12px `--vf-ink-muted`; leads with the inline evidence-label vocabulary (§3).

**Per-edition, only three things change:** the edition/partnership stamp (5.1), the worked Signal-card example (5.7), and the leading Pattern example (5.8). Everything else is stable.

---

## 6. House rules (carry across all components)

- **Section opener pattern everywhere:** mono eyebrow → 2px ink rule → Georgia headline → standfirst. Sub-sections: muted mono eyebrow → 1px hairline.
- **Gold discipline:** one gold *feature* moment per view (the VAT lens). Gold also legitimately marks "Provisional"/"Updated" status as semantic caution — that is allowed; decorative gold is not.
- **The hairline is the system.** Prefer 1–2px rules over shadows and heavy borders. Radius is restrained (4px default; pill only for chips).
- **No stock photography, no NHS blue, no performative gradients.** Warmth lives in the paper surface and the serif voice; discipline lives in the mono data layer.
