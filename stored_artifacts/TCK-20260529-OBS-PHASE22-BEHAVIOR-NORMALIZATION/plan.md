# Phase 22 + Phase 28 Initial Guard — Implementation Plan

## Goal

Implement Phase 22 (Async Behavior Normalization Worker) and the Phase 28 initial
safety guard (queue full, worker failure isolation, OFF/ON determinism) per the
`entity_enhance_phase19_28.md` roadmap.

## Files Created

### src/observability/behavior/

- `__init__.py` — package init
- `behavior_event.py` — `BehaviorEvent` frozen dataclass with taxonomy, JSON serialization
- `normalization_context.py` — minimal `BehaviorNormalizationContext`
- `normalizer.py` — `BehaviorEventNormalizer` with event-to-category routing
- `worker.py` — `BehaviorWorker` (post-run JSONL + queue drain modes)

### src/observability/budget/

- `__init__.py` — package init
- `budget_profile.py` — `ObservabilityBudgetProfile`, `SamplingPolicy`, `DegradationLevel`, presets

### Tests

- `tests/unit/observability/behavior/test_phase22_behavior_event_model.py` (12 tests)
- `tests/unit/observability/behavior/test_phase22_behavior_event_normalizer.py` (18 tests)
- `tests/unit/observability/budget/test_phase28_observability_budget_profile.py` (9 tests)
- `tests/integration/observability/test_phase22_behavior_worker_from_jsonl.py` (9 tests)
- `tests/integration/observability/test_phase22_behavior_worker_from_stream.py` (5 tests)
- `tests/integration/observability/test_phase28_observability_degradation.py` (5 tests)

## Test Results

- All 77 tests pass (Phase 19, 20, 21, 22, 28 initial guard)
- Zero regressions
