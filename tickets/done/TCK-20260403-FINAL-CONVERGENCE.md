# TCK-20260403-FINAL-CONVERGENCE: Final Architectural Stability & Convergence

## Status: INPROGRESS

## Goal
Complete the remaining open items in `final_implementation_plan_3.md` to achieve full architectural convergence and stability.

## Scope
1.  **Deeper Immutability**: Fix `SimulationModel.freeze()` to be recursively deep for collections (lists/dicts) of models.
2.  **Typed Records**: Replace `Any` in `ActionProposal.target` and `NavigationUpdate.target_pos` with specific types. Purge remaining `intent_metadata` usage.
3.  **Cleanup**: Remove leftover compatibility shims and dual serialization paths if any.
4.  **Serialization**: Ensure no `pickle` usage in infrastructure and audit `SimulationJSONEncoder`.
5.  **Payload Caching**: Finalize transport payload caching in `EngineManager`.
6.  **Integration Test Stabilization**: Resolve 26 failures across `test_hero_lifecycle.py`, `test_invariants.py`, `test_snapshot_safety.py`, and infrastructure-dependent tests.

## Acceptance Criteria
- [ ] `freeze()` is proven deep across nested collections in unit tests.
- [ ] No `Any` types remain in core action models.
- [ ] No `pickle` usage in `src/` (except where explicitly justified).
- [ ] 100% test pass rate for all simulation tests.

## Related Tickets
- TCK-20260403-RECOVERY
- TCK-20260402-VALIDATION
