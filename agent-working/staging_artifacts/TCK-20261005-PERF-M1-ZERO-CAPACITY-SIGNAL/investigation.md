---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL
date: 2026-10-05
tags: [performance, determinism, testing]
---

# Investigation: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL

## Findings (live code, 2026-10-05)
- `WorkerManager.__init__` (`src/engine/worker_manager.py:56`) accepts any ints. With
  `max_workers >= 1` and `max_queue_depth <= 0` every chunk satisfies `q_depth >= max_queue_depth`
  and is forced local; `get_stats()` reports queue utilization `1.0` (`:242-245`), which
  `ResourceGovernor._get_indicated_mode()` reads as saturation (`>= 0.9` -> DEGRADED).
- Worker half already fixed 2026-09-13 (`bc00caa1a`, PR #175): zero workers reports `0.0`.
- **Reachability: the planner's claim holds.** The only `WorkerManager(` in `src/` is
  `src/engine/kernel.py:133`, fed by `RuntimeProfile.max_worker_count` / `max_queue_depth`;
  `src/config/profiles.py:30` declares `max_queue_depth` `gt=0`. The other four callers the
  ticket names (`campaigns/runner.py`, `scenario_checkpoint.py`, `scenario_runtime.py`,
  `observability/readiness/harness.py`) do not construct it; they reach it through the kernel
  and a profile (`make_perf_profile`, default `queue_depth=1000`). The queue half is latent.
  No test or tool constructs a manager with a zero or negative queue or worker count.
- **"Unavailable":** no such state. After `shutdown()` `_pool` is `None`, `execute_batch` runs
  locally and `get_stats()` still reports normal values; process-pool small-batch fallback is
  also local execution. Neither is encoded as a utilization value. Finding: not signalled today,
  and no typed field is added (ticket scope 2).
- Negative inputs today: `max_workers < 0` behaves as disabled (`> 0` guard); `max_queue_depth < 0`
  behaves as zero. Decision: reject both (`ValueError`) rather than clamp silently.

## Baseline disposition inputs
- `PERF_*_LOCAL` profiles use `workers=0`; `PERF_*_CONC` use 4 workers, queue 1000.
- Worker fix landed 2026-09-13. Committed baselines were captured 2026-05-15 (`tests/perf/baselines/`)
  and 2026-05-19 (`docs/observability/baselines/`), so every `*_local` capture ran the old
  worker sentinel, DEGRADED from tick 1. `perf_baselines.json` has zero entries.
- `docs/observability/baselines/latest.json` profile shape is still to be read (see plan step 6).

## Added during implementation (2026-10-05)
- Finding: local fallback (`_execute_locally` -> `_wrap_work`) counted caller-thread execution as an
  active worker. workers=1, queue=1, 200 packets: `worker_utilization` 2.0 (`peak_workers` 2);
  4-worker manager after `shutdown()` doing only local work: 0.25. Violates PERF-D1 (saturated 1.0).
- Decision (perf-planner, 2026-10-05): fix in T01 by not counting local execution as active, no clamp.
  `_wrap_work(pooled=...)`. After: 1.0 and 0.0.
- Governor guard rail: overloaded run reaches DEGRADED before (2.0) and after (1.0); governor.py unchanged.
- No committed baseline file contains a utilization value, so the miscount left no stored trace.
- `latest.json` profiles: IDLE/MOVEMENT/RESOURCE/COMBAT/STRATEGIC rows are `PERF_*_LOCAL`, MIXED_1000 is
  `PERF_4GB_CONC`. Disposition table is in the ticket's Implementation Notes.
- `tests/regression/test_behavioral_5k.py` times out at the 60 s conftest limit here (environmental).
