---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP
artifact_type: test_plan
tags: [architecture, strategy]
---

# Test Plan — TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP

1. **Rename regression**: `tests/unit/strategic/test_belief_cycle.py`'s existing
   `TestBeliefDecay` class (4 tests) updated to call `decay_stale_leads()`, still pass unchanged
   in logic — proves the rename didn't alter behavior.
2. **Real pipeline wiring** (new): construct a real `AuthoritativeState` with one entity holding a
   stale `APPROXIMATE` lead (`discovered_tick` more than `stale_threshold` ticks before
   `state.tick`), run `BeliefCycleSystem.resolve_lead_staleness(state)` (or the real
   `AuthoritativeApplyPipeline.refine()` if that's cheaper to construct realistically), assert the
   lead demotes to `VAGUE` with no contradiction path involved.
3. **PRECISE immunity in the real pipeline** (new): same shape, `PRECISE` lead, assert unchanged.
4. **No inconsistent double-write** (new): a lead that is both stale (age > threshold) and
   contradicted (world state now inconsistent with it) in the same tick — run the real phase
   sequence in the correct order (decay before contradiction) and confirm the final certainty is
   `EXHAUSTED` (contradiction wins), not `VAGUE` (decay's own output, which would mean the ordering
   or merge assumption was wrong).
5. **`capacity_enforcement.py` interaction** (new): an entity over `max_leads` with one fresh
   `APPROXIMATE` lead and one stale `APPROXIMATE` lead about to decay this tick; confirm the
   pruning phase removes the (now-lower-scored) decayed lead, not the fresh one.
6. **Doc/parity correction verification**: `docs/simulation/belief_and_detour_contract.md`'s
   `BeliefEntry` description no longer claims time-based decay; `STRAT-239` in
   `docs/parity_ledger/strategic_cognition.yaml` has a corrected `test_path` and an honest history
   note, written via `tools/parity_ledger_writer.py::write_entry()` (never hand-edited), confirmed
   by re-reading the shard after the write and by `tools/parity_index.py build` succeeding
   (`write_entry()` already rebuilds the index in-process on success).
7. **Regression**: real scoped suite confirmed during Implement (expected:
   `tests/unit/strategic/ tests/unit/cognition/ tests/unit/domains/information/
   tests/integration/strategic/ tests/architecture/` at minimum) — must stay green.
