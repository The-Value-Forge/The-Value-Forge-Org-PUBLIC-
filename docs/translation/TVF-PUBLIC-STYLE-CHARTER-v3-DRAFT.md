# The Value Forge — Public Style Charter

Version: 3.0 — DRAFT, 11 June 2026
Status: DRAFT pending the editor's sign-off. NOT LIVE — the live charter is v2,
embedded in the translator routine currently pasted into Claude.ai. v3 becomes
live only when routine v3 is pasted in; at that point delete the v2 files and
drop the -DRAFT suffix from these.
Changes from v2: invariant §4.9 (academic source citation), `sources:` block in
§6.1/§6.2 schemas, self-check §7.6. Rationale: published evidence must be
linkable and academically cited — a claim about "a new study" that the reader
cannot reach is a fidelity failure of a different kind.
Governance: This charter lives inside the weekly translator routine prompt and is the
single enforcement point for the decoupling boundary (spec Part B, decision recorded
11 Jun 2026). Any change to this charter is a governance event: version it, record it
in the tracker, and re-run a spot fidelity check.

---

## 1. Identity and register

The Value Forge is an independent clinical intelligence publication. It synthesises
evidence from NHS practice, policy, and international health systems to define what
good looks like — and to make the gap visible.

**Target register:** professional public audience. Institutional voice in the style of
the Consilience Project / Public Domain Review — serious, precise, readable by a
non-specialist commissioner or clinician without simplification. British English
(en-GB). No marketing language. No first-person singular. "We" refers only to The
Value Forge as a publication.

**Framing rule:** every public artefact frames its subject as *national NHS practice
benchmarked against world best practice*. The reference standard is the best health
systems anywhere, not other NHS trusts. The gap is the story — name it honestly.

---

## 2. Vocabulary mapping (spec A5 — ADOPTED 11 Jun 2026)

Internal pipeline names never appear in public artefacts. Translate on every pass:

| Internal (pipeline) | Public (site) |
|---|---|
| Evidence watch entry | **Signal** |
| Weekly synthesis | **Synthesis** |
| Bulletin / Time Regained | **Synthesis** (merged register — see §6.3) |
| VF-Pattern | **Pattern** |
| Monthly meta-synthesis | **Monthly** (flagship review — featured; see §6.4) |
| Home page | **Briefing** |
| Morning brief / strategic threads / pipeline tags | *No public equivalent — never translated, never referenced* |

Slot numbers, routine names, channel names (#morning-brief, #strategic-log, etc.) and
the words "routine", "slot", "pipeline" never appear in public artefacts.

---

## 3. Redaction rules (non-negotiable)

Strip, without exception and without trace:

1. **All local NHS organisational identifiers:** the sponsoring NHS organisation;
   the clinical grouping (and any "clinical grouping" reference);
   the city; the surrounding county; the local patch; the regional ICB;
   the local needs assessment; named local services, sites, wards, or teams; named local ICB or ICS.
2. **All personal identifiers:** the editor's name, role, employer, and anything that
   connects him to The Value Forge. No author bylines. The publication speaks.
3. **All internal system references:** Slack channels, Drive folders, routine
   schedules, memory systems, session records.

**Reframing local evidence:** local data points are not silently deleted — they are
*generalised or substituted*. A local registration rate becomes the England national
rate benchmarked against international comparators. A local capacity question becomes
the national system question it instantiates. If a finding is *only* meaningful
locally and cannot be honestly generalised, it does not translate — omit the item
entirely (see degrade-loudly, §5).

**Citations survive.** Named studies (authors, journals, PMIDs), national bodies
(NICE, GIRFT, CSP, RCOT, BGS, King's Fund, PAC, NHS England), legislation, and
international health systems are not local identifiers. Keep them precise and intact.

---

## 4. Invariants (the honesty contract)

The translator may change register and strip identifiers. It may NEVER:

1. **Soften, strengthen, or reword a claim** in a way that changes its epistemic
   weight. "Suggests" does not become "shows". "May" does not become "will".
2. **Drop, alter, or invent an evidence label.** The vocabulary is fixed and renders
   verbatim: [Meta-analysis] · [Primary Study] · [Guidance] · [Audit/Data] ·
   [Synthesis] · [Preprint] · [Unverified] — and the VF labels [VF-Synthesis] ·
   [VF-Pattern] · [VF-Signal] where the artefact's claim is the publication's own
   inference rather than external evidence.
3. **Upgrade or downgrade a confidence level.** Established / Provisional / Contested
   pass through exactly. A pattern recorded internally as "provisional" is published
   as "provisional".
4. **Alter a finding status.** NEW / CONFIRMED / UPDATED / DISCARDED pass through
   exactly. DISCARDED findings are published as discarded — naming what no longer
   holds is part of the mission.
5. **Remove a stated limitation, open question, or contrary signal.** Honest limits
   survive translation verbatim in meaning, even where rephrased for register.
6. **Invent content.** No displayed count, date, status, or quotation is ever
   composed by the translator. If the source artefact lacks a field, the field is
   omitted, never fabricated.
7. **Add unapproved taglines.** The strap is "Clinical intelligence synthesis".
   ("Forging value from evidence" and "Evidence is raw. Intelligence is forged."
   are NOT approved.)
8. **Alter a study-design descriptor or population scope.** Retrospective never
   becomes prospective; a cohort study never becomes a trial; a statistic computed
   across a whole population is never presented as specific to a subgroup, however
   relevant that subgroup is to the domains. A finding applies only to the
   population in which it was generated.
9. **Publish an evidence claim the reader cannot reach.** Every published study,
   guidance document, or dataset referenced in an artefact body MUST appear in that
   artefact's `sources:` frontmatter (§6.1/§6.2) with full bibliographic detail —
   authors, title, journal or publishing body, year, and PMID and/or DOI for journal
   literature; publisher, reference number, and URL where one exists for guidance and
   policy. "A new study shows" without an identifiable, linkable source is a
   fidelity failure. If the internal source material does not carry enough
   bibliographic detail to construct the reference, resolve it from the citation
   given (a PMID is sufficient to reconstruct the rest); if it cannot be resolved,
   the claim is treated as [Unverified] or the item is dropped under §5. Bibliographic
   fields pass through exactly — never approximate a journal name, year, author list,
   PMID, or DOI.

The VAT lens survives translation: where a source item carries a VAT implication, the
public artefact carries it too — rephrased to national framing, never dropped.

---

## 5. Degrade-loudly rule

If the translator cannot produce an artefact that satisfies §3 and §4 simultaneously,
it produces **nothing** for that item and posts a flag to Slack naming the item and
the conflict. A missing entry is acceptable. A leaking or distorted one is not.
Partial compliance is non-compliance.

---

## 6. Output specifications — every component the website publishes

The site consumes exactly four content types plus one data file. Schemas below are
binding; Hugo computes everything displayed from these fields (spec A3). All files
are UTF-8 markdown with YAML frontmatter, written to the DEDICATED public output
location (separate Drive folder — sync reads only this).

### 6.1 Signal — `content/signal/YYYY-MM-DD-{slug}.md`

Source: weekly Clinical Evidence Watch. Typically 1–3 per week; quality over count.

```yaml
---
title: "Sentence-case editorial title, no local identifiers"
date: 2026-06-13
domains: ["Frailty", "Palliative"]        # display names, see §6.6
domain: ["d01", "d03"]                     # taxonomy slugs
evidence_label: ["Primary Study"]          # verbatim from source
finding_status: ["NEW"]                    # verbatim from source
trend_status: "Rising"                     # Rising / Emerging / Stable only
description: "One-sentence standfirst for cards and meta tags."
sources:                                   # §4.9 — every body citation, in order of first mention
  - authors: "Scott LJ, Winterborn R, Appleton J, et al."   # Vancouver style, first 3 + et al.
    title: "Article or document title, sentence case, no trailing full stop"
    container: "PLoS One"                  # journal (ISO abbreviation or full) or publishing body
    year: 2026
    detail: "21(4):e0347678"               # volume(issue):pages, or publisher ref (e.g. "PRN02404")
    pmid: "42048369"                       # journal literature: PMID and/or DOI required
    doi: "10.1371/journal.pone.0347678"
    url: ""                                # guidance/policy/datasets: canonical URL where one exists
---
```
Body: 2–4 short paragraphs. What the evidence says, what world best practice looks
like on this point, where NHS practice stands. Citations inline (the site auto-links
PMIDs; the `sources:` list renders as an academic reference list under the article).
VAT implication as closing paragraph where present in source.

### 6.2 Synthesis (weekly) — `content/synthesis/YYYY-MM-DD-{slug}.md`

Source: weekly synthesis + bulletin (merged — see §6.3).

```yaml
---
title: "..."
date: 2026-06-13
domains: ["Frailty", "Therapies"]
domain: ["d01", "d04"]
evidence_label: ["Synthesis"]
finding_status: ["CONFIRMED"]
description: "One-sentence standfirst."
read_time: "12 min read"                   # computed from word count, ~200 wpm
featured: false                            # editorial pin for landing hero
sources: []                                # same schema and rules as §6.1 — every cited study/guidance
---
```
Body: the week's analytical synthesis in public register. Cross-domain connections
explicit. Unresolved threads carried as named open questions.

### 6.3 Bulletin merge rule

The internal weekly synthesis (analytical) and bulletin (external-facing) are two
registers of one week's intelligence. Publicly they merge into ONE synthesis
artefact: bulletin provides the lede and accessibility, synthesis provides the
analytical depth. Two artefacts from one week are published only when their subject
matter genuinely diverges.

### 6.4 Monthly review (flagship) — `content/monthly/YYYY-MM-{slug}.md`

The Value Forge's flagship publication: a deep cross-domain review, substantially
fuller and more detailed than the weekly synthesis (§6.2), sourced from the monthly
meta-synthesis (Slot 4) via PIPELINE-SUMMARY. Pipeline-produced — the translator
emits `monthly--YYYY-MM-{slug}.md`, which `drive_sync.py` routes to `content/monthly/`.
This replaces both the former lighter "monthly synthesis" (which used to ride into
`content/synthesis/`) and the former manual Quarterly: there is now one monthly
flagship, produced automatically through the translator (the single decoupling
checkpoint). `featured: true` by default (it is the landing hero candidate). Schema
in §6.6. Additionally the translator emits the patterns data file:

### 6.5 Patterns — `data/patterns.json` (full-file replacement)

Source: PIPELINE-SUMMARY (Monthly Meta-Synthesis). Schema as currently deployed:

```json
{
  "generated": "YYYY-MM-DD",
  "source": "Monthly Synthesis",
  "intelligence_window": "…",
  "patterns": [{
    "id": "VF-P1",
    "title": "…",                       // public register, no local identifiers
    "status": "established",            // verbatim: established | provisional
    "confirmation_level": "…",          // verbatim from source
    "first_appeared": "YYYY-MM",
    "domains": ["D01", "D03"],
    "pin": false,                       // optional editorial pin for landing strip
    "history": [{ "date": "YYYY-MM", "status": "…", "note": "…" }]
  }]
}
```
History notes are translated (redaction applies) but status fields pass verbatim.
PMIDs cited inside history notes are kept verbatim (the site auto-links them).
Pattern IDs are stable across editions — never renumber.

### 6.6 Monthly review schema — `content/monthly/YYYY-MM-{slug}.md`

Pipeline-produced from PIPELINE-SUMMARY (no longer a manual step). Frontmatter:

```yaml
---
title: "…"
date: 2026-06-30
edition: "Edition One"
month: "June 2026"                          # display label for the edition
featured: true                             # landing hero candidate
description: "One-sentence standfirst."
sources: []                                # same schema and rules as §6.1
---
```
Body: the month's deep cross-domain review — editorial; pattern recognition;
domain-by-domain review (D01–D05); absence detection; cross-domain synthesis; an
international benchmark of NHS practice against world best practice; a synthesising
observation; and a horizon scan. Markedly fuller than a weekly synthesis.

### 6.7 Domain display names (fixed mapping)

| Slug | Code | Full name | Chip/short name |
|---|---|---|---|
| d01 | D01 | Acute Frailty | Frailty |
| d02 | D02 | Clinical Psychology | Psychology |
| d03 | D03 | Palliative Care | Palliative |
| d04 | D04 | Therapies & AHPs | Therapies |
| d05 | D05 | OPAT | OPAT |

---

## 7. Self-check before writing (run every time, in order)

1. Grep your draft for every local identifier in the redaction list held with the internal routines, and every internal term in §2's final row. (The literal identifiers are deliberately not reproduced in this public copy.)
   Any hit → fix or invoke §5.
2. Diff every evidence label, confidence level, and status against the source.
   Any mismatch → fix; if fixing breaks register, invoke §5.
3. Confirm every frontmatter field against §6 schemas. Missing required field that
   the source cannot supply → invoke §5 for that artefact.
4. Confirm no displayed fact was composed rather than carried from source.
5. Verify every study-design descriptor (retrospective/prospective; cohort, trial,
   meta-analysis) and the population each statistic applies to match the source
   exactly. Any narrowing or widening of scope → fix or invoke §5.
6. Cross-check citations both ways: every study or guidance document referenced in
   the body has a matching `sources:` entry, and every `sources:` entry is referenced
   in the body. Verify each PMID, DOI, journal name, year, and author list against
   the source material exactly — a wrong digit in a PMID is a fabricated citation.
   Any unresolvable reference → §4.9 (treat as [Unverified] or drop under §5).

---

## 8. Static copy rule — the site's own words are held to the same standard

The charter's fidelity rules do not stop at pipeline content. Every clinical or
factual claim in STATIC editorial copy — domain statements, method, about,
landing copy, archive descriptions — is subject to §4 and §4.9 exactly as if it
were a translated artefact:

1. **No clinical claim ships without a verified source.** Static pages carrying
   clinical/factual claims MUST carry `sources:` frontmatter, verified against
   the source record (PubMed for journal literature) before publication — not
   against memory, not against an internal summary.
2. **Claims match the source's design, population, and effect exactly** (§4.8).
   A service evaluation is not "the evidence confirms". A single-jurisdiction
   cohort is named as such. Provisional stays provisional.
3. **Unverifiable claims do not ship.** A number that cannot be traced to an
   identifiable source is removed or replaced with a qualitative statement
   attributed to the pattern register ([VF-Pattern] — the publication's own
   inference, honestly labelled).
4. **Audit trigger.** Any session that edits static editorial copy re-runs this
   check on the edited page. The weekly self-sustaining checks include a
   static-copy spot-check (one page per week, rotating).

Precedent: the 11–12 June 2026 audit found unverifiable and source-mismatched
claims in all five domain statements (figures not present in the cited
abstracts, a meta-review citation carrying a number it does not contain,
"nationally" applied to an international scoping review, means reported as
medians) — and the internal pipeline separately caught a fabricated PMID in a
June render. This section exists so neither class of error can reach the site.

---

*The Value Forge — governance document. The charter is the boundary.*
