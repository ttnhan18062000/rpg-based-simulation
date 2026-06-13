---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS
phase: open
date: 2026-06-13
tags: [documentation, engine, compaction, candidate-selection, determinism, performance]
---

# TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS

## Title
Add Standalone Engine Runtime Contracts: State Compaction, Candidate Selection, Deterministic Execution

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/engine/` has strong coverage of the authoritative pipeline phases, kernel, and governance logic. However three runtime concerns are either scattered across multiple files or missing entirely:

1. **State update compaction** — The engine compacts multiple intents targeting the same field before the authoritative apply step. Tests already verify semantic equivalence (compacted vs raw apply produce the same fingerprint). This is both a performance contract and a correctness contract. No standalone doc explains the compaction semantics, when it fires, what invariants it preserves, and what tests prove equivalence.

2. **Candidate selection** — Before mutation is applied, the engine selects which candidate updates are eligible for the current tick. The selection rules (phase, eligibility, ordering, deduplication) are not documented as a standalone contract. They are partially implied by `governance_logic.md` but not spelled out.

3. **Deterministic execution** — The engine makes specific guarantees about determinism: same world state + same seed produces identical output. This spans random seed management, ordering of concurrent entity resolution, and which operations are forbidden in hot paths (no `set` iteration without sort, no `dict` ordering dependence, etc.). The determinism guarantee is referenced in tests but has no standalone contract explaining what is guaranteed, what is not, and how to maintain it.

All three are critical for agents answering questions like: "Why did the replay diverge?", "Can I add a set-based lookup here?", "Is this a compaction bug or an apply bug?"

## Scope
Create three new docs in `docs/engine/`:

1. **`docs/engine/state_update_compaction.md`** — Compaction contract. Must cover:
   - What compaction is: merging multiple intents for the same field into a single canonical update before apply
   - When it runs in the pipeline (which phase, before or after candidate selection)
   - The merge rules: last-write-wins vs additive vs max/min for different field types
   - Invariant: compacted apply must produce the same semantic fingerprint as raw sequential apply
   - What tests verify this (the performance correctness test group)
   - What operations are forbidden during compaction (no side effects, no IO, no external calls)
   - Extension rules: how to register a new field type for compaction

2. **`docs/engine/candidate_selection.md`** — Candidate selection contract. Must cover:
   - What a candidate is (an entity or world object eligible for mutation in this tick)
   - The selection pipeline: phase filter → governance eligibility → deduplication → ordering
   - What the governance eligibility rules are (link to `governance_logic.md`)
   - Ordering guarantees: is candidate order deterministic? What determines order?
   - How skip/defer works: candidates that are not selected this tick
   - Edge cases: no candidates, all candidates ineligible, candidate added mid-selection
   - Source areas: `src/engine/`
   - Tests: which test group validates candidate selection behavior

3. **`docs/engine/deterministic_execution.md`** — Determinism contract. Must cover:
   - The core guarantee: identical world state + identical seed → identical simulation output (replay equivalence)
   - What is in scope for the guarantee (entity decisions, resource transfers, combat outcomes, world evolution)
   - What is explicitly NOT guaranteed (wall-clock time, log ordering, observability event ordering)
   - The rules that maintain determinism: no unordered set iteration, no dict key ordering, seed isolation per entity, no global mutable state
   - How random draws are issued (via seeded RNG, not `random.random()` directly)
   - What happens when determinism breaks: replay divergence detection, how to diagnose
   - Which tests enforce this (replay tests, determinism tests)
   - Extension rules: how to add new behavior without breaking the determinism guarantee

Each doc must follow the standard logic-contract template.

## Out of Scope
- Modifying `docs/engine/authoritative_pipeline.md` or `docs/engine/kernel.md`
- Covering the full 17-phase refinement sequence (already in `authoritative_pipeline.md`)
- Performance benchmarks or hardware class limits (already in `performance_contract.md`)

## Acceptance Criteria
- [ ] `docs/engine/state_update_compaction.md` created. Contains merge rules per field type, the semantic fingerprint equivalence invariant, and concrete test references. Frontmatter: `status: active`, `layer: engine`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/engine/candidate_selection.md` created. Contains full selection pipeline (filter → eligibility → dedup → order), ordering guarantees, skip/defer behavior. Frontmatter: same.
- [ ] `docs/engine/deterministic_execution.md` created. Contains the scope of the determinism guarantee, the rules that maintain it, forbidden operations, and how to diagnose divergence. Frontmatter: same.
- [ ] Each doc has a `## Regression tests` section with real test file references.
- [ ] Each doc has a `## Extension rules` section.
- [ ] `docs/engine/README.md` or `docs/engine/project_lawbook.md` updated to reference the three new contracts.
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-CORE-DIRTY-STATE (update intents feed into compaction — cross-link)

## Related Docs
- `docs/engine/kernel.md` — 6-phase deterministic loop
- `docs/engine/authoritative_pipeline.md` — 17-phase refinement sequence
- `docs/engine/governance_logic.md` — eligibility rules (candidate selection depends on this)
- `docs/engine/authoritative_mutation_pipeline_contract.md` — mutation rules
- `docs/engine/performance_contract.md` — hardware class performance contracts
- `docs/engine/known_limitations.md` — current scope boundaries and known non-determinism cases

## Related Stored Artifacts
None

## Related Code Areas
- `src/engine/pipeline_phases/` — phase execution (candidate selection, compaction)
- `src/engine/intent/` — intent handling and compaction logic (if present)
- `src/perf/` — performance-related compaction paths
- `src/replay/` — replay system (determinism verification)
- `tests/perf/` — performance correctness tests including fingerprint equivalence
- `tests/engine/` — engine-level tests

## Assumptions / Open Questions
- Verify the exact phase number where compaction fires before writing — if the pipeline has changed since the proposal, document what is actually there.
- If "candidate selection" is not a named concept in the source (may be called differently), grep for the concept and document it using the source term in the doc body, with a note that external docs call it "candidate selection."
- The determinism rules ("no unordered set iteration") should be verified against `docs/guidelines/design_patterns.md` — some rules may already be written there. Cross-link rather than duplicate.

## Implementation Notes
1. Read `src/engine/pipeline_phases/` files to find where compaction and selection actually happen.
2. Read `src/replay/` to understand how determinism is verified (replay diff mechanism).
3. Read `tests/perf/` to find the fingerprint equivalence test — cite it in compaction doc.
4. Check `docs/engine/known_limitations.md` for any documented non-determinism edge cases — reference them in the determinism contract.

## Test Summary
Not applicable — documentation ticket.

## Files Changed
- `docs/engine/state_update_compaction.md` (new)
- `docs/engine/candidate_selection.md` (new)
- `docs/engine/deterministic_execution.md` (new)
- `docs/engine/README.md` (updated: add new contracts to index)

## Completion Summary
Created 3 engine runtime contract docs: state_update_compaction.md (two-layer compaction, fingerprint equivalence invariant, merge rules cross-linked to update_intents.md), candidate_selection.md (3-tier selection: DeterministicScheduler/CandidateSelector/MovementCandidateSelector with 6-stage filter pipeline), deterministic_execution.md (scope of guarantee, 4 enforcement rules, DeterministicRNG stateless design, divergence detection via audit_mode/audit_dirty_set/tick_hash comparison). All docs cross-link to existing kernel.md and dirty_state_and_dependency.md. Knowledge index: 33 files changed.
