---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# Test Plan: TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP

Shared test file with the sibling ticket: `tests/unit/observability/test_event_shapers_agency.py`
(16 tests total). This ticket's own `rejection_cascade_tick`-half tests:

| Test | Behavior verified |
|---|---|
| `test_rejection_cascade_tick_emitted_above_threshold` | Correct emission at/above `_MAX_CONSECUTIVE_REJECTIONS`, correct payload (`count`, `dominant_failure_reason`) |
| `test_rejection_cascade_tick_not_emitted_below_threshold` | Below threshold suppressed |
| `test_rejection_cascade_tick_not_emitted_when_all_accepted` | No rejections → no event |
| `test_rejection_cascade_tick_aggregates_across_entities` | Population aggregate, not per-entity |
| `test_rejection_cascade_tick_does_not_need_prior_state_entities` | Pure `update`-only — fires even with empty `prior_state.entities` |

Registry/flag-gating tests (`test_agency_registry_contains_agency_shaper` through
`test_agency_shaper_independent_of_quest_flag`) are shared with the sibling ticket — see its own
`test_plan.md`.

## Regression coverage
`tests/unit/observability/` full suite (952 tests), `tests/unit/config/test_phase10_feature_flags.py`,
`tests/simulation_quality/` (excluding the pre-existing unrelated `test_grade_regression.py`).

## Real-kernel-adjacent verification
Real `EntityUpdate` with 25 rejected `IntentResult`s (above the real threshold of 20): default
delivers exactly 1 `rejection_cascade_tick` from the shaper with the correct payload (0 from
extractor); explicit OFF delivers exactly 1 from the extractor (0 from shaper). Caught and
corrected an initial verification mistake (10 rejections, below the real threshold, which the
`_MAX_CONSECUTIVE_REJECTIONS` constant confirmed is `20` not an assumed smaller value) before
relying on the result.

## Results
`tests/unit/observability/test_event_shapers_agency.py`: 16/16 pass. Full
`tests/unit/observability/`: 952/952 pass. `tests/unit/config/test_phase10_feature_flags.py`:
7/7 pass. `tests/simulation_quality/` (excluding `test_grade_regression.py`): 1419 pass (combined
sweep with sibling ticket).
