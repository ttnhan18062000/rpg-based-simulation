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
   - and, where the row has examples, asserts that an example names the forced entity or transfer.
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
- If a check can't be forced through build_kernel in a test-sized run, rpg says so with a reason. That id gets a ruling from testing-planner; it isn't silently skipped.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
