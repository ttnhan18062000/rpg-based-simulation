---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS
date: 2026-10-07
tags: [performance, determinism, engine]
---

# Investigation: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS

Read-only. Tree: `main` at 33588b966 plus the planning commit. No `src/` file was edited.

## Verdict
Confirmed, and wider than the ticket says. In shipped runs `DeterministicScheduler.select_work` can shed nothing, and
three of the four rungs of the documented shedding waterfall (diagnostic verbosity, opportunistic work, non-authoritative
periodic work) have no effect at all. Degradation still works through other levers (phase budgets, cadence, concurrency,
replay richness, traces). The planner's assumption that nothing registers periodic work dynamically holds.

## Scope 1: what defines, documents or tests sheddable work

### Definitions in `src/`
- `src/engine/scheduler.py:14-22` `PeriodicDefinition` (`is_authoritative: bool = True`). `:30-31` the constructor builds
  `_periodic_defs` from its argument and nothing else ever writes to it (no `register`/`add` method, no other assignment).
- `src/engine/scheduler.py:102-105` the only shedding line: a non-authoritative definition is skipped and `dropped_count`
  incremented when `policy.allow_non_authoritative_periodic` is false. `:138-139` `if policy.allow_opportunistic: pass`:
  opportunistic work has no producer and the branch is empty. `:141` returns `(work_sequence, dropped_count)`.
- `src/engine/policy.py:15-16` the two flags; per mode `:82-83` NORMAL (True, True), `:103-104` CONSTRAINED (True, True),
  `:124-125` DEGRADED (False, True), `:145-146` SURVIVAL (False, False). `diagnostic_verbosity`/`metrics_detail` are set per mode in
  the same blocks.
- `src/engine/kernel.py:127` `self._scheduler = scheduler or DefaultScheduler()` (no definitions). `:576-577`
  `self._current_work_items, dropped_count = self._scheduler.select_work(...)` then `self._status.record_dropped_work(dropped_count)`.

### Dynamic registration (the planner's assumption)
Holds. In `src/` and `tools/`: no `PeriodicDefinition(` instantiation, no `scheduler=` argument passed to `Kernel(`, no
`DeterministicScheduler(` call, no assignment to `_periodic_defs` outside `scheduler.py:31`. World content cannot register
periodic work: no YAML/JSON under `data/` is read by anything that builds a definition, and the class has no loader. The
kernel is the only scheduler construction and passes no definitions.

### Flags and fields with no reader in `src/` (grep of `.<field>` outside `policy.py`)
- `allow_opportunistic`: only `scheduler.py:138` (empty `pass`).
- `diagnostic_verbosity`, `metrics_detail`: no reader anywhere.
- `allow_non_authoritative_periodic`: only `scheduler.py:103`, which needs a non-authoritative definition (none exist).
- Also dead as a pair: `periodic_updates` (`src/core/updates.py:1048`) has no producer in `src/` (only `apply.py:313-314` and
  the merge code `updates.py:1137,1202-1203,1267` consume it), so `AuthoritativeState.periodic_due_ticks` (`state.py:1425`)
  never advances: a registered periodic task would be due every tick (`scheduler.py:107`). It is in the canonical hash
  (`checkpoint.py:116`), so removing it changes the hash scheme.
- The executor has no branch for periodic work kinds: `src/engine/executor.py` handles entity kinds and `DRAIN_DEBT`
  (`:199`, `:345`); a periodic item with another kind and a string owner produces no result. So even a registered task
  would be selected and then do nothing.

### Docs, parity entries and tests that promise shedding
| Where | Claim | Verdict |
|---|---|---|
| `docs/engine/matrices/resource_governor_degradation_matrix.md:17` | Periodic (Auth): always allowed | **True but vacuous**: no periodic task exists |
| same `:18` | Periodic (Non-Auth) dropped in SURVIVAL | **Partly true**: the mechanism sheds it (`scheduler.py:102-105`), no shipped task exists to shed |
| same `:19`, `:30` | Opportunistic reduced 50% in DEGRADED, dropped in SURVIVAL | **False**: no opportunistic work exists, and the flag's only reader is an empty branch (`scheduler.py:138`). The table also disagrees with `policy.py` (flag is True in CONSTRAINED, False from DEGRADED; no "reduced 50%") |
| same `:26` | Authoritative work never shed; pressure produces work debt | **Partly true**: nothing drops CRITICAL work; work debt never accumulates (`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`) |
| same `:29,:32` | Waterfall: diagnostic verbosity first, then opportunistic, then ..., then non-authoritative periodic | **False for 3 of 4 rungs shown**: diagnostic verbosity has no reader, the other two have nothing to act on |
| `docs/engine/runtime_profiles.md:42-43` | CONSTRAINED sheds non-authoritative metrics; DEGRADED sheds "replay and diagnostics" | **Partly true**: replay richness and traces do change (`replay_manager.py:90,94,99`), diagnostics and metrics detail do not |
| `docs/engine/architecture.md:72` | Law of Progressive Degradation: shed optional load (traces, then diagnostics, then AI fidelity) | **Partly true**: traces yes; diagnostics no; fidelity via `PhaseBudgetGovernor`/cadence yes |
| `docs/engine/project_lawbook.md:28` | Shedding order Telemetry -> Sampling -> Fidelity -> Stall | **Partly true** (fidelity and sampling levers exist; "telemetry" shedding is only traces/replay) |
| `docs/engine/matrices/scheduler_work_model_matrix.md:18,29` | OPPORTUNISTIC work: deferrable/droppable | **False in shipped runs** (class exists in the doc; no producer) |
| `docs/engine/matrices/observability_operational_controls_matrix.md:27` | `FORCE_DEGRADED` "accelerates shedding" | **Partly true**: it changes the mode, so cadence/budgets/concurrency/replay change; no work is shed |
| `docs/engine/matrices/worker_bounds_matrix.md:19` | tick budget enforced by "ResourceGovernor shedding" | **Partly true**: the governor changes the mode; it does not shed work |
| `src/engine/observability.py:32` comment `dropped_work_count: ... Authoritative work shed by governor` and `src/core/governance.py:45` `Work shed in the current tick` | what the counter means | **False/misleading**: it counts only what the scheduler drops (non-authoritative periodic, never authoritative); 0 in shipped runs |
| Parity ledger (`docs/parity_ledger/*.yaml`, search: shed, non-auth, opportunistic, waterfall) | no entry claims scheduler shedding as `verified`; `infrastructure.yaml` ~10934 calls concurrency "the last shedding lever" | **No parity change needed**; none claims what is false |
| Tests: `tests/unit/core/test_degradation_order.py:9-40`, `test_scheduler_contract.py`, `test_work_classes.py`, `test_signal_truth.py:112-`, `test_deferred_work_debt.py`, `tests/integration/kernel/test_work_debt_stays_empty_in_production.py` | the mechanism sheds | **True as specs of the mechanism, all with test-registered definitions**; none runs a shipped scheduler configuration |

## Scope 2: git history
`PeriodicDefinition(` was never instantiated outside tests on any branch. `git log --all -S"PeriodicDefinition("` over `*.py`
lists only test files: `tests_v2/engine/*` (2026-04-18 to 04-20), `tests_legacy/engine/*` (2026-04-26, removed 2026-06-17 by
`677abbfb5`), `tests/...` today. `src/engine/scheduler.py` was added 2026-05-18 (`562116889`, "Resource V2
Implementation") with the mechanism and no registration; the kernel has always built the default scheduler. So the path was
designed (resource governor milestones M4-M6) and never wired. It was not removed.

## Scope 3: what a mode change actually changes in a shipped run
- **Phase budgets** (scan policy, candidate/strategic/movement budgets, sweep interval, compaction level):
  `governor.py:62-63` -> `GovernorPolicy.phase_budgets`, read through `policy.py:32-56` and `phase_governor.py`.
- **System cadence** per mode (`policy.py:83+` blocks): consumed by `should_run` (`scheduler.py` brain gating).
- **Concurrency**: `kernel.py:573` `set_concurrency_limit(policy.concurrency_limit)` (1.0 / 1.0 / 0.5 / 0.25).
- **Replay**: `replay_allowed` (`kernel.py:681,1164,1169`, `replay_manager.py:90`), `replay_richness` MINIMAL
  (`replay_manager.py:94`; and the per-tick digest is `NOT_COMPUTED_LIVE_POLICY` in DEGRADED, `kernel.py:1164`), SURVIVAL emits
  nothing.
- **Subsystem traces**: `allow_subsystem_traces` (`replay_manager.py:99`).
- **LOD** is profile-driven, not mode-driven (`governor.py:63`, `scheduler.py:77`).
- **No effect today**: `allow_opportunistic`, `allow_non_authoritative_periodic` (no instances), `diagnostic_verbosity`,
  `metrics_detail`, and `dropped_work` itself.

## Scope 4: baselines and reports that carry `dropped_work`
- No committed baseline file carries it: `docs/observability/baselines/*.json`, `tests/perf/baselines/*.json`,
  `tests/regression/baseline_5k.json` contain neither `dropped_work` nor `total_dropped_work` (grep: no match).
- It is live telemetry only: `src/api/engine_manager.py:210`, `src/observability/live/snapshot_provider.py:137`,
  `src/observability/prometheus_collector.py:91-93` (`sim_dropped_work_delta`), `src/engine/observability.py:32,134`
  (`dropped_work_count = status.total_dropped_work`). Stored copies live outside the repo (the warehouse, Prometheus, run
  manifests under `data/runs`, which is not tracked).
- What the number counted: before PR #379 (2026-10-06) the value was the sum of (1) the mid-tick throttle's
  `len(results) - i` drops, (2) a `9999` sentinel per end-of-tick overrun after tick 5, and (3) scheduler sheds (0 in shipped
  runs). Both (1) and (2) depended on host speed and (2) was not a count of anything. Since #379 it counts only (3), so it is 0.
- For PERF-M1-T05: no committed baseline needs a disposition for this field. Any externally stored `dropped_work` series
  from before 2026-10-06 is **incomparable** with later values and should not be used as a degradation measure.

## Scope 5: options
- **(a) Register real non-authoritative periodic tasks.** No candidate exists in `src/`: the housekeeping the docs name
  (log rotation, summary generation) runs outside the kernel (SimQ feed, observability workers). Needs, together: a task
  with real work, an executor branch for its work kind, a producer for `periodic_updates` so `periodic_due_ticks` advances (that
  is authoritative state in the canonical hash, so it touches `state.py`/`apply.py`/`pipeline.py` and the PERF-D5 scheme),
  and a reason the work is non-authoritative yet worth scheduling. Cost: high; it builds work only so it can be shed. Benefit:
  makes the documented waterfall true.
- **(b) Remove the dead path and correct the docs.** Remove periodic definitions, `allow_opportunistic`,
  `allow_non_authoritative_periodic`, `diagnostic_verbosity`, `metrics_detail`, `periodic_updates`, `periodic_due_ticks`, and the
  `dropped_work` counter or redefine it. Cost: medium to high and gated: `periodic_due_ticks` is in the canonical hash, so
  removal needs a scheme change and edits `state.py`/`apply.py`/`pipeline.py`; ~6 test files and 8 docs change. Benefit: no dead
  surface.
- **(c) Keep the code, document it as unused, mark claims `unsupported`.** Cost: low, docs and ledger only, no hash change, no
  gated file. Keeps the mechanism and its test specs (they are valid specs of the mechanism). Leaves a dead path in place.

## Recommendation
**(c) now, and fold the removal part of (b) into the work-debt retire step 2.** That step already needs a PERF-D5 scheme
bump (`work_debt` is in the canonical hash) and the full lift; `periodic_due_ticks` is the same kind of dead hashed field and can
ride the same bump. Until then: correct the docs listed in the table to say what is true (mode changes shed replay richness,
traces, cadence, budgets and concurrency; they do not shed work), fix the two misleading comments, and describe
`dropped_work` as "work the scheduler shed; always 0 in shipped runs". Do not do (a) unless the owner wants a real
non-authoritative task for its own sake. The decision is the owner's and is pending.
