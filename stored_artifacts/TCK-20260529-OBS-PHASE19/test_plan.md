---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260529-OBS-PHASE19
artifact_type: test_plan
tags: [obs, phase19]
---

# Test Plan - TCK-20260529-OBS-PHASE19

We will implement three sets of test suites to fully verify the requirements of Phase 19:

## 1. Config & Feature Flags Unit Tests
Location: `tests/unit/config/test_phase19_observability_feature_flags.py`
Verify:
- Default values for each preset mode (e.g. `OFF` disables most flags, `LIGHT` enables profiling, `DEBUG` enables all flags).
- Direct environment overrides for each flag (e.g., `RPG_OBS_BEHAVIOR_EPISODES=true` works regardless of the active preset).
- Programmatic direct overrides via a new thread-safe override method `ObservabilityConfig.set_flag_override(flag, value)`.
- Integration of preset modes with existing `set_override_mode(...)`.

## 2. Observability Boundaries Test
Location: `tests/architecture/test_phase19_observability_boundaries.py`
Verify:
- The architectural boundary document `docs/architecture/observability_behavior_profiling_boundary.md` exists and contains defined terminology.
- No heavy post-run analysis files (e.g., in `src/observability/anomaly/`, `src/observability/cognition/`, `src/observability/reporting/`) are imported by the simulation loop / engine hot path (e.g., `src/engine/`, `src/observability/config.py`, `src/observability/event_extractor.py`).

## 3. Hot-Path Safety Contract Test
Location: `tests/architecture/test_phase19_hot_path_safety_contract.py`
Verify:
- The safety contract document `docs/architecture/observability_hot_path_safety_contract.md` exists.
- The hot-path classes do not perform expensive/blocking methods or import post-run code.
