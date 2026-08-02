---
name: article-writing
description: >-
  Write polished long-form editorial copy for The Value Forge — signals, syntheses,
  the monthly flagship, domain assessments, About/Method prose — in the publication's
  house voice and under its evidence discipline. Use whenever drafting or restructuring
  reader-facing prose. Enforces the static-copy rule (no clinical claim without a
  verified source), the VAT/use-value lens, decoupling, and the three type registers.
---

# Writing for The Value Forge

Craft long-form clinical-intelligence copy that reads like an editor with a point of
view — not an LLM smoothing itself into paste — while staying inside this publication's
evidence rules. Adapted from ECC's `article-writing` skill, rebuilt for the TVF charter.

Read `CLAUDE.md` (editorial mission + static-copy rule + design system) and, for any
"what good looks like" / exemplar judgement, `docs/PROJECT-intellectual-foundation-v3.md`
before drafting load-bearing copy.

## When to use

- Drafting or revising a signal, synthesis, the monthly flagship, or a domain assessment.
- Writing static site copy (landing, About, Method, archive, reader key).
- Turning verified evidence notes or a pipeline output into finished public prose.
- Restructuring existing copy for flow without weakening its sourcing.

## The two rules you cannot break

1. **Static-copy rule (failsafe).** No clinical or factual claim ships without a verified
   source. Phrasing must match the source's **design, population, and effect exactly**:
   a service evaluation is not "evidence confirms"; a mean is not a median; an
   international scoping review is not "nationally"; a single-centre result is not a
   national one. Unverifiable numbers are removed or restated qualitatively with
   attribution to the pattern register. Claims carry `sources:` frontmatter, verified
   against PubMed / the source record. Re-run this check on every page you edit.
2. **Decoupling.** No local NHS organisation, trust, or place names — ever. The framing is
   always **national NHS practice benchmarked against international best practice**.
   Citations may name studies or national bodies; the lens stays national.

## Voice — what good copy sounds like

- **Begin with concrete evidence**, then explain. Open on the finding, the number, the
  trial design, the gap — not on throat-clearing or a "rapidly evolving landscape".
- **Demonstrate, don't declare.** Show the evidence doing the work rather than asserting
  significance. The reader should reach the judgement with you.
- **A point of view.** The Value Forge has an editorial position (VAT as the prior
  standard); write with it, not as a neutral aggregator.
- **Tight sentences.** Expand only where the argument genuinely needs it.
- **Never invent facts, credibility, or evidence.** If it isn't sourced, it doesn't exist.

### The VAT / use-value lens (the editorial filter)

Assess everything as **use value, in context, measured by lived experience, with VAT as
the prior standard** — never exchange value (institutional fame, activity units,
reputation). Exemplars and "what good looks like" are chosen from **outcome data and
transferability**, never reputation (the Kahneman base-rate discipline; the
Clark/Baxandall/Kleinman/McGilchrist foundation). Choosing a system because it is famous
is exactly the error the foundation forbids.

### The synthesis is the USP

The five domains (D01–D05) are five lenses on one question — *where does NHS practice
stand against world best practice?* The most consequential intelligence lives at the
**intersections**, not within a single domain. Write toward those crossings.

### Scope honesty

State it plainly when relevant: the work closes the **epistemic gap** (evidence not
synthesised) and the **translation gap** (what population-average evidence means for a
specific, deprived population). It does **not** close the incentive or capacity gap —
never imply otherwise.

## Banned phrasing

Strip: "rapidly evolving landscape", "game-changer", "in today's world", generic AI
preamble, biographical padding, and engagement-bait closing questions ("What do *you*
think?"). Strip loose risk language too — e.g. a tool that "classified 46–75% as high
risk vs observed 1.2% incidence" is not a tool that "overestimates risk by 46–75%".

## Type registers (carry into any HTML/markup you touch)

- Body / prose → `--vf-font-body` (system sans)
- Editorial headlines → `--vf-font-head` (Georgia)
- All data, labels, dates, nav, tags → `--vf-font-mono` (IBM Plex Mono)

Gold (`--vf-gold*`) is **VAT-only**. No NHS blue. Don't blur the registers.

## Process

1. **Clarify** audience and the piece's job (signal vs synthesis vs flagship vs static
   copy) — one or two questions only if genuinely unresolved.
2. **Outline** the structure: lead finding → evidence → cross-domain reading → what good
   looks like → honest scope/limits.
3. **Anchor every section in verified proof.** Pull each load-bearing claim back to a
   source; check design/population/effect match before writing the sentence. Verify
   primary papers via the PubMed tool directly — don't trust a second-hand summary.
4. **Draft**, then **expand judiciously** only where the argument needs it.
5. **Cut template language** and re-run the static-copy + decoupling checks.

### Format notes

- **Signal** — one finding, tightly. Lead with the result and its design; state what it
  does and doesn't support; link the pattern(s) it touches.
- **Synthesis** — weekly cross-section; frontload the convergence across findings.
- **Monthly flagship** — the deep dive; materially fuller; the six-thinker analytical
  frame (Schmachtenberger / McGilchrist / Weinstein / Lennox / Holmes / Data-Bayesian)
  applies here explicitly. Pipeline-produced via the translator.
- **Domain assessment** — "moment in time" against NICE/BGS/GIRFT/NHSE + international
  comparators; exemplars on outcome data, not reputation.

## Validation checklist (before done)

- [ ] Every clinical/factual claim has a verified source; phrasing matches design,
      population, and effect exactly.
- [ ] `sources:` frontmatter present and PubMed-verified where applicable.
- [ ] No local NHS org / place names; framing is national vs international.
- [ ] VAT/use-value lens applied; any exemplar chosen on outcome data, not reputation.
- [ ] Scope honesty preserved (no implied incentive/capacity-gap claims).
- [ ] Banned clichés and generic transitions purged; voice has a point of view.
- [ ] Type registers respected; gold stays VAT-only.
