---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION
phase: done
date: 2026-10-15
tags: [performance, benchmarking]
---

# TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION

## Title
Attribute `resolution_overhead` (12-33 % of every tick) to named call sites, with folded-stack evidence

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION` (#597) met its AC2 only partly. Every phase above 5 % of the tick was attributed except `resolution_overhead`, which is 12 to 33 % of every tick (`docs/performance/tick_cost_growth.md` §3 H5). It is a residual, not a phase: `src/engine/kernel.py:452` sets it to `max(0, res_total - sub_sum)`, the resolution phase's total minus the refine sub-phases it times (DEV-017). It is therefore whatever runs inside `_phase_resolution` outside the timed sub-phases: dispatch, update application, bookkeeping. Under the canonical contract at `movement_2000` it was 40 % (4583 ms) against 13 % under pinned, a mode effect the investigation did not explain.

## Scope
1. **Attribute the residual from stacks, with no `src/` edit.** Use the `profile_tick.py` tooling from #597 (`--contract`, `--world`, py-spy at 250 Hz). Take samples whose stack contains `_phase_resolution` but none of the timed sub-phase frames, and rank their self and inclusive functions. Name the call sites that make up at least 80 % of the residual. Scenarios: `idle_100`, `strategic_100` and a corpus world past tick 600, all pinned. Then `movement_2000` under pinned and canonical, for the mode effect.
2. **The canonical jump.** Say which call sites grow under canonical at `movement_2000`, and whether this is work the degraded mode adds (legitimate) or a cost the mode makes visible.
3. **Write-up.** Add a section to `docs/performance/tick_cost_growth.md` (H5 filled in), with a ranked list. Anything that is rpg's to fix goes to lead-planner as an addition to the #593 hand-off, not as an edit in `src/`.
4. If a call site can only be separated by a timer in `kernel.py`, propose it to rpg through lead. Do not add it.

## Out of Scope
- Any `src/` change outside `src/perf/`, and all fixes.
- Re-attributing the phases #597 already attributed.
- Baselines.

## Acceptance Criteria
- AC1: At least 80 % of the `resolution_overhead` samples in each scenario are attributed to named call sites, with folded-stack shares and the profile headers (commit, host, loadavg, contract).
- AC2: The canonical-versus-pinned difference at `movement_2000` is explained, or stated as unexplained with what was ruled out.
- AC3: `tick_cost_growth.md` H5 is filled in. Any rpg items are sent to lead-planner for #593.
- AC4: Resource rule: heavy runs go one at a time, in the foreground, under the systemd-run memory cap. Tell lead-planner before `movement_2000` and before any run over about 3 GB, and check that `free -m` shows at least 2.5 GB available first.

## Related Tickets
- TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION (#597), TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES (DEV-017)

## Related Docs
- docs/performance/tick_cost_growth.md (§3 H5, §8), docs/guidelines/intentional_divergences.md (DEV-017), docs/engine/kernel.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION/

## Related Code Areas
- src/engine/kernel.py (_phase_resolution, :452, read only), tools/perf/profile_tick.py, tools/perf/_profiling_common.py, tools/perf/profile_diff.py

## Assumptions / Open Questions
- A1: Starts after #597 merges (its tooling options are needed).
- A2: py-spy stays installed as a uv tool (not in .venv).

## Implementation Notes
Method changed from the ticket's "rank stack samples" after the first look at existing data, with perf-planner's approval (plan.md "Revision"):
1. Replayed the kernel's own timer accounting on the folded stacks of five #597 profiles (`residual_by_kernel_accounting.py`): 93 to 99 % of the residual sits on `src/engine/pipeline.py:393`, the `fused_strategic_pass` run_phase.
2. Cause, provable from the code: `refine`'s Phase 7 timer starts `t_start` at `pipeline.py:386`; `t_start` is assigned again at `:431` for the `faction_sentiment` block; `costs["final_integrity"] = (t8 - t_start)` at `:461` therefore times only `:431-461` (0.1 to 0.33 ms), and the strategic, lifecycle, groups and capacity work before it falls into `resolution_overhead`.
3. Counterfactual (`strategic_pass_counterfactual.py`), no `src/` edit: a process-local timer on `StrategicIntelligenceSystem.fused_strategic_pass`, same seed run unwrapped then wrapped; inertness by the end-state fingerprint (shown for canonical runs and the movement_500 pinned control; NOT shown for movement_1000 pinned, which had no control). Pinned runs are not deterministic because of the queue and worker wall-clock signals and the scheduler's tick-time inputs (`PINNED_NOTE`); the mid-tick throttle is report-only since DEV-014.
4. Runs, all one at a time under `MemoryMax=3G`, quiet window checked, lead's go for the corpus world: idle_100 and strategic_100 pinned (10 + 30 ticks), movement_500 and movement_1000 pinned and canonical (3 + 20 and 3 + 15 ticks), `frontier_extended` canonical 0 + 1100 ticks crossing all four modes.
Deviations from the ticket text: the corpus world was run canonical from tick 0 (to cross the modes), not "pinned past tick 600"; `movement_2000` was not run (`movement_500` and `movement_1000` stood in, as lead agreed).

## Test Summary
No `src/` change and no maintained tool, so no pytest suite was added (test_plan.md). Evidence checks instead: the classifier reproduces the table's residual shares within a few points on four of five profiles; the counterfactual script's `--selftest` passes; the wrapper's own cost was calibrated (about 0.3 microseconds per tick); fingerprints identical for canonical runs. Gates on the final tree before the batch push are run once at batch close (mypy gate rc=0 and `codebase.health check` rc=0 were run on the tree after eceb0ba68..e284f020b; `tests/unit/perf` and the perf guard tests 316 passed).

## Files Changed
- docs/performance/tick_cost_growth.md (H5 row filled; new "H5 attribution" section; the SURVIVAL suggestion for rpg withdrawn)
- agent-working/stored_artifacts/TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION/ (investigation.md, plan.md, test_plan.md, `residual_by_kernel_accounting.py`, `strategic_pass_counterfactual.py`)
Commits on `perf-t08-noisy-baselines`: eceb0ba68, e284f020b, 4d22e2975, 4002d6e01. Raw run data: `reports/perf/resolution_overhead/` (git-ignored).

## Completion Summary
- **AC1 met:** the unattributed residual after subtracting the wrapped `fused_strategic_pass` is 2.9 % (idle_100), 8.3 % (strategic_100), 1.9 % and 0.7 % (movement_500 pinned, canonical), 1.1 % and 0.6 % (movement_1000), 12.9 % (corpus `frontier_extended`, canonical): below 20 % everywhere, the strategic pass being 87 to 99.4 % of `resolution_overhead`. Headers in investigation.md (commit 9accca4ad, host, loadavg, contract).
- **AC2 partly explained:** in the `movement` runs the canonical-against-pinned jump is the strategic pass costing 1.6 to 2.0 times as much (248 against 125 ms at 500; 564 against 345 ms at 1000), not unattributed bookkeeping. The mode alone does not explain it: on the corpus world crossing all four modes the median pass is flat (12.4 to 13.1 ms) while the tick doubles. What makes `movement` costlier under canonical is **not established**; candidates untested: the two contracts evolve different worlds, or a property of `movement`.
- **AC3 met:** `tick_cost_growth.md` H5 filled with a ranked list; the rpg items (the one-line timer fix at `pipeline.py:431`; the SURVIVAL suggestion withdrawn) went to lead-planner through perf-planner for the #593 hand-off.
- **AC4:** every run one at a time, foreground or background, under `MemoryMax=3G` with the quiet window; lead's go for the corpus world; no run over 3 GB; `movement_2000` not run.
- No AC text was changed. Open: the cause of the `movement` canonical-against-pinned difference.
