---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-BROKER-CONFIG
phase: open
date: 2026-07-02
tags: [observability, simulation-quality, broker-mode, redis, configuration, kernel]
---

# TCK-20260702-OBSISO-BROKER-CONFIG

## Title
Unify broker-mode stream configuration and fix kernel feed routing

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Broker mode is silently dead out-of-box: the producer publishes to `simulation:events` (`ObservabilityConfig.get_stream_name()`, env `SIM_STREAM_NAME`/`RPG_STREAM_NAME`, default in `src/observability/config.py:336-338`) while the consumers default to `sim:events` (`BrokerQualityFeed` in `src/simulation_quality/feed.py:61,133` and `QualityWorker` in `src/simulation_quality/worker.py:73`, env `QUALITY_STREAM_NAME`). Additionally, `Kernel` calls `build_feed_from_env()` at init (`src/engine/kernel.py:232-233`) and starts the resulting feed against an in-engine hub — in broker mode this appears to start a Redis consumer thread *inside the engine process*, so scoring runs in-engine anyway (defeating isolation) and may double-consume alongside an external worker. Verify and fix.

## Scope
- Single source of truth for stream identity: SimQ consumers resolve the stream name (and Redis URL) through `ObservabilityConfig` (or a shared constant it owns) instead of independent `QUALITY_*` defaults. Keep `QUALITY_STREAM_NAME`/`QUALITY_BROKER_URL` as explicit overrides but default them to the `ObservabilityConfig` values.
- Kernel mode routing: when `QUALITY_FEED_MODE=broker`, the engine must not construct a `QualityHub` or start any consumer thread — it only publishes (stream adapter already handles that). `build_feed_from_env()` result handling in `kernel.py` adjusted accordingly; in-process mode behavior unchanged. Investigate the exact current wiring around `kernel.py:225-270` first — the fix must match how `_quality_feed`/`_quality_hub` are used downstream (persistence, report generation).
- Startup diagnosability: worker logs the resolved (url, stream, group) triple at INFO on start; if the stream does not exist or has no recent entries after N seconds, log a WARNING naming the producer-side env vars (this is the failure that was previously silent).
- Docs: update `docs/guides/simulation_quality.md` "Feed modes" section with the unified config table (all env vars, defaults, which process reads which) and a broker-mode quickstart (engine env + worker command).
- Parity ledger: add/update `docs/parity_ledger/infrastructure.yaml` entry for broker-mode config resolution.

## Out of Scope
- Scorer completeness in the worker (TCK-20260702-OBSISO-WORKER-PARITY)
- Performance measurement (TCK-20260702-OBSISO-ISOLATION-PROOF)
- New stream backends

## Acceptance Criteria
- With **no** `QUALITY_*`/`SIM_STREAM_*` env vars set and `QUALITY_FEED_MODE=broker` + `SIM_STREAM_BACKEND=redis`: events published by a run are consumed by `QualityWorker` (integration test with fakeredis or a marked `slow`/`requires-redis` test, following the existing pattern in `tests/simulation_quality/test_broker_feed_integration.py`).
- In broker mode, the engine process starts zero SimQ scorer objects and zero Redis consumer threads (assert via thread names / hub absence).
- In-process mode: `tests/simulation_quality/test_kernel_simq_integration.py` and `test_feed.py` pass unchanged.
- `QUALITY_SCORING_DISABLED=1` still disables everything in both modes.
- Config docs list every env var with its default and owning process.

## Related Tickets
TCK-20260630-SIMQ-WIRE-KERNEL (in-process wiring), TCK-20260520-SIM-OBS-M36 (RedisStreamAdapter/Consumer), TCK-20260702-OBSISO-EPIC

## Related Docs
docs/plans/observability_process_isolation.md (G1, G3), docs/guides/simulation_quality.md (Feed modes), docs/engine/contracts/infrastructure_compat_contract.md

## Related Stored Artifacts
stored_artifacts/TCK-20260630-SIMQ-WIRE-KERNEL* (if present)

## Related Code Areas
src/observability/config.py (get_stream_backend/get_redis_url/get_stream_name), src/simulation_quality/feed.py (build_feed_from_env, BrokerQualityFeed), src/simulation_quality/worker.py, src/engine/kernel.py:225-270, src/observability/stream/factory.py

## Assumptions / Open Questions
- Assumption: aligning consumer defaults onto `ObservabilityConfig` is preferred over renaming the producer stream (producer default is older and documented). 
- Open: in broker mode, who writes `quality_scores.jsonl` into the run dir the engine owns? Worker uses `QUALITY_RUN_DIR` — decide whether the worker's run_dir should be pointed at the engine's run dir or kept separate; document the decision.

## Implementation Notes
Kernel must remain importable and runnable with `redis` package absent (infrastructure compat contract) — all changes stay behind the existing graceful-degradation paths.

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
