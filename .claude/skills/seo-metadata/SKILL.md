---
name: seo-metadata
description: >-
  Make The Value Forge discoverable and citable — page metadata, Open Graph /
  social cards, canonical URLs, JSON-LD structured data (Article, Organization,
  WebSite), robots/sitemap hygiene, and AI-search visibility. Use when working
  on head.html metadata, sharing previews, structured data, search indexing, or
  pre-alpha discoverability. Does NOT own visual design (ui-design) or copy
  (article-writing).
---

# SEO & metadata — discoverability for an evidence publication

The site currently ships `<title>`, `description`, favicon and breadcrumb microdata —
and nothing else: **no Open Graph, no Twitter card, no canonical, no JSON-LD.** For a
publication whose value is being *cited* (by commissioners, clinicians, policy people,
and increasingly by AI search), that's the largest unbuilt asset. Distilled from Addy
Osmani's `web-quality-skills` `seo` skill (MIT) with JSON-LD validation practice from
InfluxData's production Hugo skill; rebuilt for this site.

**House constraints come first.** Metadata is site copy: the **decoupling rule** applies
(no local NHS organisation or place names in any title, description, OG text, or
structured data — the one authored-lane exception never extends to metadata), and no
description may make a clinical claim the page's verified sources don't support.

## The metadata partial (spec — freeze-gated implementation)

One new partial, `layouts/partials/head-meta.html`, included from `head.html`. It
touches `layouts/` → **builds** → do not ship until the editor lifts the Netlify freeze.

Per page, emit:

```html
<link rel="canonical" href="{{ .Permalink }}">
<meta property="og:site_name" content="The Value Forge">
<meta property="og:type" content="{{ if .IsPage }}article{{ else }}website{{ end }}">
<meta property="og:title" content="{{ .Title }}">
<meta property="og:description" content="{{ with .Description }}{{ . }}{{ else }}{{ .Site.Params.description }}{{ end }}">
<meta property="og:url" content="{{ .Permalink }}">
{{ with $ogImage }}<meta property="og:image" content="{{ .Permalink }}">{{ end }}
<meta name="twitter:card" content="{{ if $ogImage }}summary_large_image{{ else }}summary{{ end }}">
{{ if .IsPage }}<meta property="article:published_time" content="{{ .Date.Format "2006-01-02" }}">
{{ with .Lastmod }}<meta property="article:modified_time" content="{{ .Format "2006-01-02" }}">{{ end }}{{ end }}
```

`$ogImage`: resolve through the same three-tier chain as card art (frontmatter →
`card_art.json` → none). A generative-SVG-only page gets the `summary` card, not a
broken image URL. A dedicated 1200×630 default OG image is a Phase-6 nicety.

**Canonical caveat:** `.Permalink` is only correct because the sitemap fix already
builds with `-b $DEPLOY_PRIME_URL`; when the custom domain lands (Phase 6), `baseURL`
changes once and everything follows. Never hand-write absolute URLs.

## JSON-LD (structured data)

Three node types, emitted from the same partial:

- **`Organization`** — site-wide, stable `@id` (`{{ .Site.BaseURL }}#org`): name
  "The Value Forge", `url`, `logo`. Feeds entity resolution/knowledge graphs. Exactly
  one per page.
- **`WebSite`** — home page only: name, `url`.
- **`Article`** — every content page (signal / synthesis / monthly / editorial /
  perspectives / domain assessment): `headline` (≤ 110 chars), `description`,
  `datePublished`, `dateModified`, `publisher` → the Organization `@id`, `license`:
  `"https://creativecommons.org/licenses/by/4.0/"`. `author`: the Organization —
  **except** the authored lane, where Perspectives' named `author` frontmatter maps to
  a `Person` node (the one place bylines are correct) and Editorial maps to the
  editor's byline as signed.

The pipeline's frontmatter already carries everything needed (`title`, `date`,
`description`, taxonomies) — the translator does not need to change.

### Validation — use the right tool

**Validate at `validator.schema.org`, NOT Google's Rich Results Test.** The Rich
Results Test only reports types eligible for a visual search enhancement; `Article`
variants often are, but `Organization`/`WebSite` **never** are — it reports "no items
detected" for perfectly valid markup, a false negative that looks like failure.
Local structural check (freeze-safe, run after `hugo --minify`):

```bash
python3 - <<'EOF'
import re, json
html = open('public/index.html', encoding='utf-8', errors='replace').read()
for b in re.findall(r'<script type=["\']?application/ld\+json["\']?>(.*?)</script>', html, re.S):
    j = json.loads(b)  # raises on malformed JSON
    print('OK', j.get('@type'))
EOF
```

## On-page rules (apply during any content/template work — no build needed to *check*)

- **Titles:** unique per page, ~50–60 chars, keyword-bearing noun phrase first, site
  name last (the existing `{{ .Title }} — {{ .Site.Title }}` pattern is right).
- **Descriptions:** 150–160 chars, unique, factual — written to the same standard as
  site copy (no claims beyond the page's sources; the pattern-register phrasing rules
  apply). The pipeline's `description` frontmatter feeds this; spot-check translator
  output.
- **Headings:** one `<h1>` per page, no skipped levels — template-owned; verify when
  editing layouts.
- **Link text:** descriptive anchors, never "click here" / "read more" alone (also an
  accessibility rule — same fix serves both).
- **URL shape:** Hugo's section/slug URLs are already right (lowercase, hyphens,
  stable). Never rename published slugs without a redirect in `netlify.toml`.

## Robots, sitemap, indexing

- Hugo generates `sitemap.xml`; keep it canonical-only. Submit to Search Console at
  alpha (the editor action, needs the domain).
- **Pre-alpha:** the spike-repo Netlify URL should not be indexed — a
  `X-Robots-Tag: noindex` header in `netlify.toml` (or robots meta) until the real
  domain launches, then removed. Add this to the Phase-6 cutover list so launch flips
  it off deliberately.
- **AI crawlers:** do not blanket-block (`OAI-SearchBot`, `PerplexityBot`, `ClaudeBot`
  etc. each read `robots.txt` separately; a Disallow removes TVF from that engine's
  citations — the opposite of the publication's purpose). Structured data above is the
  main lever; the second is already house style: first paragraphs that state the
  finding plainly are exactly what AI answers extract.
- **`llms.txt`:** speculative, unproven adoption — skip; revisit at Phase 6.

## Validation checklist

- [ ] Decoupling holds in every title/description/OG field/JSON-LD node.
- [ ] Descriptions make no claim the page's `sources:` don't support.
- [ ] One `<h1>`; heading levels unskipped; canonical present and absolute.
- [ ] JSON-LD parses locally (script above); exactly one Organization node per page.
- [ ] Perspectives `Person` author nodes only where a named byline exists.
- [ ] Implementation PR is draft + freeze-gated; noindex stays on until domain launch.
