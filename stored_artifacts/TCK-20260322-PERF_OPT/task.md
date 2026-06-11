---
content_type: doc
status: historical
layer: performance
authority: P2
audience: agent
tags: [perf_opt]
---

# Epic 17: Multi-Hero & Permadeath (Phase 2)
- [x] Implement `world_day` properties natively mapping scaled formulas into `models/schemas`.
- [x] Add `raid_interval_days` & `raid_base_strength` parameters to configuration constants.
- [x] Modify `generator.py::spawn_race` to inject `world_age_mult` scalars derived from `world_day`.
- [x] Build a Camp Reinforcement routine iterating local instances on a 500-tick loop.
- [x] Hook Faction `RaidAI` into `CalamitySystem` dispatchers on interval thresholds.
- [x] Verify test suite correctly calculates Day 400 2x stats and automated raid spawning logic.

# Regression Fixes (TCK-20260321-FIXTESTS)
- [x] Fix `Entity.copy()` shallow copy bug (AssertionError in `test_equipment_enhance`).
- [x] Add missing `logging` import in `src/systems/generator.py` (NameError in `test_calamity_system`).
- [x] Stabilize `test_chaos_mode_resilience` termination conditions.
- [x] Initialize E2E production stack (RabbitMQ/Kafka) via Docker and verify `test_message_reliability`.
- [x] Confirm 100% green pass on `pytest tests/ -v`.
- [x] Fix Phase 1 `AttributeError` regressions by updating integration suite accessors.
- [x] Harden RabbitMQ client with 20-attempt connection retry logic (127.0.0.1).
- [x] Harden Kafka client with 20-attempt connection retry logic (127.0.0.1).
- [x] Inject `job: docker` labels in `promtail-config.yml` for unified LogQL queries.
- [x] Inject `job: docker` labels in `promtail-config.yml` for unified LogQL queries.
- [x] Investigate Performance Bottleneck (100% CPU, 0.4 TPS)
    - [x] Profile simulation tick phases using Prometheus metrics
    - [x] Pinpoint `collect` phase and worker dispatch as the bottleneck
    - [x] Audit `Entity.copy()` and `AIBrain.decide` for O(N) complexity issues
    - [x] Benchmark grid serialization and frontier scanning
- [x] Restore Simulation Performance (Restoring TPS > 10)
    - [x] Profile performance using `cProfile` and `profile_tick.py`
    - [x] Identify root causes of 100% CPU usage
    - [x] Implement Grid data structure optimization (`bytearray` + `Material` cache)
    - [x] Implement Entity state copy optimization (`model_copy(deep=False)`)
    - [x] Implement AI Task Batching (Engine <-> Worker communication)
    - [x] Optimize AI Perception scan radius for non-heroes
    - [x] Verify performance restoration using benchmarks and stats
- [x] Verify Performance Restoration
    - [x] Run simulation and monitor TPS (target > 10)
    - [x] Verify CPU usage reduction in `backend` container
    - [x] Ensure AI behavior remains correct after optimizations
- [x] Optimize `test_production_stack.py` with Loki readiness probes and 50s indexing wait.
- [x] Fix directory-agnostic E2E setup in `conftest.py`
- [x] Restore 10MB Kafka message limit and fix `kafka_client.py` syntax
- [x] Resolve `ValueError: 4` in `CalamitySystem` by capping EnemyTier
- [x] Correct `world_day` calculation in backend `/stats` endpoint
- [x] Fix Watchdog recursive failure loop in `watchdog.py`
- [x] Resolve Loki 400 Bad Request by optimizing LogQL matchers
- [x] Verify stable 100% pass rate on core E2E subset
- [x] Unify E2E infrastructure in `conftest.py` with 120s stabilization and directory-agnostic paths.
- [x] Add `docker` stage to Promtail and unify pipelines for `varlogs`.
- [x] Resolve Kafka `InconsistentClusterIdException` in `conftest.py`
- [x] Increase RabbitMQ/Kafka retry windows to 120s for host-side resilience.
- [x] Achieve 100% Green Suite Pass.
