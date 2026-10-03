# Investigation — TCK-20260616-DOCS-READABILITY-PILOT

## Scope sizing
- 348 markdown docs under `docs/` excluding `docs/archive/`.
- 218 of those mention a numbered "Phase N"/"Milestone N" pattern.
- 112 of the 218 are under `docs/engine/`; of those, 64 (`docs/engine/history/` + `docs/engine/ledger/`) are self-declared historical migration records, relocated to `docs/archive/` under TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER — out of scope for this epic.
- Remaining in-scope total after archival: 154 files across mechanics, engine/contracts, engine/matrices, core, simulation, observability, testing, combat, systems, strategy, cognition, world, guidelines, compliance, plans.

## Key finding: two different meanings of "Phase N" coexist in the corpus
1. **Development-milestone tracking** — e.g. `docs/core/entity_base.md`'s "Section 38: Phase 26 — Behavior Scorecards..." headers, organizing an entire doc as a chronological changelog of when features were built. This is what the user wants removed — these docs describe *what was built and when*, not *how the engine works*.
2. **Genuine runtime architecture** — the kernel's 6-phase tick lifecycle (named, not numbered, per `docs/engine/kernel.md`) and the authoritative pipeline's 17 numbered refinement stages (e.g. "Phase 14 — Objective Reward") are real, load-bearing facts about execution order that many docs cross-reference for correctness (e.g. "rewards are only applied in phase 14" tells a reader exactly when in the tick a mutation becomes legal). Stripping these outright would lose real information.

The pilot's rewrite rule (see plan.md) keeps category 2's *names* while dropping bare numbers and the word "Phase" itself, to avoid visual confusion with category 1. Category 1 is deleted or rephrased around current status, never preserved.

## Risk found during archival prep (not pilot, but relevant context)
Moving `docs/engine/history/` and `docs/engine/ledger/` required fixing ~29 files' worth of relative markdown links (`](../engine/X.md)`), since some targets stayed in `docs/engine/` and others moved with the relocated set. The same risk applies within the pilot/future batches if any rewritten doc's heading anchors are referenced elsewhere (e.g. `docs/core/entity_base.md#section-38-phase-26-...`) — renaming headings changes anchors. None of the 4 pilot files had incoming anchor-specific links (verified via `grep -rn` for each doc's basename across `docs/`), but this must be checked per-file in the full-scale batches, especially for `docs/core/entity_base.md` which is heavily cross-referenced.

## Verification performed
- `grep -rn` for each pilot file's basename across `docs/` to confirm no incoming anchor-specific links before editing.
- Post-edit grep sweep confirmed zero remaining numbered phase/milestone matches in all 4 pilot files.
- `make knowledge-index-update` ran cleanly (6 files re-embedded, 0 deleted — expected since this batch only edits content, doesn't move/delete files).
