---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-SIMQ-NARRATIVE-ANCHOR-RECALIBRATION-FRONTIER-BATCH
tags: [simulation-quality, calibration, testing, bug]
---

# Test Plan — TCK-20260817-STANDARD-SIMQ-NARRATIVE-ANCHOR-RECALIBRATION-FRONTIER-BATCH

## Commands and results

Post-fix, batch run (isolated, one test at a time):
```
test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability   FAILED (COMBAT, first attempt, before co-discovered fix)
test_frontier_extended_seed42_200t_narrative_grade_stability                 1 passed in 21.29s
test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability  1 passed in 24.33s
test_frontier_living_world_seed123_200t_combat_narrative_grade_stability     1 passed in 28.02s
test_frontier_marches_seed42_200t_narrative_grade_stability                  1 passed in 23.80s
```

Test 1's COMBAT co-discovery investigated and fixed (see investigation.md), then re-verified
across 3 consecutive isolated runs:
```
run 1: 1 passed in 17.36s
run 2: 1 passed in 17.43s
run 3: 1 passed in 17.59s
```

## Regression check
No `src/` file changed. Only the `NARRATIVE` anchor entry (5 tests) and `COMBAT` anchor entry
(test 1 only) were edited, plus `frontier_marches_seed42_200t`'s docstring trim — verified via
`git diff` review that no other pillar's anchor or any other test was touched.

## Final status
All 5 tests pass reliably under isolated execution, matching CI's real invocation pattern for
this suite.
