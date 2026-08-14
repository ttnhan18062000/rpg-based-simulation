---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION
artifact_type: test_plan
tags: [simulation-quality, cognition, adventure]
---

# Test Plan — TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION

## Regression Surface

The fix touches `src/engine/tactical.py`'s Pillar 5.1 `elif` branch (lines 260-287) — shared
infrastructure for combat target selection, movement, and every non-`REACH_LOCATION` Objective. It
may also touch `src/domains/adventure/resolver.py` if Plan chooses option (a) instead of the
investigation's option (b) recommendation. All of the following must keep passing unmodified.

**Unit — tactical / combat** (same `evaluate_entity_intent` method as the objective-pursuit
branch; a change confined to lines 260-287 can still regress control flow earlier in the method if
not exercised):
- `tests/unit/tactical/test_target_stickiness.py`
- `tests/unit/tactical/test_objective_pursuit_coverage.py` — contains the existing
  `test_objective_kind_reach_resource_produces_executable_action` (far-away case) and
  `test_objective_kind_acquire_item_produces_executable_action` (unrelated `ObjectiveKind`, must
  not regress).
- `tests/unit/combat/test_anti_stalemate.py`
- `tests/unit/combat/test_tactical_legality.py`
- `tests/unit/combat/test_engagement_behavior.py`
- `tests/unit/combat/test_tactical_hardening.py`
- `tests/unit/combat/test_target_selection_contract.py`
- `tests/unit/movement/test_tactical_movement.py`
- `tests/unit/movement/test_mob_leashing.py`

**Unit — Adventure domain** (`ObjectiveIntentResolver`, only relevant if Plan touches
`resolver.py`):
- `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`
- `tests/unit/domains/adventure/test_craft_upgrade_execution.py`

**Integration — Adventure domain / pipeline:**
- `tests/integration/domains/adventure/test_harvest_to_event.py` — existing `item_crafted` test;
  its docstring explicitly documents the current gap this ticket closes and should be updated (not
  a behavior regression risk, but stale-comment hygiene — see investigation.md Prior Work).
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`
- `tests/perf/test_phase3_adventure_decision_budget.py` — perf budget guard; the new branch adds
  one more conditional check per non-`REACH_LOCATION` objective per tick, must not blow budget.

**Unit/Integration — Strategic cognition (System B, shares `tactical.py`'s `REACH_LOCATION`
branch as the working reference; must not regress from a nearby edit):**
- `tests/unit/strategic/test_strategic_cognition_regression.py`
- `tests/unit/strategic/test_cognition_authoritative_path.py`
- `tests/integration/pipeline/test_strategic_cadence.py`

**Architecture / integrity guard:**
- `tests/integrity/test_logic_guards.py::test_objective_intent_resolver_is_reachable_from_production_pipeline`
  — explicit AC requirement (must still pass); asserts `"ObjectiveIntentResolver.resolve"` appears
  literally in `inspect.getsource(TacticalDecisionSystem.evaluate_entity_intent)`.

## New Tests Required

Per the ticket's Acceptance Criteria:

1. **`test_objective_kind_reach_resource_far_from_node_still_navigates`** (AC #1 — may already be
   satisfied by the existing `test_objective_kind_reach_resource_produces_executable_action` in
   `tests/unit/tactical/test_objective_pursuit_coverage.py`; add only if that test's coverage
   doesn't already assert "no harvest action fires while far away," e.g. assert
   `update.task is None` or `update.interaction is None` in addition to the existing navigation
   assertion, to make the "unchanged" claim explicit rather than incidental).
   - Category: unit
   - Verifies: entity at distance > 1.0 from the target resource node continues to receive
     navigation (not a harvest/interact action) — regression guard for AC #1.
   - Location: `tests/unit/tactical/test_objective_pursuit_coverage.py` (extend existing test or
     add alongside it).

2. **`test_objective_kind_reach_resource_arrival_produces_harvest_action`**
   - Category: unit
   - Verifies: entity within `dist <= 1.0` of the target resource node, with an active
     `ObjectiveState(kind=ObjectiveKind.REACH_RESOURCE, target=str(node.id))`, produces a
     non-`MOVE_TO` result from `TacticalDecisionSystem.evaluate_entity_intent` — specifically a
     `task`/`interaction` payload equivalent to an `INTERACT`/harvest action on the node
     (`target_id == node.id`), not `update.navigation.target_set` pointing at the (already-
     reached) node position again. This is the direct regression test for AC #2 and the ticket's
     core bug.
   - Location: `tests/unit/tactical/test_objective_pursuit_coverage.py` (same file/fixtures as the
     existing `REACH_RESOURCE` far-away test, for easy side-by-side comparison).

3. **`test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`**
   - Category: integration
   - Verifies: a full, non-mocked drive from `TacticalDecisionSystem.evaluate_entity_intent`
     (entity already at/near the node) — or, mirroring `test_harvest_to_event.py`'s pattern, a
     directly-constructed `ActionIntent(kind="HARVEST_RESOURCE", target_id=node.id)` through
     `ActionIntentAdapter.execute()` — into `InteractionSystem.enforce`, then
     `ResourceTransactionSystem.resolve_all`, then `EventExtractor.extract`, produces a real
     `resource_harvested` `SimulationEvent`. Use `ResourceNodeState(required_ticks=1, ...)` (or
     drive `required_ticks` ticks of `InteractionUpdate(progress_delta=1)` accumulation) so
     completion happens within the test without an unbounded tick loop — mirroring how
     `test_harvest_to_event.py` keeps its `item_crafted` proof single-step. This is the direct
     test for AC #3 and the entry that satisfies `STRAT-246`'s P0 `test_path` requirement for the
     newly-closed arrival gap.
   - Location: `tests/integration/domains/adventure/test_harvest_to_event.py` (add a second test
     function alongside the existing `item_crafted` one; update the file's module docstring, which
     currently documents this exact gap as unclosed, to point at the new test instead of
     describing the gap as open).

4. **`test_objective_intent_resolver_is_reachable_from_production_pipeline`** — already exists
   (`tests/integrity/test_logic_guards.py:483`). No new test needed; re-run as-is per AC's explicit
   "must still pass" requirement. If Plan's chosen fix shape removes the `resolve()` call from the
   `REACH_RESOURCE` arrival path specifically (option b) while every other `ObjectiveKind` still
   reaches it, this guard remains satisfied — verify this is actually the case after implementing,
   since the guard is a blunt source-string check, not a per-`ObjectiveKind` reachability proof.

5. **`test_reach_location_arrival_behavior_unchanged`** (only if not already implicitly covered by
   existing combat/tactical regression suites — check at Implement time before adding)
   - Category: unit / anti-drift guard
   - Verifies: `ObjectiveKind.REACH_LOCATION`'s existing arrival branch (`tactical.py:213-259`)
     produces byte-identical `EntityUpdate` shapes before and after the fix, for both the
     node-target and building-target (`EAT`/`REST`) cases — explicit AC #4 regression guard, since
     the fix's new branch sits in the same method.
   - Location: `tests/unit/tactical/test_objective_pursuit_coverage.py` or existing strategic/
     tactical suites if equivalent coverage is confirmed to already exist.

## Scoped Pytest Commands

```bash
# Tactical / combat regression (tactical.py is shared with combat target-selection)
pytest tests/unit/tactical/ tests/unit/combat/ tests/unit/movement/ -v

# Adventure domain regression (only load-bearing if resolver.py is touched; run regardless as a
# cheap sanity check since ObjectiveIntentResolver.resolve is still invoked by this call path)
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v

# Strategic cognition (System B) regression — shares tactical.py's REACH_LOCATION branch
pytest tests/unit/strategic/test_strategic_cognition_regression.py tests/unit/strategic/test_cognition_authoritative_path.py tests/integration/pipeline/test_strategic_cadence.py -v

# Perf budget guard (adventure decision phase)
pytest tests/perf/test_phase3_adventure_decision_budget.py -v

# Architecture / integrity guard (explicit AC requirement)
pytest tests/integrity/test_logic_guards.py -v

# New tests added by this ticket (adjust paths to match final Implement placement)
pytest tests/unit/tactical/test_objective_pursuit_coverage.py tests/integration/domains/adventure/test_harvest_to_event.py -v
```

Do not run `pytest tests/` (repo-wide). Do not scope only to `tests/unit/tactical/` — the change
sits inside a method shared with combat/movement, and the parent ticket's own regression sweep
(`stored_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/test_plan.md`) already
established that a narrower scope missed relevant coverage once before.

## Anti-Drift Test Guards

- **`REACH_LOCATION` must not change behavior.** The fix adds a narrower branch inside the
  existing `elif` block; it must not touch, reorder, or fall through into `tactical.py:213-259`.
  Re-run the full tactical/combat/movement group (not just strategic-cognition tests) to catch any
  accidental control-flow bleed between the two branches.
- **`HarvestSystem`/`HarvestAction` must stay untouched and stay unwired.** A regression guard
  worth adding (or confirming already covered): `pipeline.py` should still have zero references to
  `HarvestSystem`/`HarvestAction.start_harvest` after this change — if a future edit accidentally
  wires the wrong system in, it would silently create the `TOWN-104` duplication the parity ledger
  already flags as a risk. Not required by the ticket's AC, but cheap insurance; consider a one-
  line assertion in `tests/integrity/test_logic_guards.py` if Plan agrees it's in scope.
- **`ObjectiveIntentResolver.resolve()`'s existing unit-mapping table must not change** unless
  Plan explicitly chooses option (a). Re-run
  `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py` and confirm no new
  assertions were needed there if `resolver.py` was left untouched (option b) — if it was touched,
  this file must gain a case for the new arrival-aware mapping.
- **`ActionIntentAdapter`'s `HARVEST_RESOURCE`, `REQUEST_CRAFT`, and `BUY_ITEM` dispatch branches
  must not regress.** These were the parent ticket's additions; a change to the shared
  `ActionIntentAdapter.execute()` tail (`action_intent.py:257-260`) risks all three, not just
  `HARVEST_RESOURCE`. Re-run `tests/integration/domains/adventure/test_harvest_to_event.py`'s
  existing `item_crafted` test unmodified alongside the new `resource_harvested` test.
- **`STRAT-246`'s `test_path` must remain a fully passing list after the update.** When the parity
  ledger entry is updated (per Acceptance Criteria), the new/extended test(s) added here must be
  appended to its `test_path` field, and every test already listed there
  (`test_objective_intent_resolver_is_reachable_from_production_pipeline`,
  `test_objective_pursuit_coverage.py`, `test_craft_upgrade_execution.py`,
  `test_harvest_to_event.py`) must still pass — do not update `v2_evidence`/`support_boundary`
  text without re-verifying the full existing `test_path` list, since it is P0.
- **Perf budget must not regress.** The new branch runs once per non-`REACH_LOCATION`,
  non-`DEFEAT_ENEMY` objective per entity per tick — cheap (one more `dist` comparison and
  conditional), but `tests/perf/test_phase3_adventure_decision_budget.py` is the existing guard
  and should be re-run rather than assumed safe.
