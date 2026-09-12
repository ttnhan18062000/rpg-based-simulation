# Investigation — TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER

## Fix layer decision: `WorkerManager.get_stats()`'s own sentinel, not `ResourceGovernor`

The ticket's own Scope left this open: fix `WorkerManager.get_stats()`'s sentinel value, or make
`ResourceGovernor._get_indicated_mode()` skip the `worker_utilization` check when
`profile.max_worker_count <= 0`.

Grepped every real consumer of `worker_utilization` (`src/`, non-test) before deciding:
`src/certification/{models,harness,recorder}.py`, `src/engine/{observability,kernel}.py`,
`src/api/engine_manager.py`, `src/observability/prometheus_collector.py`, `src/observability/
reporting/metric_recorder.py`, `src/observability/live/snapshot_provider.py`,
`src/core/governance.py` — **all of these display, log, or record the value; none of them branch
on it.** `ResourceGovernor._get_indicated_mode()` (`governor.py:88,96,139`) is the *only* real
consumer that makes a decision based on it.

This settles the layer question in favor of the sentinel fix: a governor-only special-case would
leave every one of those other consumers still reporting "100% worker utilization" on a run where
workers are deliberately disabled and zero are active — misleading in every one of those contexts,
not just the governor's. Fixing the source value at `WorkerManager.get_stats()` corrects it
everywhere at once, and is strictly more correct for every consumer, not a special case for one.

## Confirming this doesn't mask a real signal

The ticket's own Scope asked: does any other pressure signal already cover real compute pressure
independently when workers are disabled? Read `ResourceGovernor._get_indicated_mode()`
(`governor.py:75-101`) in full: `work_debt_total`, `tick_compute_ms`, and `memory_estimate_mb` are
all independent of worker-pool state — they measure the kernel's own per-tick wall-clock compute
time, accumulated work debt, and memory, none of which depend on whether worker threads exist.
A real overload in worker-disabled (synchronous) mode would still surface via these signals and
correctly escalate `DEGRADED`/`SURVIVAL`. `worker_utilization=0.0` cannot mask a real overload —
it only stops falsely reporting one that doesn't exist.

## Real reproduction, before and after

Built a real, uninstrumented `Kernel` (not a synthetic `PressureSignals` unit test) with
`RuntimeProfile(max_worker_count=0)`, matching `ScenarioRuntimeService`'s own real construction,
and ran 5 real ticks against an empty world:

**Before the fix**: `mode=2` (`RuntimeMode.DEGRADED`) on every tick, confirming the mis-trigger
exactly as the ticket described — no organic pressure story, pure sentinel artifact.

**After the fix**: `mode=0` (`RuntimeMode.NORMAL`) on every tick, same profile, same scenario.

## Normal-case regression check

Confirmed the `max_workers > 0` case is unaffected: a real `WorkerManager(max_workers=2)` run,
saturating both workers simultaneously via a real thread barrier (not mocked), still reports
`worker_utilization == 1.0` — genuine saturation is still reported accurately, not silently zeroed.

## All 3 real call sites re-confirmed governed correctly

- `ScenarioRuntimeService` (`scenario_runtime.py:395`): `tests/unit/engine/
  test_scenario_runtime_service.py` — 41 passed, 1 skipped.
- `ScenarioCheckpointer` (`scenario_checkpoint.py:94`): `tests/unit/engine/
  test_scenario_checkpointer.py` — same run, included above.
- `BROKER_DISABLED=1` (`config/loader.py:74`): `tests/cli/test_infra_isolation.py` — 4 passed.

## Sibling sentinel (`queue_utilization`) — not touched, per the ticket's own prior finding

The ticket's own Request Summary already confirmed `queue_utilization`'s identical `<=0 → 1.0`
branch is structurally unreachable (`RuntimeProfile.max_queue_depth` is Pydantic `Field(..., gt=0)`,
and every real construction site passes a real positive value) — re-verified this claim holds
(no new `max_queue_depth=` construction sites introduced since the ticket was filed) and left it
untouched, per the ticket's own explicit Scope note.
