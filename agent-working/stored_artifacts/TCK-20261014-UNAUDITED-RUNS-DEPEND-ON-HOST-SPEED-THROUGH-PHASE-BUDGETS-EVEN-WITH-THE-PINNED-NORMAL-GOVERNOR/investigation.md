---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR
artifact_type: investigation
tags: []
---

# investigation — TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR

## Result
**Source: wall-clock, not hash order.** `PhaseBudgetGovernor.evaluate` (`src/engine/phase_governor.py:107-143`, called from `ResourceGovernor.evaluate` at `src/engine/governor.py:62` on every tick) reads the measured per-phase milliseconds (`signals.effective_phase_cost["locomotion"]` and `["final_integrity"]`) and the measured tick cost. Above 10 ms or 15 ms (or 30 and 50 percent of the tick budget) it switches the scan policy to THROTTLED or EXACT_DIRTY and lowers the movement and strategic budgets and the sweep interval. That changes which entities get movement candidates and strategic scans, so the world diverges. The shared test helper `PinnedNormalGovernor` (`tests/helpers/kernel_pinning.py`) overrides only `_get_indicated_mode` and `force_mode`, so the mode stays NORMAL but `evaluate` still hands the live signals to `PhaseBudgetGovernor`. Its docstring claims the outcome does not depend on host speed; for phase budgets that is false. `audit_mode=True` zeroes the signals (`ZeroedSignalSource`) and removes the dependence, which is why the gate harness (`audit_mode`, `PYTHONHASHSEED=0`) and the grade anchors are deterministic.

This is the open PERF-D1 contract (`SignalContract.LIVE` is "today's behaviour", `src/config/profiles.py:57`), not new in rpg-next: `PhaseBudgetGovernor.evaluate` and `effective_phase_cost` are present on b396080cc, and the file dates from 2026-05-18.

## Evidence (rpg-next 4858607c2, seed 42, `PinnedNormalGovernor` + `LocalSequentialExecutor`, `max_tick_budget_ms` 1e9, host load 13 to 18 from other sessions)
1. **Hash seed is not the source.** frontier_living_world, 800 ticks, sequential, `PYTHONHASHSEED` 0, 1, 2, 0: all four digests identical at every 100-tick checkpoint (d9c5ba...). crowded_frontier, 800 ticks: two outcomes, and the same `PYTHONHASHSEED=0` produced both (2e8bd1... on one run, e3684a... on another); `PYTHONHASHSEED=1` produced the second twice. The digest depends on the run, not on the hash seed.
2. **Normal mode diverges early, audit mode does not.** crowded_frontier, 220 ticks, `PYTHONHASHSEED=0`, three runs started together: normal mode first diverges at tick 9 (entities 22, 23 and 27 stand on different tiles and in different movement modes, WANDER versus REGROUP); with `audit_mode=True` all three runs are identical on every tick to 220.
3. **Pinning the phase budgets removes it.** Same setup, eight processes at once under their own load: with `PhaseBudgetGovernor.evaluate` called with `signals=None`, four runs are identical at every tick to 220; without that, the four runs diverge by tick 2 and end on four different digests.
4. **Earlier symptoms explained.** The base-versus-base differences seen when comparing the warmup fix (crowded_frontier a950.../3943.../3b90..., frontier a950... against 75d4...) were produced by running three to six processes at once, which pushes a phase over 10 ms. They are not caused by that fix.

## Who is affected
- Any run built with `PinnedNormalGovernor` (about 22 files reference it) but without `audit_mode`. This is likely behind the timing-dependent tests already known as flaky on a loaded host (for example `test_hero_guild_routing_seed42_1000t`).
- My own paired probes for D70 and the cover step used `PinnedNormalGovernor` but not `audit_mode`. Divergence 2.125 says "pinned NORMAL governor, `audit_mode`", copied from 2.124; for the D70 probes that is wrong. The D70 headline (camp adds 50 to 0) is structural and unaffected, but the per-kind deaths and alive counts there carry host-speed noise. 2.125 should be corrected.
- Not affected: `tools/test_architecture/rpg_gate_harness.py` (sets `audit_mode` and `PYTHONHASHSEED=0`), the simq grade anchors (audit_mode runs), and `src/perf/long_run_harness.py`.

## Proposed fix (not applied)
1. **Measurement rule:** every paired measurement and probe sets `flags={"audit_mode": True}`. Zero code change; add it to the measurement protocol.
2. **Test helper:** make `PinnedNormalGovernor.evaluate` call `PhaseBudgetGovernor.evaluate(profile, None, ...)`, or have it set `phase_budgets` to the NORMAL baseline, so the helper does what its docstring says. Add the regression test described in the test plan. This may change which of the 22 tests are timing-dependent; run them before and after.
3. **Engine (PERF-D1, separate decision):** under `SignalContract.CANONICAL` the phase pressure already comes from a reference-millisecond model. Making CANONICAL the default for non-live runs would remove the dependence without audit_mode; that is the performance owner's call.
4. Optional guard: a one-line warning when a Kernel is built without `audit_mode` and with a pinned governor, since that combination reads as deterministic and is not.

## Fix applied (approved by rpg-planner: fix 1 and 2, with the additions)
- **Pin at the source.** `ResourceGovernor.zeroes_signals` (False by default; True on `PinnedNormalGovernor`). The Kernel computes `_signals_zeroed = audit_mode or governor.zeroes_signals` and uses it for `select_signal_source` and the manifest's `signal_contract` record, so the pinned path uses the same `ZeroedSignalSource` as `audit_mode`. The mode, the phase budgets, `effective_tick_cost` and any later wall-clock reader see zeros. `PinnedNormalGovernor` keeps its mode overrides.
- **Typed record.** `RunManifest` gains `audit_mode: Optional[bool]` and `signals_zeroed: Optional[bool]` (None in older manifests); the replay manifest, which is the run ledger header, carries the same two keys. `src/observability/reporting/run_determinism.py` has `run_is_host_independent(manifest)` and `require_host_independent_runs(manifests)`, which raises `NonAuditRunError` naming every run not recorded as `signals_zeroed: true` (an older manifest with no record counts as not recorded).
- **Not done: enforcement in the comparison tools.** The only existing run comparators read distribution files, not run manifests (`baseline_comparator.py`), or build their own audit runs (`simq_reanchor`, the gate harness set `audit_mode` themselves). So `require_host_independent_runs` is available and tested but wired into no existing tool yet; wiring it needs the manifest path to reach the comparator, which is a follow-up for whoever owns those tools.
- **Regression tests** (`tests/unit/engine/test_pinned_governor_is_host_independent.py`, 5 tests): with a fake clock that advances 20 ms per read (every phase over 15 ms) the pinned governor chooses identical budgets on every tick and sees no timings; the unpinned governor under the same clock does not (positive control); the Kernel zeroes signals for audit_mode and for the pin only; the manifest fields round-trip; the comparison refusal.

## Proof
- Four pinned-normal runs started together under load (crowded_frontier, seed 42, `PYTHONHASHSEED=0`, no audit_mode, host load above 20 with the 22-file test run going): identical on every tick to 220 (final 157c48d6be). Before the fix the same four diverged by tick 2 and ended on four digests.
- That digest equals the `audit_mode` digest (157c48d6be), and the `audit_mode` run is hash-identical on every tick before and after the fix (220 of 220).

## The mid-tick drop (planner's question 2)
On this base `Kernel` has no throttle that drops work. The mid-tick check in `_phase_resolution` (`kernel.py`, the `i % 10` loop) and the end-of-tick check both only call `_report_budget_overrun`, which records telemetry and a watchdog alert and "never changes outcomes"; neither calls `force_mode` nor `record_dropped_work`, and no result is skipped (they were made report-only by TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY). The one `record_dropped_work` call is `_phase_scheduling` (`kernel.py:574`), fed by `Scheduler.select_work(state, policy)`; the policy there derives from the mode, which is NORMAL under the pin, and nothing registers droppable work, so the dropped count is 0. So `PinnedNormalGovernor` did cover this path; the one uncovered wall-clock path was the phase budgets, now closed at the source. The remaining `not self._audit_mode` conditions gate only the overrun reports.

## The 22 PinnedNormalGovernor files, before and after (rpg-next 2e1a4d201, then with the fix; same host, load 15 to 22)
Run: the 19 test files that reference the pin (the helper itself, the guard `test_no_local_pinned_governor_copies.py` and the new no-compile test are not behaviour tests), plus the guard and the no-compile test after.
- Before: 72 passed, 2 failed, 2 xfailed (30 min). After: 82 passed, 1 failed, 2 xfailed (28 min); the 9 extra passes are the new and added tests.
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_mix_is_not_dominated_by_cooperation`: fails before and after with the same value (pooled cooperation share 0.6991, 1450 of 2074; seed 42 0.7007, seed 1337 0.6975). A deterministic red that is not host-speed dependent; unchanged by the fix. Its expectation is not touched.
- `tests/mechanic_scenarios/test_conflict04_movement_layer.py::test_invariant_no_entity_stays_blocked_...`: failed before with `TimeoutError: Test execution exceeded the resource time limit` (a 30-minute run on a loaded host); passes after. The only outcome that changed, and it is the timing-dependent kind.
- Every other file passed before and after (the other ten mechanic_scenarios files, test_species_relations_metamorphic_validation, test_health_never_exceeds_max_hp, test_total_coin_is_conserved, test_rpg_gate_harness, test_resource_regrowth_wiring). The xfails are unchanged. No assertion was changed in any file.

## Repro (self-contained; run three copies at once and compare the per-tick hashes)
```python
import sys, os, hashlib, json
tree, world, seed, ticks, mode = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]  # mode: normal | audit | nophase
os.chdir(tree); sys.path.insert(0, tree)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world
if mode == "nophase":
    from src.engine.phase_governor import PhaseBudgetGovernor
    _o = PhaseBudgetGovernor.evaluate
    PhaseBudgetGovernor.evaluate = staticmethod(lambda profile, signals, current_mode, current_tick, opt_profile=None: _o(profile, None, current_mode, current_tick, opt_profile))
flags = {"no_frame_pacing": True, **({"audit_mode": True} if mode == "audit" else {})}
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=compile_world(world, seed), rng=DeterministicRNG(seed), flags=flags, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
for _ in range(ticks):
    k.tick_once()
    s = k._state
    snap = {e: [x.kind, list(x.navigation.position), x.combat.hp, x.combat.alive] for e, x in sorted(s.entities.items())}
    print(s.tick, hashlib.sha256(json.dumps(snap, default=str).encode()).hexdigest()[:10])
```
