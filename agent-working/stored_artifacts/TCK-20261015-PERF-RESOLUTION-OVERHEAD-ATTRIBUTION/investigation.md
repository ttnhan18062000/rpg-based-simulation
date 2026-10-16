---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION
date: 2026-10-16
tags: [performance, benchmarking]
---

# Investigation: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION

Static reading only (no run, no `src/` edit). Sources: `src/engine/kernel.py` (`_tick_once_inner` around :425-470, `_phase_resolution` :599-662), `src/engine/pipeline.py` (`AuthoritativeApplyPipeline.refine`), `tools/perf/profile_tick.py`, `docs/performance/tick_cost_growth.md` (H5, section 3).

## What the residual is, exactly
`resolution_overhead = max(0, res_total - sum(sub_phase_costs))` where `res_total` is the wall time of `Kernel._phase_resolution()` (`kernel.py:450-453`) and `sub_phase_costs` is what `refine` timed. So it is **everything in `_phase_resolution` and in `refine` that has no timer of its own**. By reading the code, the candidates are:
1. Result ordering and duplicate check: `self._final_results.sort(...)`, the loop building `entity_updates` (per result; includes the `i % 10` budget check and `time.perf_counter_ns()` read).
2. `_drain_pending_grief_triggers(entity_updates)`.
3. Building the `StateUpdate`.
4. `refine` outside its timed blocks: its prologue (`pipeline.py:41-95`), the code between the per-block `t_start` / `costs[...]` pairs, and whatever runs after the last timed block (merging of the per-system updates into `refined_update`, `metric_counters`).
5. `self._metrics` assembly and the `movement_cache` / `_index_*` reads.
6. The replay emit with `self._state.fingerprint()` when `self._current_policy.replay_allowed` (`kernel.py:654-665`); the benchmarks pass `no_replay`, but the policy flag, not the run flag, gates this line, so it must be checked rather than assumed off.
7. Anything `refine` calls whose cost is not under a timer (for example `ApplyPath` commit work if it happens inside `refine`; the grep shows no timer around it).

## Why a line-based attribution is needed
`refine`'s timers are inline `t_start` / `costs[...]` pairs in one long function, not separate functions, so a stack-frame name test ("contains none of the timed sub-phase frames") cannot separate timed from untimed samples. py-spy's folded frames carry `file:line`, so a sample is **timed** when its `refine` frame's line lies inside a timed block (the `t_start` line to its `costs[...] =` line, read from `pipeline.py`) and **residual** otherwise; a sample with `_phase_resolution` but no `refine` frame is residual by construction (items 1-3, 5, 6).

## Canonical jump at `movement_2000` (hypothesis, not a finding)
Under canonical the governors read a modelled cost and `movement_2000` leaves NORMAL (CONSTRAINED or SURVIVAL, tick_cost_growth.md section 3). A degraded policy changes `cadence` (passed to `refine`) and `replay_allowed` (set false at `kernel.py:201` and `:563`). Either can move cost out of the timed blocks into the residual: skipped systems stop contributing to `sub_sum` while the per-entity result loop (item 1) and the untimed `refine` parts keep scaling with entity count. Test: the per-tick mode sequence next to the per-tick residual in the pinned and canonical profiles; if the residual jumps on the ticks the mode changes, it is a mode effect on what is timed, not new work.

## Constraints that shape the plan
- py-spy at 250 Hz, non-blocking (the blocking mode slowed a tick about 8x here); the sampler's overhead is measured by `--sampler none`.
- `movement_2000` is the heaviest process (tick about 11 s under canonical, per the 4583 ms at 40 %); it needs lead's separate go and a `MemoryMax` cap, one at a time.
- A tick table is printed by `profile_tick.py`; the stacks file is `profile.folded` of the measured ticks only.

## Finding from the existing #597 profiles (no new run): the residual is a shadowed timer in `refine`
**Hypothesis, supported by 5 existing profiles, not yet proven by a counterfactual.**
- `refine`'s "Phase 7" block starts `t_start` at `src/engine/pipeline.py:386` (before `fused_strategic_pass`, lifecycle, groups, clan, capacity, dirty sets) and stores it with `costs["final_integrity"] = (t8 - t_start)` at `:461`. **`t_start` is assigned again at `:431` for the `faction_sentiment` block**, so `final_integrity` measures only `:431-461`. The reported `final_integrity` is 0.1 to 0.33 ms in every profile; the code it was meant to time is not small.
- Replaying the kernel's own accounting on the folded stacks (script `residual_by_kernel_accounting.py` in this folder: a block runs from the latest `t_start` line to the next `costs[... t_start]` line, as at runtime) classifies the `_phase_resolution` samples as counted or residual. Residual samples fall **93 to 99 % on one line, `pipeline.py:393`, `fused_strategic_pass`** (the `strategic_intelligence` run_phase), in all five profiles:

| profile (commit ebbcaf46b) | residual samples / `_phase_resolution` samples | at line 393 | table `resolution_overhead` | table `final_integrity` |
|---|---|---|---|---|
| movement_1000 pinned | 4128 / 27541 (15 %) | 99 % | 883 ms (15.8 % of tick) | 0.17 ms |
| movement_1000 canonical | 2157 / 17249 (13 %) | 99 % | 620 ms (19.8 %) | 0.19 ms |
| strategic_100 canonical | 620 / 2655 (23 %) | 93 % | 102 ms (17.0 %) | 0.33 ms |
| idle_100 canonical | 198 / 478 (41 %) | 97 % | 36 ms (29.2 %) | 0.10 ms |
| mixed_200 canonical | 207 / 923 (22 %) | 96 % | 48 ms (18.5 %) | 0.20 ms |

  The sample share and the table share agree within a few points for four of five rows; `movement_1000 canonical` (13 % of samples against 19.8 % of the tick) is the loosest, and sampling skews absolute ms (the profile header says py-spy inflates them).
- So `resolution_overhead` is mostly **`strategic_intelligence` time that a mis-scoped timer failed to attribute**, not dispatch or bookkeeping; a fix is one line in `src/engine/pipeline.py` (a separate variable for the faction_sentiment block), which is **rpg's, via lead**, not mine (`src/` outside `src/perf/` is out of scope).
- A second, smaller effect: the same shadowing means `final_integrity` (as stored) is a tail slice while `faction_sentiment` is inside it; no double count, but `sum(sub_phase_costs)` is underestimated by the lost head.
- Not explained by this: the canonical jump at `movement_2000` (40 % against 13 %): `strategic_intelligence` cost may grow in degraded modes (it is the part that now falls into the residual), to be tested with the per-tick mode sequence as planned.

## Counterfactual results, idle_100 and strategic_100 pinned (2026-10-16; commit 9accca4ad; 10 warm-up + 30 measured ticks; one process each, MemoryMax=3G; mode NORMAL for every tick)
`strategic_pass_counterfactual.py`: same seed run twice in one process (unwrapped, then wrapped with the process-local timer on `StrategicIntelligenceSystem.fused_strategic_pass`); `inert` = identical sha256 of `state.fingerprint()` at the end of both runs. The residual is computed from the WRAPPED run (its `resolution_overhead` minus its wrapped ms); the unwrapped run's overhead is the check column.

| scenario | inert | wrapped ms/tick | `resolution_overhead` (wrapped run) ms | residual ms | residual share | `resolution_overhead` (unwrapped run) ms | reported `final_integrity` ms | wrapper cost per tick | loadavg1 |
|---|---|---|---|---|---|---|---|---|---|
| idle_100 pinned | True | 25.507 | 26.256 | 0.749 | 2.9 % | 19.311 | 0.101 | 0.37 us | 0.52 |
| strategic_100 pinned | True | 55.245 | 60.247 | 5.002 | 8.3 % | 52.383 | 0.146 | 0.30 us | 0.80 |

- **AC1 is met for both: the residual is 2.9 % (idle_100) and 8.3 % (strategic_100) of the overhead, below the 20 % bar.** `fused_strategic_pass` is 97 % and 92 % of `resolution_overhead`. The wrapper is inert (identical fingerprints) and costs about 0.3 microseconds per tick, negligible.
- **Caveat on the check column:** the unwrapped run's overhead (19.3 and 52.4 ms) is lower than the wrapped run's (26.3 and 60.2 ms), by 36 % and 15 %. The wrapper's own cost is four orders of magnitude too small to explain that, so it is run-to-run variance between two 30-tick processes' runs on this loaded VM, and these figures do not show that "wrapping did not move the overhead" any tighter than that. The conclusion rests on the within-run ratio (wrapped ms against the same run's overhead), which does not depend on the difference between runs.
- **Reported `final_integrity` stays 0.10 to 0.15 ms,** as the shadowed `t_start` predicts.
- Still open: the corpus world past tick 600 (needs lead's go) and the movement_2000 canonical-versus-pinned question (movement_1000/500 stand in, per lead).

## Counterfactual, movement_500 and movement_1000 (2026-10-16; commit 9accca4ad; warm-up 3; 20 and 15 measured ticks; one process per run, MemoryMax=3G; quiet window checked before each: loadavg1 0.58 to 1.28)
| scenario, contract | measured modes | wrapped `fused_strategic_pass` ms/tick | `resolution_overhead` (wrapped run) ms | residual ms (share) | `resolution_overhead` (unwrapped run) ms | fingerprint with and without wrapper |
|---|---|---|---|---|---|---|
| movement_500 pinned | NORMAL 20 | 125.2 | 127.6 | 2.4 (1.9 %) | 93.0 | differs |
| movement_500 pinned, repeat with `--control` | NORMAL 20 | 87.6 | 89.9 | 2.2 (2.5 %) | 110.4 | differs; **the two unwrapped runs differ too** |
| movement_500 canonical | SURVIVAL 20 | 248.0 | 249.7 | 1.7 (0.7 %) | 230.1 | identical |
| movement_1000 pinned | NORMAL 15 | 345.0 | 348.7 | 3.7 (1.1 %) | 355.7 | differs (no control run) |
| movement_1000 canonical | SURVIVAL 15 | 564.2 | 567.8 | 3.6 (0.6 %) | 520.3 | identical |

- **AC1 holds at these sizes too:** the unattributed residual is 0.6 to 2.5 % of `resolution_overhead`; `fused_strategic_pass` is 97.5 to 99.4 % of it in every run (idle_100 97 %, strategic_100 92 %).
- **Inertness is shown for the canonical runs (identical fingerprints at movement_500 and movement_1000) and for the movement_500 pinned control; it is NOT shown for movement_1000 pinned.** The pinned fingerprints differ with and without the wrapper, but a pinned run is not deterministic: `PINNED_NOTE` in `tools/perf/_profiling_common.py` says "pinned fixes the RuntimeMode only (PinnedNormalGovernor); the other wall-clock inputs still move outside audit_mode: the mid-tick budget throttle's wall-clock reading (report-only since DEV-014), the queue and worker wall-clock signals and the scheduler's tick-time inputs". **The mid-tick throttle reads the wall clock but is report-only (DEV-014) and does not change a result; the nondeterminism that moves a pinned run comes from the other inputs named there (queue and worker wall-clock signals, the scheduler's tick-time inputs).** At movement_500 the control (two unwrapped runs) differs by itself, so that difference is not evidence against the wrapper. At movement_1000 pinned there was no control: its residual still stands as a within-run ratio, but the wrapper's inertness there is unproven. (An earlier message of mine, and the commit message of e284f020b, named the budget throttle as the cause; that was imprecise: the contract note calls the throttle report-only.)
- **AC2 (canonical against pinned), partly explained:** the canonical runs are SURVIVAL for every measured tick; the pinned ones NORMAL. The strategic pass costs **1.6 to 2.0 times as much** under canonical (248 against 125 ms at 500; 564 against 345 ms at 1000), and it is the strategic pass that grows, not unattributed bookkeeping (the residual stays at or below 2.5 % in both contracts). That is the shape of the #597 finding at movement_2000 (`resolution_overhead` 40 % of the tick under canonical against 13 % pinned): the share is the strategic pass's. **Not established:** what in `fused_strategic_pass` does more work in SURVIVAL (candidates: the `cadence` passed to it, a forced full scan, or per-mode policy), and whether that extra work is legitimate degraded-mode work or cost the mode makes visible; with all measured ticks in one mode this run cannot separate them. A within-run comparison needs ticks in both modes (warm-up 0 on a world that crosses modes) or a pinned-SURVIVAL governor, neither built here.
- Caveats: 15 to 20 measured ticks per run; the unwrapped-run column differs from the wrapped by 3 to 24 % (run-to-run variance; the conclusions use the within-run ratio); `movement_1000 pinned` ran with loadavg1 1.64 at its end (0.73 at its start).

## Corpus world crossing the modes, per-mode medians (2026-10-16 ~16:45; commit 9accca4ad; lead's go; `frontier_extended`, canonical, 0 warm-up, 1100 ticks, unwrapped then wrapped in one process, collector on, MemoryMax=3G; quiet window at start; loadavg1 1.05 at the end)
- **AC1:** wrapped `fused_strategic_pass` 13.57 ms/tick of 15.58 ms `resolution_overhead` (unwrapped run: 15.49 ms, within 0.6 %): residual 2.0 ms = **12.9 %**, below the 20 % bar. Inert: identical end-state fingerprints (canonical, deterministic). Reported `final_integrity` 0.146 ms.
- **Mode order in this run:** NORMAL ticks 0-19, CONSTRAINED 20-32, DEGRADED 33-66, SURVIVAL 67-1099 (the modes occur in that order, so mode and world age are confounded across the first three; within SURVIVAL the world ages by a thousand ticks).

| mode | ticks | median wrapped `fused_strategic_pass` ms | median `resolution_overhead` ms | median residual share | median tick wall ms |
|---|---|---|---|---|---|
| NORMAL | 20 | 12.68 | 13.68 | 8.2 % | 59.6 |
| CONSTRAINED | 13 | 12.36 | 13.56 | 8.5 % | 61.1 |
| DEGRADED | 34 | 13.06 | 14.03 | 8.4 % | 61.7 |
| SURVIVAL | 1033 | 13.01 | 15.07 | 13.2 % | 124.3 |

SURVIVAL first 100 ticks 13.7 ms, last 100 ticks 12.7 ms: no age trend inside SURVIVAL either.

**Reading: in this world the strategic pass does NOT cost more in SURVIVAL. Its median is flat across the four modes (12.4 to 13.1 ms) while the tick's wall time doubles (60 to 124 ms).** The movement runs (pinned against canonical, 1.6 to 2.0 times) therefore are not explained by "the strategic pass is costlier in SURVIVAL": that explanation is weakened, not confirmed, by this run. What differs between the two movement contracts besides the mode is not established: candidates (none tested) are that the two contracts do not evolve the same world (canonical's modelled governor changes which systems run or when, so the state the strategic pass sees differs; the pinned runs are not deterministic), or that `movement` has a feature `frontier_extended` lacks. The growth of the tick in SURVIVAL on this world is somewhere other than `fused_strategic_pass` (its share of the tick falls from 21 % to 10 %), outside what this ticket attributes. Caveats: one world; the first three modes have 20, 13 and 34 ticks; a single process run.
