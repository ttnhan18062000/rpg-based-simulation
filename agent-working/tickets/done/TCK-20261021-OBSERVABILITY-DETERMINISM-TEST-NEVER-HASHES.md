---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261021-OBSERVABILITY-DETERMINISM-TEST-NEVER-HASHES
phase: done
date: 2026-10-21
tags: []
---

# TCK-20261021-OBSERVABILITY-DETERMINISM-TEST-NEVER-HASHES

## Title
test_phase28_observability_determinism is named "same authoritative hash" but only toggles the observability mode and never compares a hash

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Lead-planner-u24's read-only pass on origin/main (2026-10-21): the test is named for the same authoritative hash across observability modes, but it only toggles the mode and never hashes. This is a test-strength gap. Testing-planner was copied and may take it; tests/integration is rpg-planner's path, so either lane can do it with the other's OK. After v1.

## Scope
- Use testing-planner's suggested shape. Run the same world and seed through build_kernel for N ticks, under OFF and under FULL.
- Assert that the final authoritative state hash is identical, using the existing hash helper.
- Add a mutation check: make one mode write authoritative state, and the test goes red.
- Keep the test's name, so the frozen-name rule holds if it applies.
- Testing-planner reviews the test on the PR.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The test fails if an observability mode changes authoritative state.
- It passes on main.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- tests/integration/observability/test_phase28_observability_determinism.py

## Assumptions / Open Questions
- Confirmed on origin/main by testing-planner (2026-10-21). test_observability_off_and_full_have_same_authoritative_hash only flips ObservabilityConfig OFF -> FULL and asserts get_mode(). It never runs the kernel and never computes a hash.
- It is cited as determinism evidence in docs/simulation_quality/quality_scoring_contract.md:1217 and docs/testing/observability_coverage.md:85. Check whether any parity-ledger entry leans on it; testing found none by name.

## Implementation Notes
- The test now runs WORLD frontier_living_world, seed 42, 100 ticks through `build_kernel` (pinned governor, sequential executor, audit mode) under OFF and under FULL and compares `CanonicalStateHasher.get_hash` of the final state. The name `test_observability_off_and_full_have_same_authoritative_hash` is kept.
- Non-vacuity: it also asserts FULL wrote `simulation_events.jsonl` and OFF did not, so the two modes really differ in what they record.
- Mutation check (`test_the_comparison_catches_an_observability_mode_that_writes_authoritative_state`): a FULL run that advances `state.tick` after every tick (an observability path writing authoritative state) gets a different hash from OFF. It is a self-test of the comparison's power, not a production-code mutation: the repository has no switch that makes a mode write state.
- FULL and OFF hashes are equal on main (735a1c635): no determinism finding.
- Not changed: docs/simulation_quality/quality_scoring_contract.md:1217 and docs/testing/observability_coverage.md:85 cite the test as determinism evidence; they are now true. No parity-ledger entry cites it by name (grep).

## Test Summary
2 passed in 23 s, serial, peak RSS 164 MB. Hash equality OFF vs FULL on frontier_living_world seed 42, 100 ticks.

## Files Changed
tests/integration/observability/test_phase28_observability_determinism.py

## Completion Summary
The determinism test now hashes: OFF and FULL give the same final authoritative hash, and a state-writing mode is caught. Test-only.
