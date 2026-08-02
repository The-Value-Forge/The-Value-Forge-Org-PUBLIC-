# Domain assessment — "moment in time" versioning

Each of the five domain pages (`content/domain/dNN/_index.md`) carries a **Domain Assessment**: a dated, source-verified statement of "what good looks like", rendered in a collapsible pull-down above the domain's article feed (`layouts/domain/list.html`). The articles remain the page's main feature; the assessment is the standing analytical backdrop.

This note defines how the assessment is **versioned and archived**, so that as the evidence moves the publication keeps a genuine record *in time* rather than silently overwriting its own thinking.

## Frontmatter schema

```yaml
assessment:
  version: 1                 # integer; bump on each material re-assessment
  assessed: "2026-06-18"     # date this version was assessed
  next_review: "2026-09"     # cadence: quarterly by default
  prior_versions:            # omit or [] until there is a superseded version
    - version: 1
      assessed: "2026-06-18"
      note: "First assessment."            # one line: what it said / what changed
      url: "/domain-history/d01-2026-06-18.html"   # optional: link to the archived snapshot
```

The pull-down footer (`.assessment-history`) renders the current version + review date, and — once `prior_versions` is populated — a "Previous assessments" list linking each archived snapshot. While `prior_versions` is empty it shows "This is the first assessment…", which is the current state for all five (all v1, 18 Jun 2026).

## Re-assessment workflow (when an assessment materially changes)

1. **Snapshot the outgoing version first.** Save a self-contained copy of the *current* rendered assessment to `static/domain-history/<domain>-<assessed>.html` (e.g. `static/domain-history/d01-2026-06-18.html`). A static HTML copy is used deliberately — it is a frozen record, not re-rendered, so the past "moment in time" stays exactly as it was published. (No Hugo template depends on it; it is served as-is.)
2. **Record it in `prior_versions`.** Prepend an entry with the outgoing `version`, its `assessed` date, a one-line `note` (what that version concluded / why it changed), and the `url` of the snapshot from step 1.
3. **Bump the current version.** Increment `version`, set a new `assessed` date, roll `next_review` forward.
4. **Rewrite the body** and **re-run the static-copy §8 check** on every clinical claim (verified source; design/population/effect matched; firm standards vs "should"; decoupled — no local identifiers). See the static-copy rule in `CLAUDE.md`.

## Cadence

Default re-assessment is **quarterly** (`next_review`), or out-of-cycle when new evidence materially shifts a domain's "what good looks like" or moves one of the cross-domain patterns. This mirrors the pattern-register history model and the Evidence Timeline: the assessment accrues a visible lineage rather than resetting each time.

## Why static snapshots rather than rendered archive pages

Re-rendering an old assessment through the live templates would let later token/design changes silently alter a record that is supposed to be fixed. A frozen HTML snapshot is the honest representation of what the publication actually said on a given date — which is the whole point of "moment in time".
