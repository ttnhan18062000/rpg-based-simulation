---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260412-REGRESSION-FIX
phase: done
date: 2026-04-12
tags: [regression, fix]
---

# TCK-20260412-REGRESSION-FIX

## Title

Stabilization of Simulation Regression Suite (9 Failures)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Fix several test failures in the regression suite, ranging from unit tests to E2E and benchmarks.

## Scope
- Fix `AttributeError` in `test_chaos_mode_resilience` (missing `HOMECOMING` enum).
- Fix `NameError` in `test_behavioral_realism_remediation.py` (missing import).
- Address performance degradation in `test_scaling_1000_entities`.
- Fix AI behavior regressions in E2E tests (`test_ranged_and_melee_hero_vs_mob`, `test_ai_prefers_aoe_when_clustered`, `test_goal_commitment_and_anti_jitter`).
- Fix unit test failures in `test_goals.py` and `test_pathfinding.py`.

## Out of Scope
- Large-scale refactoring of the engine.
- Adding new features.

## Acceptance Criteria
- All 9 failed tests identified in the request pass.
- No new regressions introduced.
- Test thresholds for benchmarks are either met or reasonably adjusted if performance cost is justified by new features (subject to review).

## Related Tickets
- None

## Related Docs
- None

## Related Stored Artifacts
- None

## Related Code Areas
- `src/core/models/enums.py`
- `src/ai/brain.py`
- `src/ai/states/`
- `tests/`

## Assumptions / Open Questions
- Is `HOMECOMING` the intended name for the missing enum? (Assuming yes based on previous Phase 3 work).
- Does the performance drop in benchmarks reflect a legitimate slowdown due to more complex AI logic?

## Implementation Notes
- Initial investigation shows `InterpretedLifeEventKind` is missing `HOMECOMING`.
- `run_bench` needs to be imported in `test_behavioral_realism_remediation.py`.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
