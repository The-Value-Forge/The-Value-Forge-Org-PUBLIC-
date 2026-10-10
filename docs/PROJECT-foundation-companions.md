# Value Forge — Foundation companions (repo-decoupled distillation)

Captured 18 June 2026. Decoupled summaries of two of the three foundation companions.
Canonical originals (Drive): `PROJECT-system-foundation-v2`, `PROJECT-design-rationale-v1`.
Third companion `VALUE-FORGE-GOVERNANCE-v1` (Drive) — **decoupled essentials ingested**, in "Governance (decoupled essentials)" below. The identifying material (the owner's role, named trusts and hospitals) is deliberately omitted and stays omitted. Until 10 Sep 2026 this line still called it un-ingested, directly above the section that had ingested it.
Sibling: `docs/PROJECT-intellectual-foundation-v3.md` (the *why*); this file is the *how* and the *why-built-this-way*.

> Decoupled: the originals are grounded in a named, specific deprived population and contain internal Drive folder IDs; both are rendered/omitted here so the repo stays decoupled and public-safe.

---

## The six-thinker analytical framework (the reasoning layer)

Applied **explicitly and fully only in the monthly meta-synthesis** (Slot 4); embedded *implicitly* (filtering, citation discipline, epistemic labelling) in the daily/weekly routines. The framework does its deepest work synthetically, across a month's accumulated intelligence — the NHS evidence landscape doesn't move fast enough to warrant daily application (that would dilute it to decoration).

| Lens | Discipline | Real-world anchor |
|---|---|---|
| **Schmachtenberger** | generator-function / transdisciplinary synthesis (insight at the intersections) | the Consilience Project |
| **McGilchrist** | whole-system / hemispheric attention (the right-hemisphere view of the living whole) | Iain McGilchrist |
| **Weinstein** | unifying structure; interrogating *why a consensus exists* | Eric Weinstein (Geometric Unity) |
| **Lennox** | epistemic discipline — what is known vs inferred vs unknowable | John Lennox |
| **Holmes** | abductive / detective reasoning from the evidence | (Sherlock Holmes archetype) |
| **Data** | Bayesian / probabilistic reasoning; base rates; guarding against bias | **Daniel Kahneman** is the real thinker behind this lens |

(The foundation layer adds the *ethics* — Lennox/Imago Dei — and the *critical theory of value* — McGilchrist, T.J. Clark, Baxandall, Benjamin, Kleinman, Mol, Merleau-Ponty/Bois. See the intellectual-foundation doc.)

---

## System foundation (the *how*)

**Mission:** ensure every moment a patient spends in the health system adds *genuine* value to their life; build the evidence/intelligence/whole-system capability to make that true at scale. Components are judged against the mission; outputs that drift to generic NHS commentary (losing population specificity) are failing it.

**Routine architecture (runs in the Claude.ai runtime, not this repo):**
| Slot | Name | Cadence | Output |
|---|---|---|---|
| 1 | Daily Morning Brief | weekday AM | `#morning-brief` |
| 2 | Weekly Clinical Evidence Watch | weekly | `#evidence-watch` (PubMed + Scholar) |
| 3 | Weekly Synthesis + Bulletin | Fridays | `#weekly-synthesis` + `#bulletin` |
| 4 | **Monthly Meta-Synthesis** (most critical) | 1st Monday | `#strategic-log` + PIPELINE-SUMMARY to Drive |
| 5 | Memory Governance | 1st Sunday | `#google-memory-update` |
| 6 | Strategic Thread Connector | 30 min after Slot 1 | thread reply on `#morning-brief` |
| 7 | Slack Preservation Archive | last Sunday | Drive archive files |

**Pipeline:** daily (retrieve + locally filter) → weekly (VF-Pattern convergences + open questions) → monthly (full framework + PIPELINE-SUMMARY) → quarterly (consolidation → Evidence Scan + Editorial). Each tier does something the adjacent tiers cannot; skipping tiers loses analytical work.

**Pipeline fields (per item, canonical):** Domain · Finding · Evidence type · Status (NEW/CONFIRMED/UPDATED/DISCARDED) · Local relevance (High/Medium/Low — only High/Medium carried to Quarterly) · VAT implication · Open question.

**Label vocabulary:**
- *External evidence:* `[Meta-analysis]` `[Primary Study]` `[Guidance]` `[Audit/Data]` `[Synthesis]` `[Preprint]` `[Unverified]`.
- *Value Forge analytical (distinct category):* `[VF-Synthesis]` (the system's own cross-source position — calibrated confidence, NOT equivalent to published evidence), `[VF-Pattern]` (recurring cross-channel/cross-time signal), `[VF-Signal]` (weak signal, watch-and-verify).

**Preservation (dual, independent):** Slot 4 saves PIPELINE-SUMMARY to Drive at point of production (primary); Slot 7 archives channel outputs monthly (secondary). Designed around the free-Slack **90-day retention limit** — nothing critical may depend on Slack history alone.

---

## Design rationale (the *why-built-this-way*)

**Design philosophy:**
- **Compounding over accumulating** — each tier *advances* the previous tier's output (status markers, recurring open questions, longitudinal log); accumulation without compounding is noise.
- **Depth at the right tier** — match analytical method to scale; don't apply maximum rigour uniformly.
- **Preservation independence** — no single point of failure in preservation; critical data has ≥2 independent paths.
- **Epistemic honesty over institutional comfort** — labelling, calibration, and "say plainly when a section yields nothing" all serve knowing what we actually know vs infer.
- **Mission primacy** — adding genuine value to patients' lives is *the* criterion, not one among many.

**Key architectural decisions (and why):**
1. **Thinker framework centralised in Slot 4** — applied monthly on accumulated material; daily application would make it formulaic/decorative.
2. **PIPELINE-SUMMARY saved directly by Slot 4** — independent of the Slot 7 archive chain (no single preservation dependency).
3. **First-edition explainer sits in the theme rotation** — demonstrates the system on real intelligence, not a Step-Zero preamble.
4. **Strategic Thread Connector (Slot 6) separate from Slot 1** — precision retrieval vs strategic interpretation are different operations; separation aids maintenance/diagnosis.
5. **VF labels a distinct category** — Lennox discipline applied to the system's own outputs; never dress system inference as published `[Synthesis]`.
6. **Four-tier pipeline** — each tier produces what adjacent tiers cannot.
7. **Community as a cross-cutting secondary lens, not a sixth domain** — the acute↔community interface is context for all five domains.
8. **Slot 7 separate from Slot 5** — Slack preservation vs Claude-memory governance are different systems/data.
9. **Local relevance as a flag (High/Medium/Low), not binary include/exclude** — relevance is a spectrum; preserve it for weighting.
10. **Status markers on every item** — the compounding mechanism; without them each month is a fresh list, not a developing record.

**Failure modes to watch:** *drift* (outputs become generically useful, lose population specificity); *decoration* (framework named but not performed); *confidence miscalibration* (inference dressed as evidence; preprint mislabelled as primary); *cascade* (a Slot 4 miss leaves a Quarterly gap); *first-edition* (a thin inaugural sets a poor permanent tone).

**Triggers for a design review:** self-audit recommends prompt changes two months running; Quarterly can't be built from available summaries; framework analysis is consistently thin; a new routine would interact with existing slots; Slack pricing/platform changes; the Quarterly moves to wider distribution; >6 months without a memory consolidation.

---

## Governance (decoupled essentials)

> The governance original (`VALUE-FORGE-GOVERNANCE-v1`, Drive) is the most *identifying* document — it names the owner's role and specific trusts/hospitals. All of that is omitted here; only the decoupled, transferable essentials are kept.

**The six-thinker framework — full articulation** (each chosen because it addresses a *distinct, recurring failure mode* in complex-system leadership; together they check each other's blind spots):
- **Daniel Schmachtenberger** — map the whole system before intervening; **generator functions** (surface problems are produced by underlying structural causes — intervene at the cause, not the symptom). Warns against *naive sensemaking* (accepting the first coherent narrative because coherence feels like understanding). Don't inherit a problem's framing from any body before checking the framing is accurate.
- **Iain McGilchrist** — holistic, contextual perception must temper reductive analysis; the part-focused mode cannot perceive living wholes. Clinically real: a frail person isn't the sum of their problem list (organ-system medicine on multimorbidity produces iatrogenic harm); CGA is the evidence-based corrective; a good death cannot be decomposed into measurable variables. Ask of every input: *does this see the whole, or only the part it was built to measure?*
- **Eric Weinstein** — why institutional consensus diverges from the best evidence; the **Distributed Idea Suppression Complex** (incentives, gatekeeping, credentialling that make consensus self-reinforcing regardless of evidence). Scrutinise guidance with the same rigour as any claim; name when invested confidence exceeds what the evidence supports.
- **John Lennox** — epistemic precision at the limits of knowledge: hold apart *demonstrated* / *reasonably inferred* / *speculative* / *genuinely unknown* without false certainty or relativism. The pretence of certainty where none exists is a specific institutional dishonesty with operational consequences.
- **Sherlock Holmes** (archetype) — abductive reasoning under incomplete evidence: observe before theorising, generate and test hypotheses, eliminate what's contradicted, hold conclusions only as firmly as the evidence warrants. Corrects *theory before evidence*.
- **Lieutenant Commander Data** (archetype) — dispassionate transparency about epistemic status: state what is and isn't known with equal precision; update without ego; don't shade findings to manage relationships or dress uncertainty in confident language. **Real-world anchor: Daniel Kahneman** (base rates, probability, bias).

**Operating principles:** clinical first; community secondary (the acute↔community interface is a standing question on every domain); value-added-time filter; population lens (national guidance assessed for how it lands on a specific population, never assumed to translate); citation discipline (no item without a verifiable source + date — unverified is excluded, not hedged); no duplication; recursive by design; honest accounting (say so when a section yields nothing; three strong items beat twelve weak ones); public benefit takes precedence over personal/institutional advantage.

**AI-assistant configuration (how the model is asked to reason):** reason from first principles on contested/high-stakes questions rather than defaulting to consensus; construct ≥2 independent lines of analysis before concluding; distinguish established/provisional/contested/unknown and state confidence directly; challenge weak assumptions and flawed logic (including the operator's); don't default to agreement for social ease; surface second-order/systemic effects.

**Scope honesty / what this is not:** a personally-operated synthesis of *publicly available* evidence to support strategic thinking — **not** a research platform, clinical decision-support tool, substitute for formal literature review, or an official NHS intelligence function. Outputs are a starting point for thinking, validated through proper clinical/governance structures before any action. No patient-level, trust-level, or non-public data is ever used.
