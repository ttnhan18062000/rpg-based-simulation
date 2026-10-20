---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE
phase: open
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE

## Title
Every required validity row of the rpg gate has at least one real-kernel positive test, and a lint fails when an id has none.

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Two of rpg's validity checks were blind on the v1 gate run (rpg-planner, 2026-10-19), and both read 0 violations, so they looked green:
- V1 counted a 0-gold accepted charge as a payment.
- V4 read `update.resource_transfers`, which `economy.py:256` clears before the ledger sees it.

The designer ruled that each of V1-V8 gets one real-kernel positive test on rpg's pre-v1 branch (Lane C).

testing-planner ruling, 2026-10-19: this becomes a **standing contract rule**. A validity row is not accepted without a positive test that forces a violation through `build_kernel` (the run path the gate harness uses) and asserts `violations > 0` on the emitted row. A unit-level test that builds the StateUpdate by hand does not count. For example, `test_v8_fires` case (a) uses the real ApplyPath and RunLedger but bypasses the kernel pipeline, which is where V4's blindness was.

**BLOCKED** until rpg's combined pre-v1 fix PR, carrying Lane C's kernel positives, is on main. The lint then lands with every id covered and no allowlist.

## Scope
1. **Format doc** (`rpg_gate_baseline_format.md`, "Required validity rows"): add the rule, and say what counts. It is a test that:
   - runs `build_kernel` for at least one tick with a forced violation;
   - asserts the emitted validity row's `violations > 0`;
   - and, where the row's examples carry an entity id, asserts that an example names the forced entity. Where the examples carry no entity id by design (V2 book totals, V6 coin totals, V7 pooled {way, why}; rpg-planner, 2026-10-20), the test pins the example's key instead. A capped example list may be checked by membership in the forced set (V5).
2. **The map:** a testing-owned map from each validity id to the pytest node ids of its kernel positive tests, for example `tests/simulation_quality/rpg_gate/kernel_positives.yaml`. The values come from rpg (Lane C sends the node ids); the format is testing's.
3. **The lint:** `tests/architecture/test_rpg_gate_validity_rows_have_kernel_positives.py`. It fails when:
   - an id in `config.required_validity` (either level) has no entry;
   - a named node id is not collected (`pytest --collect-only`, or parsing the test module with ast);
   - the named test function does not reach `build_kernel`. The static check is a call to `build_kernel`, or to a helper in the same module that calls it.
   It also fails on a map entry for an id that is not required, a stale entry. Each failure mode has a regression case.
4. **Process:** the format doc says a new V-id PR carries its map entry and its kernel positive together.

## Out of Scope
- Writing rpg's positive tests (Lane C, rpg's).
- Changing any check's logic.
- Outcome rows.

## Acceptance Criteria
- [ ] AC1: the format doc states the rule and what counts as a kernel positive.
- [ ] AC2: the lint passes on main with an entry for every required id (V1-V8), using rpg's node ids.
- [ ] AC3: regression cases. Removing an id's entry, naming a node id that doesn't exist, naming a test that never calls build_kernel, and adding an entry for an id that isn't required each fail the lint.
- [ ] AC4: rpg-planner confirms the map's node ids on the PR (comment link).

## Related Tickets
- TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL (#663)
- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (V8, and case (a) as the unit-level check)
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- (none yet; staging artifacts are the implementer's first step)

## Related Code Areas
- tests/architecture/ (the lint)
- tests/simulation_quality/rpg_gate/ (the map, config.yaml)
- rpg's kernel positive tests (read only)

## Assumptions / Open Questions
- Unblock: rpg's combined pre-v1 PR merges, and rpg sends the node ids per V-id.
- **Node ids from rpg-planner, 2026-10-20** (on rpg-gate-positive-tests 1d27d31b2, then 1571b8810, which goes into rpg-pre-v1-fixes). F = `tests/integration/observability/test_gate_validity_checks_fire_through_the_real_kernel.py`:
  - V1: PENDING (rpg's Lane B is adding it; the ticket stays BLOCKED until rpg sends the id).
  - V2: `F::test_v2_fires_when_a_body_with_meat_decays_and_the_decay_sink_is_silent`
  - V3: `F::test_v3_fires_for_a_starvation_death_beside_an_open_way_even_when_the_dying_entity_had_no_update`
  - V4: `tests/integration/observability/test_v4_counts_a_forbidden_meal_through_the_real_kernel.py::test_a_meat_only_body_that_eats_plant_food_in_a_real_run_is_counted`
  - V5: `F::test_v5_fires_for_an_alive_entity_that_acts_outside_the_world_extent`
  - V6: `F::test_v6_fires_when_an_entity_holds_more_coin_than_the_world_ever_declared`
  - V7 (pooled): `F::test_v7_fires_in_the_pooled_rows_of_real_runs_where_people_never_use_a_declared_way`
  - V8: `F::test_v8_fires_for_an_entity_added_mid_run_with_no_declared_source`
  - Tightened at 1571b8810: V3, V5 and V8 assert that the example names the forced entity (V8 checks the exact [(newcomer_id, apply tick)]). V4's example check is to be confirmed with rpg.
  - Controls (not map entries): the `::test_v2_sink_example_is_absent_...` and `::test_v3_records_one_death_once_...` tests.
  - Implementer: if these tests reach `build_kernel` through a helper imported from another module (not one defined in the same module), widen the static check to follow that one import, or stop and report. Do not allowlist.
- If a check can't be forced through build_kernel in a test-sized run, rpg says so with a reason. That id gets a ruling from testing-planner; it isn't silently skipped.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
