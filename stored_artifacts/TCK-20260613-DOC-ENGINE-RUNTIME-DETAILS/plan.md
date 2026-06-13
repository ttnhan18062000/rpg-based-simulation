# Plan — TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS

Ticket: TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS
Date: 2026-06-13

---

## Goal

Create three standalone engine contracts in `docs/engine/`:
1. `state_update_compaction.md`
2. `candidate_selection.md`
3. `deterministic_execution.md`

Then update `docs/engine/project_lawbook.md` (the master index) to reference all three.

---

## Key findings from investigation

### Compaction
- Two-layer system: `StateUpdate.merge_many()` (aggregation) + `StateUpdateCompactor.compact_with_metrics()` (true compaction)
- Compaction fires as the very first step in `AuthoritativeApplyPipeline.refine()` (pipeline.py:96), before any of the 17 phases
- Three merge rules: delta-sum, set-last-write-wins, list-concatenation
- Fingerprint equivalence invariant is tested in `tests/perf/test_apply_compaction_perf.py:76`
- `docs/core/update_intents.md` already covers the merge rules and `merge_many()` — cross-link, do not duplicate
- The new doc must explain `StateUpdateCompactor` (the richer layer), the two compaction modes (standard vs AGGRESSIVE), and the fingerprint invariant

### Candidate selection
- Two distinct mechanisms: dirty-set domain routing (`CandidateSelector` in dirty.py) and movement-specific sub-selection (`MovementCandidateSelector` in candidate_selector.py)
- `docs/core/dirty_state_and_dependency.md` already covers dirty-set routing exhaustively — cross-link, do not duplicate
- The new doc should frame the full 3-tier selection hierarchy (scheduler → dirty-set routing → movement sub-selector) and document the 6-stage `MovementCandidateSelector` filter in detail
- Budget enforcement and urgency classification are movement-specific and not yet documented anywhere

### Determinism
- Core guarantee is same-seed → same hash, verified by `CanonicalStateHasher.get_hash()` (SHA-256 of sorted canonical JSON)
- `DeterministicRNG.get_float()/get_int()` are stateless (composite seed) — order-independent
- Result sort (kernel.py:449) collapses concurrent collection into deterministic resolution order
- Parity is officially ratified for Sequential mode only (known_limitations.md:28)
- `docs/engine/kernel.md` covers the 6-phase loop and audit_mode fingerprinting — cross-link, do not duplicate
- New doc should cover: RNG model, canonical hash mechanics, forbidden operations, divergence diagnosis, and extension rules

---

## Implementation steps

### Step 1: Write `docs/engine/state_update_compaction.md`
Structure:
- Frontmatter (status: active, layer: engine, authority: P1, audience: agent, last_verified: 2026-06-13)
- What compaction is (two-layer: merge_many + StateUpdateCompactor)
- When it runs (Phase 1 of AuthoritativeApplyPipeline.refine, before all 17 phases)
- Merge rules (cross-link to update_intents.md — do not copy tables)
- Fingerprint equivalence invariant (the correctness contract)
- Compaction modes (standard vs AGGRESSIVE)
- Forbidden operations during compaction
- Regression tests (cite test_apply_compaction_perf.py:76 and test_dirty_set_integrity.py)
- Extension rules (how to register a new field type)

### Step 2: Write `docs/engine/candidate_selection.md`
Structure:
- Frontmatter
- What a candidate is
- Three-tier selection hierarchy (scheduler → dirty-set routing → phase-level sub-selection)
- Tier 1: DeterministicScheduler.select_work() — readiness, LOD, cadence gating
- Tier 2: CandidateSelector / get_relevant_entity_ids() — domain routing (cross-link to dirty_state_and_dependency.md)
- Tier 3: MovementCandidateSelector — the 6-stage filter in detail
- Urgency classification and budget enforcement
- Ordering guarantees (always sorted entity ID)
- Skip/defer mechanics (non-urgent under EXACT_DIRTY policy, readiness ungating)
- Edge cases (no candidates, force_full_scan, all ineligible)
- Regression tests
- Extension rules

### Step 3: Write `docs/engine/deterministic_execution.md`
Structure:
- Frontmatter
- Core guarantee (same seed + same state → same hash)
- What is in scope / what is explicitly NOT guaranteed
- Rules that maintain determinism (RNG model, result sort, canonical hash, immutable state, sorted candidate sets)
- DeterministicRNG: stateless vs stateful API, domain separation, forbidden uses
- CanonicalStateHasher: what it covers, what it does not
- How to diagnose divergence (audit_mode, DirtySetLeakError, replay tick_hash comparison)
- Known parity limitation (sequential-only ratification)
- Regression tests
- Extension rules (how to add new behavior without breaking determinism)

### Step 4: Update `docs/engine/project_lawbook.md`
Add the three new contracts to the master index table.

### Step 5: Run post-completion commands
```
make knowledge-index-update
make docs-registry
```

---

## Constraints
- Do NOT modify `docs/engine/kernel.md` or `docs/engine/authoritative_pipeline.md`
- Do NOT cover the full 17-phase sequence (already in authoritative_pipeline.md)
- Do NOT copy merge rule tables from update_intents.md — cross-link instead
- Do NOT copy domain routing tables from dirty_state_and_dependency.md — cross-link instead
- Each doc must have `## Regression tests` and `## Extension rules` sections
- Frontmatter: status: active, layer: engine, authority: P1, audience: agent, last_verified: 2026-06-13

---

## Files to create / modify
| File | Action |
|---|---|
| `docs/engine/state_update_compaction.md` | Create |
| `docs/engine/candidate_selection.md` | Create |
| `docs/engine/deterministic_execution.md` | Create |
| `docs/engine/project_lawbook.md` | Update (add 3 entries to index) |
