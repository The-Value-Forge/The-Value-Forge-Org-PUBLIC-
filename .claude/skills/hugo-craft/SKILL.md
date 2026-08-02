---
name: hugo-craft
description: >-
  Hugo templating and build craft for The Value Forge — runtime-validated
  template changes, nil-safe data access, and the repo's load-bearing patterns
  (as-slice scalar hardening, section-name collisions, buildFuture, the asset
  pipeline, pipeline-owned files). Use when creating or editing Hugo layouts,
  partials, shortcodes, or archetypes, debugging template errors, touching
  hugo.toml, or reading .Site.Data / frontmatter in templates. Visual decisions
  belong to ui-design; this skill owns template correctness.
---

# Hugo craft — template correctness & institutional memory

Two jobs: (1) a testing discipline that catches the errors `hugo` alone misses, and
(2) the codified list of this repo's hard-won, non-obvious patterns so no session
re-derives or breaks them. Testing protocol and nil-safety patterns adapted from
InfluxData's production `hugo-template-dev` skill (influxdata/docs-v2); everything
under "Load-bearing TVF patterns" is this repo's own history (PRs #20, #24, #30).

## Rule zero: a clean build is not a working site

**`hugo --minify` validates syntax, not runtime execution.** Nil field access, wrong
type assertions, and missing-data paths surface only when pages render — and some
(like scalar-vs-slice frontmatter) surface only with the *right shaped content*, which
is why the 19-Jun pipeline cycle broke production for two weeks (PR #20).

### Mandatory protocol for any template change

```bash
# 1. Runtime render with error capture
rm -f /tmp/hugo-test.log
hugo server --port 1315 >/tmp/hugo-test.log 2>&1 &
sleep 5
grep -E "error calling partial|can't evaluate field|failed|ERROR" /tmp/hugo-test.log | head -20

# 2. Verify every affected page actually renders
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:1315/PATH/TO/PAGE/   # expect 200

# 3. Stop
pkill -f "hugo server --port 1315"
```

Then the full production build: `hugo --minify && npx pagefind --site public`.
For visual confirmation use the `site-verify` skill (local screenshots — works under
the Netlify freeze when previews don't exist).

**Test with adversarial content shapes.** The pipeline is an external writer: before
shipping a template that reads pipeline frontmatter, render at least one page where the
field is a scalar, one where it's a list, and one where it's absent.

## Nil-safe data access (the error class behind PRs #20/#24)

- **Taxonomy-shaped frontmatter goes through `layouts/partials/as-slice.html`** —
  every `domain` / `domains` / `evidence_label` / `finding_status` read, no raw
  `range` over them ever again. A scalar `domains:` was a production build failure; a
  scalar `domain:` was a JS crash + archive garbage. The partial coerces
  scalar-or-slice; keep all four call sites (and any new one) behind it.
- **Hyphenated or variable keys need `index`:** dot notation only works for Go
  identifiers. `{{ index .Site.Data "my-data" $key }}`, never `.Site.Data.my-data`.
- **Guard each nesting level:** `{{ if $root }}{{ $x := index $root "key" }}{{ if $x }}…`
  — and remember `{{ if . }}` passes for an **empty map**; when it matters, check the
  specific key: `{{ if and $data (isset $data "field") }}`.
- **`with` over `if` for optional scalars:** `{{ with .Params.form_url }}…{{ end }}`
  (the feedback-page placeholder pattern).
- Debug by printing, then remove: `<pre>{{ printf "%#v" $var }}</pre>`.

## Load-bearing TVF patterns — do not re-derive, do not "fix"

- **`layouts/responses/` renders `/feedback/`** — Hugo has a `feed`/`feedback`
  name-prefix collision; `type: "responses"` in `content/feedback/_index.md` redirects
  the lookup. Moving it to `layouts/feedback/` re-breaks it. (PR #19.)
- **`buildFuture = true` in `hugo.toml` is load-bearing** — the Monthly flagship is
  dated to its source month-end but syncs mid-month; without the flag Hugo silently
  hides it until the month turns. Removing it un-publishes the flagship. (PR #30.)
- **`piece_kind`, never `kind`** in Perspectives frontmatter — `kind` is
  Hugo-reserved. (PR #30.)
- **Pipeline-owned files are never hand-edited:** `data/patterns.json`, everything in
  `content/signal/`, `content/synthesis/`, `content/monthly/` arriving via the daily
  sync — edits are overwritten by the next sync. Repo-owned editorial data lives in
  `data/vat_patterns.yaml` (gold gating) and `data/feedback.json`. The authored lane
  (`content/editorial/`, `content/perspectives/`) is repo-owned — the sync never
  touches it.
- **Asset pipeline:** tokens + main CSS are
  `resources.Concat → Minify → Fingerprint` with an `integrity` attribute
  (`head.html`). New CSS joins the bundle — never a separate render-blocking `<link>`.
  `assets/css/tvf-tokens.css` must stay byte-identical to
  `docs/design-system/tvf-tokens.css` (Drive-first dual-home rule).
- **Card art is three-tier:** frontmatter `card_image:` → `data/card_art.json` →
  slug-seeded generative SVG (`layouts/partials/card-art.html`, FNV-32a with
  prefix-salted independent x/y hashes — suffix salts don't decorrelate, that was
  PR #27). The SVG fallback also covers *broken* assignments; a card must never render
  blank.
- **Sitemap/absolute URLs build with `-b $DEPLOY_PRIME_URL`** on Netlify — never
  hand-write absolute URLs in templates; use `.Permalink`/`absURL`.
- **Pagination:** `pagerSize = 24`; list templates paginate via `.Paginate` with the
  shared mono/hairline pager partial (dormant under 24 items). `/feed/` caps at 100 +
  `content-visibility: auto`.
- **Netlify build gate:** `netlify.toml`'s `ignore` rule cancels builds for commits
  touching only `docs/ .claude/ scripts/ .github/` and root `*.md`. Anything touching
  `content/ data/ assets/ layouts/ static/ archetypes/ i18n/ hugo.toml netlify.toml
  package.json` **builds** — under a freeze, stage on a draft PR and hold.

## Templates vs JS — separation of concerns

Hugo templates own structure and data binding; the two small vanilla JS files own
behaviour. Keep it that way:

- Pass template data to JS via `data-*` attributes
  (`data-x="{{ .x | jsonify | safeHTMLAttr }}"`), not inline script variables.
- Inline `<script>` in a layout only for critical no-logic initialisation; behaviour
  lives in `assets/js/`. Everything degrades without JS (the read-state, dropdown, and
  timeline all follow this — new work matches it).
- Prefer build-time Hugo computation and CSS state (`:has()`, `:checked`) over new JS
  entirely; the JS budget in `web-quality` is deliberately tiny.

## Validation checklist

- [ ] Runtime protocol run (server log grep + curl 200 on affected pages), not just
      `hugo --minify`.
- [ ] Pipeline-read frontmatter tested against scalar / list / absent shapes;
      taxonomy reads go through `as-slice`.
- [ ] No hand-edits to pipeline-owned files; no renamed published slugs without a
      `netlify.toml` redirect.
- [ ] Load-bearing patterns above untouched (or the change consciously supersedes one
      and updates this skill + CLAUDE.md in the same PR).
- [ ] Build-triggering paths vs docs-only paths identified; freeze respected.
