# Patterns over time — the year-in design (July 2026)

**Status: DESIGN NOTE — the editor's prompt (15 Jul): "think about how patterns functions over time… imagine we are a year into the project… patterns need to be linked to at least some references." Nothing here is built yet; sequencing at the end.**

The pattern register is the site's only *cumulative* artifact — signals and syntheses are weekly snapshots, the Monthly is a monthly one, but VF-P1 in July 2027 is the same object as VF-P1 today, carrying a year of longitudinal record. That makes it both the most valuable thing on the site a year in, and the thing whose failure modes compound. Five findings, ordered by consequence.

## 1. The regeneration fidelity risk (most consequential)

`data/patterns.json` is **wholesale-regenerated** each monthly cycle: the translator re-emits the entire file from the monthly summary. Today that's 11 patterns × ~1 history entry. A year in it's plausibly 30–60 patterns × 12+ entries — and the architecture asks a language model to faithfully re-transcribe a large longitudinal record it is only *appending to*, every month. One bad cycle silently truncates a history array, drops a pattern, or rewrites `first_appeared` — the same failure class as the 19-Jun scalar break, but against the one dataset that cannot be regenerated from anywhere else. Git history makes it *recoverable*; nothing makes it *detected*.

**Mitigation A (now, sync-side, free):** `drive_sync.py` validates an incoming `patterns.json` against the current one with **monotonic guards** — warn-and-hold (don't route) if: an existing `id` disappears; any existing pattern's `history` array shrinks; any `first_appeared` changes; `generated` goes backwards. The longitudinal record is append-only by nature; the sync should enforce that shape. (Extends the existing warn-annotation machinery; same create-only-discipline philosophy as PR #33.)

**Mitigation B (medium term, architectural):** the translator stops re-emitting the whole file and emits a monthly **delta** (`patterns-delta-YYYY-MM.json`: new patterns + new history entries + status changes only); a repo-owned merge script folds it into the canonical file. The model never re-writes history it isn't changing. Requires translator v3.5 + a small script — worth doing before the file gets big, cheap while it's small.

## 2. References — from prose to structure (the editor's explicit ask)

The evidence **half-exists already but is trapped in prose**: history notes contain PMIDs as free text (`"Clinical evidence (PMIDs 42100443, 41665982, …); operational (PRN02404; …)"`). The register template already renders notes through `pmid-link.html`, so PMIDs are clickable today — but nothing *requires* a reference, nothing can *check* one, and there is no link to the site's own evidence chain.

The house's own static-copy rule (§8) makes this a matter of principle, not polish: **patterns are the most consequential claims the site makes, and a claims register whose entries can be emitted unreferenced is a spirit-violation of the site's own failsafe.**

Two reference layers, both on the history *entry* (evidence attaches to the observation, not the pattern abstract):

- **Layer 1 — structured citations:** each history entry gains `references: [{"pmid": "42100443"}, {"cite": "NHSE Board Item 8, 4 Jun 2026", "url": "…"}]`. PMIDs machine-checkable; non-PubMed citations carry their own label/URL.
- **Layer 2 — internal provenance (the richer one):** each history entry gains `supporting: ["<signal-or-synthesis-slug>", …]` — the site's own articles that fed the observation. Pattern → signal → that signal's PubMed-verified `sources:` is a full provenance chain, the links can never rot (same site), and the register can render "Evidence: 3 signals · 1 synthesis" per entry. The Evidence Timeline can then draw true pattern↔signal relationships instead of inferring by date.

**Enforcement, three points:**
1. **Schema (upstream):** translator v3.5 makes `references` and/or `supporting` REQUIRED on every new history entry — a pattern observation with neither does not clear the bar for the register (parallel to the weight-bar rule in v3.4).
2. **Sync (repo, free):** `drive_sync.py` warn-annotates any incoming history entry carrying neither a PMID (in structured refs or note text) nor a `supporting` slug.
3. **Editorial:** a pattern with no references anywhere in its history cannot be VAT-designated in `data/vat_patterns.yaml` (gold is the site's strongest claim; it must sit on the strongest evidence). Rule recorded here; enforced by editorial practice.

Back-fill: the 11 current patterns all carry PMIDs in note prose — a one-off structured back-fill can be done at v3.5 activation (or left: display-level linking already works; the guards apply to new entries).

## 3. Lifecycle — a register that only ever confirms is a red flag

All 11 patterns are `status: "established"` today. Over a year the register earns credibility precisely from **visible revision and discard** — the Kahneman/base-rate discipline demands a visible hit rate ("11 patterns proposed, 8 held, 2 qualified, 1 discarded" is a stronger epistemic claim than 11 evergreen confirmations, and the site's honesty-about-limits voice requires it).

**Lifecycle vocabulary** (translator emits; templates render):
`emerging` → `established` → (`qualified` — held but narrowed) → (`contested` — credible counter-evidence, maps to `--vf-contested`) → (`discarded` — register keeps it, struck through in the catalogue, history preserved) → (`superseded` → successor id — split/merge trace).
Plus one **build-time computed** state, not translator-emitted: **dormant** (no history entry in N≥4 months) — rendered as a quiet section, never deleted.

**Register page a year in:** active patterns first (current two-column register), then dormant (compact rows), then discarded/superseded (ledger rows, struck, with the discard note — the "we were wrong here" record is a feature, displayed with the same typographic dignity). Front-page strip logic unchanged (highest-salience active + VAT gate).

## 4. Patterns need permalinks — the pattern as citable object

A year in, VF-P1 with 12 entries and a provenance chain is the most citable object the publication owns — and currently it has **no URL** (it exists as a row on `/patterns/` and dots on the timeline). Commissioners citing "VF-P1, tracked since Jun 2026, 14 supporting signals across five domains" need `/patterns/vf-p1/`.

**Mechanism:** Hugo content adapters (`content/patterns/_content.gotmpl`, supported in v0.147) generate a page per pattern from `data/patterns.json` at build time — no hand-maintained content files, pipeline stays the single writer. Each page: title/status/domain span; full dated history with per-entry evidence links (both layers); status-change timeline; VAT designation if held; citation line (CC BY). Pagefind indexes them; signals can cross-link back ("contributes to VF-P1").

## 5. Governance rhythm

- **Annual "state of the register"** section in the June Monthly (register anniversary): hit rate, discards, splits/merges, evidence-density per pattern — Slot 4 already does monthly meta-synthesis; this is one added annual section (routine change, the editor pastes).
- **VAT designations reviewed on status change:** a pattern leaving `established` triggers an editorial re-check of its `vat_patterns.yaml` entry.
- **`intelligence_window` is currently emitted empty** — minor upstream fix to fold into v3.5.

## Sequencing

| Step | What | Where | Status |
|---|---|---|---|
| 1 | This design note | docs/ | ✅ done (15 Jul) |
| 2 | Sync guards: monotonic patterns validation (HOLD on id loss / history shrink / first_appeared rewrite / stale generated) + reference warnings on new entries + append-only idempotent **delta merge** (`patterns-delta-YYYY-MM.json`), full-file path kept for v3.4 back-compat | `scripts/drive_sync.py` + `scripts/test_drive_sync_patterns.py` (11 tests, all pass; live file re-validates clean) | ✅ **BUILT 15 Jul** ("fix the backend" — the editor's go). Inert until the PR merges to `main` (the daily Action runs main's scripts) |
| 3 | Translator v3.5 patterns amendment: delta emission, REQUIRED `references`/`supporting` on every new history entry, `intelligence_window` fix, lifecycle vocabulary | `docs/translation/ROUTINE-weekly-translator-v3.5-PATTERNS-AMENDMENT-DRAFT.md` | ✅ **DRAFTED 15 Jul** — awaiting the editor: apply 3 edits to the live Claude.ai copy + dual-home |
| 4 | Pattern permalink pages (content adapter, `/patterns/vf-p1/`…) + per-entry evidence rendering (structured refs + supporting links) in register and permalink pages + lifecycle-status CSS vocabulary | `content/patterns/_content.gotmpl`, `layouts/patterns/single.html`, `layouts/partials/pattern-evidence.html` | ✅ **BUILT 15 Jul** (the editor: "carry on with fixing as much as you can") — preview-staged on PR #37. Deferred within step 4: dormant-state auto-computation and discarded-section layout (no data exercises them yet — the CSS vocabulary is ready) |
| 5 | Annual state-of-the-register section | Slot 4 routine (Claude.ai) | the editor action, when due |

Remaining decision for the editor: **step 4's shape** (permalink pages via content adapter + lifecycle sections on the register). Steps 2–3 are built/drafted; step 3 activates only when he pastes.
