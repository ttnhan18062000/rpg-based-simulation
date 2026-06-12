---
status: historical
layer: testing
authority: P2
audience: developer
---

# Phase 10 — Optimization / Scaling / Rollout Hardening Coverage

This document outlines the test coverage matrix for Phase 10, distinguishing existing stability, stress, and API health checks from the new feature-specific scaling, budgeting, and rollout gates.

## Existing Coverage (Do Not Duplicate)

- **Long-Run Pure/Runtime Stability**: Verifies memory stability and engine ticks over extended iterations (10k+ ticks).
- **Determinism Parity**: Ensures standard replay determinism using state hashes.
- **Arena 50v50 Stress**: Verifies thread safety and baseline combat scaling under high entity density.
- **Envelope Violations & Observability Parity**: Checks validation bounds and logging schemas.
- **API Live Health/Websocket**: Tests API routes and websocket subscriber limits under normal execution.

## New Phase 10 Coverage (Feature-Budget & Rollout Safety)

- **Feature Flag Rollout Behavior**: Toggling phases between `OFF`, `SHADOW`, `ON`, and `STRICT` modes.
  - Test File: [test_phase10_feature_flags.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/config/test_phase10_feature_flags.py)
  - Profile Toggling: [test_phase10_rollout_profiles.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/config/test_phase10_rollout_profiles.py)
- **Phase Budget Enforcement**: Restricting tick ms, processed entities, provider calls, and results.
  - Test File: [test_phase10_phase_budget_manager.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/perf/test_phase10_phase_budget_manager.py)
- **Dirty-Work Scheduler**: Skipping unchanged entities and regions.
  - Test File: [test_phase10_dirty_work_scheduler.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/perf/test_phase10_dirty_work_scheduler.py)
- **Provider Scoped Query & Capping**: Restricting and deterministic ordering of provider calls.
  - Test File: [test_phase10_provider_budget_enforcement.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/world/providers/test_phase10_provider_budget_enforcement.py)
- **Cache Invalidation Correctness**: Cache TTL and event-driven invalidation.
  - Test File: [test_phase10_cache_invalidation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/perf/test_phase10_cache_invalidation.py)
- **Trace/Event Volume Governor**: Capping low-severity logs and event summarization.
  - Test File: [test_phase10_trace_volume_governor.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/test_phase10_trace_volume_governor.py)
- **Memory Capacity Hard Limits**: Deterministic eviction of low-salience knowledge, trusts, and coop memory.
  - Test File: [test_phase10_memory_capacity_limits.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/perf/test_phase10_memory_capacity_limits.py)
- **Graceful Degradation Levels**: Transitioning through `NORMAL` -> `CONSTRAINED` -> `DEGRADED` -> `CRITICAL`.
  - Test File: [test_phase10_graceful_degradation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/perf/test_phase10_graceful_degradation.py)
- **Developer Diagnostics**: Budget skips and blocker loops reporting.
  - Test File: [test_phase10_developer_diagnostics.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/diagnostics/test_phase10_developer_diagnostics.py)
- **Combined Phase Overhead (Phases 1-9)**: Integrated scenarios.
  - Test File: [test_phase10_integrated_enhanced_stack_budget.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/perf/test_phase10_integrated_enhanced_stack_budget.py)
- **Determinism Parity**: Ensuring shadow and strict mode execution are deterministic.
  - Test File: [test_phase10_enhanced_determinism_parity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/certification/test_phase10_enhanced_determinism_parity.py)
- **Rollout Gate Checks**: Performance, determinism, and semantic verification gate.
  - Test File: [test_phase10_enhanced_rollout_gate.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/certification/test_phase10_enhanced_rollout_gate.py)

