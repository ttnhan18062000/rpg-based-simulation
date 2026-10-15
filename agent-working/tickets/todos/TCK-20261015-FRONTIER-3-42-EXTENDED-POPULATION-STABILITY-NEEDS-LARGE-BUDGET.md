---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261015-FRONTIER-3-42-EXTENDED-POPULATION-STABILITY-NEEDS-LARGE-BUDGET
phase: open
date: 2026-10-15
tags: [testing]
---

# TCK-20261015-FRONTIER-3-42-EXTENDED-POPULATION-STABILITY-NEEDS-LARGE-BUDGET

## Title
Mark `test_generated_frontier_3_42_extended_population_stability` `resource_budget_large`, like the other 1000t tests in the file

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
rpg-implementer found (relayed by rpg-planner, 2026-10-15) that `tests/unit/worldassembly/test_corpus_diversity.py::test_generated_frontier_3_42_extended_population_stability` (tick 1000) is marked only `@pytest.mark.slow`. conftest's default `medium` budget (60 s) kills a bare local run. The test needs 270-350 s and passes with `--resource-budget off`.

CI is not affected. `make simq-corpus-diversity-slow-isolated` already passes `--resource-budget large` for every node. Only local runs without that flag time out.

Every other 1000t guard in the same file carries `@pytest.mark.slow` plus `@pytest.mark.resource_budget_large` (e.g. `test_simq_routing_test_seed42_1000t_cognition_grade_stability`). This test is the one that was missed. testing-planner chose `resource_budget_large` over `extra_slow`: it keeps the test under `-m slow`, so the isolated target's `-m slow` collection (the >=32 guard) and CI selection are unchanged.

## Scope
1. Add `@pytest.mark.resource_budget_large` to `test_generated_frontier_3_42_extended_population_stability`, keeping `@pytest.mark.slow`.

## Out of Scope
- The test's known-red entry in `tools/test_architecture/slow_known_reds.yaml` (throttled kernel by design plus the run-dir collision, under TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2). A timeout is a different failure from what that entry describes, and the entry stays as it is.
- Any assertion, tick count or anchor value.
- Other tests' markers.

## Acceptance Criteria
- [ ] AC1: the test carries `slow` and `resource_budget_large`, and nothing else changes in the file.
- [ ] AC2: `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --collect-only -q` collects the same node count before and after (>=32).
- [ ] AC3: a bare local run (`pytest <nodeid>`, no `--resource-budget`) is no longer killed by the 60 s budget. Record its result (pass, or the same known-red failure) and wall time in Test Summary. A failure other than the budget kill is reported, not fixed here.

## Related Tickets
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (owns the known-red entry)
- TCK-20261006-EXTRA-SLOW-TESTS-LOCAL-RESOURCE-BUDGET (the conftest rule)
- TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION (introduced `resource_budget_large`)

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py
- tests/conftest.py (budget selection, read-only here)

## Assumptions / Open Questions
- None. Owner's ruling (testing-planner) is in the Request Summary.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
