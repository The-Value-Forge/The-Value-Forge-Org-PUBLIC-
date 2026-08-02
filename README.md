# The Value Forge

**An independent clinical intelligence publication.** The Value Forge synthesises evidence from NHS practice, policy, and international health systems to define what good looks like — and to make the gap visible.

The editorial filter is **value-added time (VAT)**: of all the time a patient spends in contact with NHS services, how much of it genuinely adds value to their health, function, or experience? Evidence that narrows this gap is the signal. Everything else is noise.

## Five domains, one question

The publication covers five clinical domains — not as separate bulletins, but as five lenses on the same question: where does NHS practice stand against world best practice?

| | |
|---|---|
| D01 | Acute Frailty |
| D02 | Clinical Psychology |
| D03 | Palliative Care |
| D04 | Therapies & AHPs |
| D05 | OPAT |

The most consequential intelligence emerges at the intersections between domains, not within any single one. A weekly synthesis draws these threads together. Confirmed cross-domain findings are registered as VF-Patterns — the longitudinal record of what the evidence is collectively establishing.

## What the site publishes

- **Signals** — individual evidence items with national significance, labelled by evidence type and finding status
- **Syntheses** — weekly cross-domain synthesis: where the evidence lines up and where it diverges
- **Pattern register** — confirmed, provisional, or discarded cross-domain patterns with their evidence trail
- **Evidence timeline** — an interactive view of how the evidence base has developed across all five domains
- **Monthly review** — the flagship deep cross-domain analysis, published each month and substantially fuller than the weekly synthesis

## How content arrives

Content is produced by an automated weekly pipeline. A translator routine synthesises internal evidence outputs and writes public-register markdown to a dedicated Drive folder. A scheduled GitHub Action (`drive-sync.yml`, daily 07:00 UTC) syncs new files into the Hugo content tree; Netlify rebuilds on commit. The translation rules — style charter, schema, and citation requirements — are in `docs/translation/`.

The pipeline enforces a static copy rule: no clinical or factual claim is published without a verified source. Phrasing must match the source's design, population, and effect exactly.

## Build

```
npm install
hugo --minify
npx pagefind --site public
```

Hugo v0.147.0. Search is [Pagefind](https://pagefind.app/), indexing the built `public/` directory.

## Repository layout

```
content/         signal, synthesis, patterns, monthly, domain pages, method, archive
layouts/         Hugo templates and partials
assets/css/      tvf-tokens.css (design tokens) + main.css
assets/js/       timeline.js — interactive evidence timeline at /patterns/timeline/
data/            patterns.json — the VF-Pattern register, updated by the pipeline
scripts/         drive_sync.py — Drive → repo sync used by the Action
docs/            design system reference, translation charter and routine reference copies
```

Workflow secrets required: `GDRIVE_SERVICE_ACCOUNT_KEY`, `GDRIVE_FOLDER_ID`.

## Development workflow

Work happens on session branches PR'd into `main`; `main` is production. Build phases and open tasks are in `TODO.md`.

## Licence

Content published under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No NHS branding. No local organisation branding.
