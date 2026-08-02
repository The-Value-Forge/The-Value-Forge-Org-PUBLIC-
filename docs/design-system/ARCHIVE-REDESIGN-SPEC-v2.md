# Archive redesign — spec v2 (the archive as an exhibition)

Status: DRAFT for the editor's review. Supersedes v1 — which is not discarded: v1's bounded, faceted, time-grouped **catalogue** becomes the "behind the curtain" layer of this two-tier model. Author: Claude Code, 19 Jun 2026.
Grounded in a scoped review of museum/gallery collection UX (sources at end).

## The model: two tiers (what every good gallery does)

Galleries never open with the database. They run **two layers**, and the move between them is deliberate:

- **Front of house — the exhibition layer.** Curated, image-led, finite, *alive*: highlights/featured, the current "exhibition", themed entry tiles, curatorial stories. A quiet link leads to →
- **Behind it — the catalogue.** The deep, faceted, searchable record of everything, paginated (spec v1).

This is universal across Tate, the Met, MoMA, Rijksmuseum, V&A, and — the two **size-matched** exemplars for a small editorial team — **Wellcome Collection** (health + humanities; "Stories / Collections / Exhibitions" over a faceted catalogue) and the **Public Domain Review** (curated *Collections* + *Essays*, just three facets: medium · time · theme). We copy Wellcome/PDR, **not** the Met (we are a fixed-taxonomy editorial publication, not a million-record institution).

## The lucky fit — our nouns already map onto the gallery model

| Gallery relationship (proven) | The Value Forge equivalent |
|---|---|
| **Collections / departments** — standing, structural (Met's 17 departments; "V&A Collection" facet) | **The five clinical domains (D01–D05)** — five permanent galleries, each with its own landing (like a Met collection-area page) and its "moment in time" assessment |
| **Exhibitions** — time-bound, curated, **archived not deleted** (MoMA keeps every show since 1929, cross-linked) | **The Quarterly editions** — each quarter is an exhibition; past editions stay browsable by date, cross-linked to the signals/patterns they drew on. This *is* the "moment in time" versioning already planned. |
| **Stories / themes** — narrative threading otherwise-unrelated items into an argument (Met Heilbrunn essays; Wellcome Stories) | **The VF-Patterns** (cross-domain threads) + **Syntheses** + the Quarterly editorial — the intersections the publication exists to surface |
| **Facets / provenance** (maker, date, medium, place…) | **domain · date/quarter · pattern(theme) · type (signal/synthesis/quarterly) · evidence_label · finding_status** |
| **Highlights / masterpieces** (fixed anchors) | **Featured** synthesis + highest-salience pattern + current Quarter |

We already own the curatorial furniture; it just needs arranging as an exhibition. The research also **validates our existing taxonomy**: keep facets to roughly PDR's three — **domain · period · pattern/theme** — plus **type** and **status** toggles. Don't build maker/material/place facets we don't need.

## The exhibition front (the Tate "funnel", adapted)

Proposed `/archive/` becomes the exhibition front, structured top-to-bottom:

1. **The current exhibition (hero)** — the live Quarter (or a featured "moment in time" assessment), with real curatorial framing. Rotates quarterly.
2. **Highlights** — featured synthesis + the highest-salience VF-Pattern (fixed anchors so first-time visitors land somewhere considered).
3. **The five domain galleries** — five entry tiles → each domain page + assessment (the standing collections).
4. **Pattern threads** — VF-Patterns as cross-cutting themed collections (the USP made browsable).
5. **Recent acquisitions** — a short "latest this quarter" strip so it feels current.
6. **"Explore the full archive →"** — one quiet, deliberate door into the catalogue.
7. Cross-link the **Evidence Timeline** as the spatial/chronological alternative to a list (the Met "Heilbrunn" trick — we already have it).

**Never lead with the raw list.** The five techniques that keep an ever-growing archive from feeling endless — highlights, themed doors, rotation, stories, timeline — are designed in from day one, even while the archive is small, because they're what scales.

## The catalogue behind (spec v1, intact)

`/archive/browse/` (or equivalent): faceted search + compact time-grouped rows (Year → Quarter) + pagination, facets via **Pagefind metadata** (`type`, `domain`, `evidence_label`, `finding_status`). Search is prominent *here* — this is the "find" surface. Everything ever published is reachable here even though the front shows only the curated subset.

## Architecture (the Wellcome lesson)

Treat **editorial content** (signals / syntheses / quarterly narrative — Hugo `content/`) and the **structured catalogue** (`data/patterns.json` + frontmatter records) as conceptually separate, joined at one browse/search surface. We already have this split — it's the right one.

## Accessibility (WCAG 2.1 AA — the institutional baseline)

The front is image-led (card art), so: descriptive **alt text per card** generated from frontmatter (domain + finding, never "image"); **lazy-load that preserves the alt attribute** through deferred load; keyboard-operable card reader; and a **list-view fallback** to the image grid (V&A pattern). No text baked into images.

## Build phases

- **Phase 1 — the catalogue (bounds the problem; from v1).** Compact rows + Hugo pagination at `/archive/browse/`. Immediately ends the endless scroll. *Acceptance: rows, paginated, clean build.*
- **Phase 2 — the exhibition front.** Rebuild `/archive/` as the curated funnel (hero + highlights + 5 domain tiles + latest + "explore" link + timeline cross-link). *Acceptance: finite, curated, image-led, AA-accessible; no raw list above the fold.*
- **Phase 3 — threads + facets.** VF-Patterns as themed collections; Pagefind facets (domain/type/theme) on the catalogue. *Acceptance: filter by domain/type/theme against the live index; degrades without JS.*
- **Phase 4 — Quarterly-as-exhibition archive.** Past Quarterly editions browsable by date, cross-linked to their signals/patterns (MoMA model); ties into the assessment "moment in time" versioning.

## Decisions for the editor

1. **`/archive/` becomes the exhibition front**, with the catalogue at `/archive/browse/`? *(Recommended — reuses the front-of-house URL.)*
2. **Curation effort per quarter** — mostly **auto-generated** highlights (current quarter + top pattern + latest) with a light quarterly editorial touch (choose the hero exhibition + foregrounded pattern)? *(Recommended — PDR-scale, sustainable for a small team.)*
3. Confirm the **facet set**: domain · period · pattern/theme · type · status. *(Recommended as-is — matches existing taxonomies.)*
4. Build order: catalogue first (Phase 1, bounds the problem) then the exhibition front (Phase 2)? *(Recommended.)*

## Out of scope

Pipeline/frontmatter changes; redesigning the Feed/card gallery (it remains the immersive *browse* surface); the domain-assessment pages (done). This spec covers the archive surfaces only.

## Sources (scoped review, 19 Jun 2026)

Tate (`/art`, Art by theme, Archive collections); The Met (Collection faceted search; departments; Heilbrunn Timeline; Stories); MoMA (collection search; exhibition history archive since 1929); Rijksmuseum (Rijksstudio theme pages + masterpieces); V&A (Explore the Collections — search-first + facets; list/image views); **Wellcome Collection** (Stories/Collections/Exhibitions + faceted catalogue; CMS-vs-catalogue split); **Public Domain Review** (curated Collections + Essays; 3 facets); Europeana & Google Arts & Culture (Themes/Stories-first fronts). Accessibility: AAM, Cogapp, Cuberis museum-web AA guidance.
