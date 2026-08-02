# Archive redesign — spec v1

Status: DRAFT for the editor's review. Not yet built. Author: Claude Code, 19 Jun 2026.
Related: `layouts/archive/list.html` (current), `CARD-GALLERY-SPEC-v1.md`, `TVF-DESIGN-SYSTEM-reference-v1.md`, Evidence Timeline (`/patterns/timeline/`).

## Problem

The archive currently aggregates every `signal` + `synthesis` + `quarterly` page into one flat, newest-first list. The pipeline adds ~3–5 signals + 1 synthesis **every week**, plus monthly/quarterly items. Within months this is an unbounded scroll, and the card layout (great for *browsing*) is the wrong unit for an *archive* (finding). The archive needs to feel like an intelligence index you navigate, not a feed you fall down.

## Principles

1. **Separate the jobs of the surfaces.** The card gallery / **Feed** is the immersive *browse* surface (cards, reader). The **Archive** is the precise *find* surface (rows + filters + search + time structure). The **Evidence Timeline** is the visual *over-time* surface. Cross-link the three; don't duplicate them.
2. **Bounded by default.** No view should grow without limit. The page shows the present and lets you drill into the past.
3. **Structured by the publication's own cadence** — Year → Quarter — so the archive reads as chapters, consistent with the Quarterly and with the domain assessments' "moment in time" model.
4. **Reuse what exists** — the `domain`, `evidence_label`, `finding_status` taxonomies and the Pagefind index already in the build. No bespoke search/filter engine.
5. **Design-system compliant & decoupled** — `--vf-*` tokens only; mono for dates/labels/counts; hairlines; gold stays VAT-only; rows not cards; no local identifiers.

## Layout

```
┌─ Archive ────────────────────────────────────────────────┐
│  [ search box (Pagefind) ]                                │
│  Filter:  [Signals] [Syntheses] [Quarterly]   ·  domains  │
│           [D01][D02][D03][D04][D05]  ·  [evidence label ▾]│
│                                                           │
│  2026 · Q2  (14)                                [latest]  │
│   19 Jun · ⟨Signal⟩  D01  Corridor care: first national…  │
│   18 Jun · ⟨Synthesis⟩ D03  Earlier specialist input…     │
│   …                                                       │
│  2026 · Q1  (22)                              [collapsed] │
│  2025 · Q4  (19)                              [collapsed] │
│                                            [ older ▾ ]    │
└───────────────────────────────────────────────────────────┘
```

**Row anatomy (one line, scannable):** `date (mono) · type badge · domain chip(s) · title (link)`. Optional trailing `evidence_label` pill where present. No description, no art — that's the gallery's job.

**Time grouping:** group by Year, then Quarter (Hugo `.GroupByDate`). The most recent quarter is expanded; older quarters are collapsed `<details>` with an entry count. A final "older" affordance for anything beyond the last N quarters.

**Pagination backstop:** even within "expanded", cap with Hugo `.Paginate` (~24 rows/page) so a heavy quarter can't blow the page.

## Faceted filtering (Pagefind metadata)

Pagefind supports filtering by page metadata. Tag each indexed page with `data-pagefind-filter` attributes for `type` (signal/synthesis/quarterly), `domain` (d01–d05), `evidence_label`, `finding_status`. The archive's search/filter UI then offers facets **for free**, reusing the existing index — no custom JS filter engine. Search is prominent: the archive is where you go to *find* a specific piece.

## Phasing

- **Phase 1 — bound the page (small, safe).** Convert the archive to compact rows + Hugo pagination. Immediately removes the endless-scroll problem. No new data model. *Acceptance: archive renders rows, paginated; builds clean; Lighthouse unaffected; no card art on archive.*
- **Phase 2 — time structure.** Group rows Year → Quarter, latest expanded, older collapsed with counts. *Acceptance: entries grouped correctly; current quarter open; counts accurate; keyboard-accessible disclosures.*
- **Phase 3 — Pagefind facets.** Add `data-pagefind-filter` metadata + filter chips + prominent search. *Acceptance: filtering by type/domain/label works against the live index; degrades to the grouped list with JS off.*

## Implementation notes (Hugo)

- Rows + pagination: `{{ $pages := where .Site.RegularPages "Section" "in" (slice "signal" "synthesis" "quarterly") }}` → `.Paginate $pages.ByDate.Reverse`.
- Grouping: `.GroupByDate "2006"` (year) then a quarter key (derive from `.Date.Month`). Render nested `<details>`.
- Facets: add `data-pagefind-filter="type:Signal"` etc. on indexed elements; configure the Pagefind UI with filters. (Pagefind re-indexes at build via the existing `npx pagefind` step.)
- Templates: `layouts/archive/list.html` (rebuild), new partial `layouts/partials/archive-row.html`, CSS block `.archive-*` in `main.css`.
- Apply the same row/pagination/grouping pattern later to `/signal/` and `/feed/` list views, which face the same growth.

## Decisions for the editor

1. **Group by Quarter or Month?** (Quarter recommended — matches the Quarterly cadence and keeps the index shallow.)
2. **Default window** — show current year expanded and collapse prior years, or only the current quarter? (Current quarter expanded recommended.)
3. **Keep a card/grid toggle on the archive**, or rows only? (Rows-only recommended — the gallery already serves browsing.)
4. **Per-page size** for pagination (24 suggested).

## Out of scope (this spec)

Changing the pipeline or frontmatter; redesigning the Feed/gallery; the domain-assessment pages (separate, done). This spec is the archive *index* surface only.
