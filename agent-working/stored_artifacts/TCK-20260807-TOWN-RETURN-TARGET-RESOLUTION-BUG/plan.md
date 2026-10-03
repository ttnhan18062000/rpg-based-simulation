---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG
artifact_type: plan
tags: [strategy, simulation-quality]
---

# Plan: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG

Per investigation.md, implement the ticket's own preferred option (a): add a `target_position`
fallback to `TacticalDecisionSystem._resolve_target_position()`, mirroring
`StrategicIntelligenceSystem._resolve_active_objective()`'s existing "detour" pattern.

## Steps

1. `src/engine/tactical.py`: in `_resolve_target_position()`, after the existing int-parse and
   coordinate-string-parse attempts, add `if target_pos is None and obj.target_position is not
   None: target_pos = obj.target_position`. Update the docstring to explain why (mirrors the
   detour pattern; additive-only, doesn't disturb `node_id`/`building_id` population for the
   currently-working int-castable paths).
2. Tests (`tests/unit/tactical/test_objective_pursuit_coverage.py`):
   - New objective with unparseable `target` + set `target_position` → navigates toward
     `target_position`.
   - New objective with unparseable `target` + no `target_position` → stays unresolved (no
     navigation), same as before this fix.
   - Anti-regression: objective with a real resolvable `target` (resource-node ID) PLUS a
     deliberately wrong `target_position` → the resolvable ID wins, proving the fallback never
     overrides the currently-working path.
3. Integration test (`tests/unit/strategic/test_expanded_goals.py`): drive the real production
   pipeline end-to-end — `StrategicIntelligenceSystem.evaluate_strategic_intent()` (TownScorer
   wins) → `TacticalDecisionSystem.evaluate_entity_intent()` — confirm a real `NavigationUpdate`
   toward `town_center` results.
4. Docs: `docs/engine/contracts/tactical_contract.md` — new Section 7, "Objective Target
   Resolution," documenting `_resolve_target_position`'s 3-step resolution order and the
   deliberate scope boundary (navigation only, arrival-dispatch for these 3 project kinds is
   separate, deferred future work).
5. Parity: `docs/parity_ledger/strategic_cognition.yaml` — new `STRAT-249` entry (this subsystem
   file, not `combat_movement.yaml` — the fix is about strategic-goal navigation resolution, not
   combat tactics, even though the touched function lives in `tactical.py`).
6. Real-kernel-adjacent verification: the same production-pipeline call sequence as the
   integration test, run manually first to confirm behavior before codifying it as a test.
7. Run scoped tests (`tests/unit/tactical/`, `tests/unit/strategic/`, `tests/unit/movement/`,
   `tests/unit/combat/test_tactical_hardening.py`, `tests/unit/combat/test_tactical_legality.py`),
   doc-staleness check, parity cross-reference, Verify static precheck, Finalize.

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md confirms exact fix location/design | Done — `target_position` fallback, option (a) |
| Fix implemented, resolves real position for the 3 kinds | Done |
| Regression test: existing int/tuple resolution unaffected | Done — dedicated anti-regression test |
| Real-kernel verification: purposeful progress toward town_center | Done — codified as `test_town_return_project_now_produces_real_navigation` |
| Scoped pytest passes | Done |
