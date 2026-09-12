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

## CI caught a real regression before merge: a fixture that only worked by accident

`gh pr checks` failed `Integration` on the first push. Triaged per standing discipline (pulled
annotations, then reproduced the exact CI command locally rather than assuming transient) — it
reproduced locally too: `tests/integration/kernel/test_substrate_freeze_m1.py::
TestSubstrateFreezeM1::test_apply_path_singular_authority` failed with
`TypeError: '>=' not supported between instances of 'float' and 'MagicMock'`.

Root cause: this test's own `mock_kernel_deps` fixture builds a `MagicMock()` `RuntimeProfile`
with `max_worker_count=0` — the exact worker-disabled case this ticket's fix targets — but never
sets `profile.degradation_threshold_ram`. Before the fix, `worker_utilization=1.0` satisfied
`ResourceGovernor._get_indicated_mode()`'s `>= 0.9` check and returned `DEGRADED` immediately,
never reaching the later `CONSTRAINED`-branch comparison that reads `degradation_threshold_ram`.
The fixture's own gap was real but invisible, masked by the exact bug this ticket fixes. With
`worker_utilization=0.0` now correctly reported, evaluation proceeds further and the gap surfaces.

Fixing that alone exposed a second, cascaded gap: `GovernorPolicy.from_mode(RuntimeMode.NORMAL)`
enables full replay (`DEGRADED` did not), so `Kernel._phase_persistence()` now actually calls
`CanonicalStateHasher.get_hash()` on the tick's own state — which it never did under the old,
incorrectly-DEGRADED mode — and that touches the fixture's own bare `rng = MagicMock()`, which
isn't JSON-serializable.

Both are real, evidenced consequences of this fix correctly reaching code paths the bug had been
hiding, not unrelated flakes. Fixed at the root, not papered over: added
`profile.degradation_threshold_ram = 0.85` (`RuntimeProfile`'s own real default,
`src/config/profiles.py:47`) and replaced the bare `MagicMock()` rng with a real
`DeterministicRNG(42)`, matching the pattern already used by other real-`Kernel` tests in this
repo (e.g. `tests/unit/kernel/test_grief_trigger_drain.py`). Re-ran the full local `tests/
integration` suite before pushing again: 968 passed, 0 failed.

**Larger implication, worth reading before bisecting any further fallout from this fix.** If the
sentinel forced `DEGRADED` every tick for every `max_worker_count<=0` run, then `ScanPolicy.
EXACT_DIRTY` was always the scan policy and the governor was always shedding work in that mode —
in tests *and* in real runs, for however long this bug existed. An unknown number of code paths
downstream of `RuntimeMode.NORMAL`/`CONSTRAINED` (full replay, un-shed scan policies, anything
gated on *not* being in `DEGRADED`) have never executed under any observation made against a
worker-disabled run. This fixture is the first instance found — there will likely be more. **The
default hypothesis for any further failure surfacing after this fix is that the code path was
always broken and simply never reached, not that this fix broke it** — the same relationship
`TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`'s own count-expansion fix had
to the real `ActionIntent` crash it exposed earlier in this arc. Verify that per-instance rather
than assuming it, but start there before hunting.
