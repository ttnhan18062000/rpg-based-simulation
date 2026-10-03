---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260529-OBS-PHASE22-BEHAVIOR-NORMALIZATION
artifact_type: test_plan
tags: [obs, phase22, behavior, normalization]
---

# Test Plan — Phase 22 + Phase 28 Initial Guard

## Scope

- Phase 22: BehaviorEvent model, BehaviorEventNormalizer, BehaviorWorker
- Phase 28 initial: ObservabilityBudgetProfile, queue degradation, worker failure

## Unit Tests

| File | Tests | Coverage |
|------|-------|---------|
| test_phase22_behavior_event_model.py | 12 | BehaviorEvent fields, immutability, JSON roundtrip, taxonomy |
| test_phase22_behavior_event_normalizer.py | 18 | All event type mappings, determinism, unknown handling, batch |
| test_phase28_observability_budget_profile.py | 9 | Budget profile fields, presets, enums |

## Integration Tests

| File | Tests | Coverage |
|------|-------|---------|
| test_phase22_behavior_worker_from_jsonl.py | 9 | JSONL processing, artifact writing, corruption tolerance, failure isolation |
| test_phase22_behavior_worker_from_stream.py | 5 | Queue drain, failure isolation, clean stop, non-blocking |
| test_phase28_observability_degradation.py | 5 | Queue full non-blocking, critical event protection, dropped count, engine isolation |

## Results

All 77 tests pass (Phases 19–22 + 28 initial guard).
