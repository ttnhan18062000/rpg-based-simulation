---
status: active
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
