# Plan — TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER

## Disposition
Fix at `WorkerManager.get_stats()`'s own sentinel layer — the only consumer that decides anything
based on `worker_utilization` is `ResourceGovernor`, but every other real consumer (dashboards,
metrics, certification reports) also displays this value, so fixing the source is strictly more
correct than a governor-only special case. Change the `max_workers<=0` sentinel from `1.0` to
`0.0`. Confirmed via real Kernel reproduction (before: DEGRADED every tick; after: NORMAL every
tick) and confirmed no other pressure signal is masked (tick_compute_ms/work_debt_total/
memory_estimate_mb remain independent, real coverage).

## Steps
1. Change `WorkerManager.get_stats()`'s `worker_utilization` sentinel from `1.0` to `0.0` when
   `self._max_workers <= 0`.
2. Add unit coverage: `get_stats()` returns `0.0` when disabled; confirm the normal
   (`max_workers > 0`) real-saturation case is unregressed via a real thread-barrier test.
3. Add the ticket's own required real, uninstrumented multi-tick Kernel test: `max_worker_count=0`
   profile, empty world, confirm `RuntimeMode.NORMAL` holds across 5 real ticks.
4. Re-run tests for all 3 real call sites (`ScenarioRuntimeService`, `ScenarioCheckpointer`,
   `BROKER_DISABLED=1`) to confirm still correctly governed.
5. Leave `queue_utilization`'s identical-shaped sentinel untouched — re-confirmed structurally
   unreachable, per the ticket's own explicit Scope note.

## Guardrails
- Do not touch `queue_utilization`'s own sentinel — confirmed structurally unreachable by Pydantic
  validation, not this ticket's to fix.
- Do not change `ResourceGovernor`'s own escalation/recovery/dwell-time logic — only the
  `WorkerManager` input value.
- Preserve the exact `self._max_workers > 0` condition already used for pool initialization —
  same guard, same semantics, just a different false-branch value.
