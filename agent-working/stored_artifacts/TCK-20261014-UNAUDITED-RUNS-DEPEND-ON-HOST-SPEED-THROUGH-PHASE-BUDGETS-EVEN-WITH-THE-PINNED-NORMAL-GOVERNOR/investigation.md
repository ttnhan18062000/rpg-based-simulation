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
