---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION
date: 2026-10-16
tags: [performance, benchmarking]
---

# Plan: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION

Planning only; sent to perf-planner. No run until lead releases perf, and `movement_2000` needs its own go.

## Revision after the first look at existing data (2026-10-16)
The #597 folded stacks already answer most of AC1: 93 to 99 % of the kernel-counted residual sits on `pipeline.py:393` (`fused_strategic_pass`) because `t_start` is shadowed at `:431` and `final_integrity` times only `:431-461` (investigation.md, last section). So the plan changes from "attribute by stacks from new profiles" to **confirm and bound that finding with the fewest runs**, and the heavy `movement_2000` runs shrink to the canonical-jump question only:
1. **Counterfactual without a `src/` edit:** a profiling child under `src/perf`/`tools/perf` that wraps `StrategicIntelligenceSystem.fused_strategic_pass` with a timer (monkeypatch in the child process only) and prints its ms per tick next to the table's `resolution_overhead`. If the two agree within a few percent on `idle_100`, `strategic_100` and one corpus world past tick 600 (small processes, pinned), the finding is proven. Residual after subtracting it must be below 20 % of the original to meet AC1's 80 %.
2. **Canonical jump (`movement_2000`, lead's separate go):** per-tick mode sequence beside the wrapped `fused_strategic_pass` ms, pinned and canonical, to see whether the strategic pass is what grows. If that is too heavy for the evidence, `movement_1000` (already profiled) plus `movement_500` stand in and AC2 is stated as partly explained with what remains.
3. **rpg item for #593 (through lead):** one-line fix of the shadowed `t_start` at `pipeline.py:431`, expected effect: `final_integrity` reports the real strategic/lifecycle/groups time and `resolution_overhead` falls to the true overhead; note DEV-017 consequences (reported tick costs per phase move, total unchanged).

## Method as first written (kept for the record; superseded where the revision above says so)
1. **Residual-sample classifier** (reproduction script kept in this ticket's staging folder, like the T08 script, moving to stored_artifacts at close; not a `tools/perf` tool unless perf-planner wants it owned and tested): read `profile.folded`, parse each stack's frames as `func (file:line)`, keep samples containing `_phase_resolution`, split them into **timed** (the `refine` frame's line inside a timed block of `pipeline.py`, ranges read from the file's own `t_start` / `costs[...]` pairs at the profiled commit) and **residual** (everything else). Rank residual functions by self and inclusive samples; list the call sites that cover at least 80 % of the residual (AC1). The classifier is cross-checked on its own against the phase table: the share of timed samples must roughly match `sum(sub_phase_costs) / res_total` from the tick table (a mismatch means the line ranges are wrong, and is reported).
2. **Scenarios, all pinned first** (one process at a time, `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, quiet-window check loadavg1 < 1.5 and `free -m` available > 2500 MB): `idle_100`, `strategic_100`, one corpus world past tick 600. Profile headers (commit, host, loadavg, contract) copied into the write-up.
3. **`movement_2000` pinned and canonical** (lead's separate go; one process each; MemoryMax=3G): the same classifier, plus the per-tick mode sequence beside the per-tick residual from the tick table, to test the hypothesis in investigation.md (jump on the ticks where the mode changes, or not).
4. **Write-up** in `docs/performance/tick_cost_growth.md`: H5 row filled in and a ranked list under it, with folded-stack shares. Anything that is rpg's to fix goes to lead-planner as an addition to the #593 hand-off (message, not a `src/` edit). If separating a call site needs a timer in `kernel.py`, propose it to rpg through lead; do not add it.

## Order and gates
- **Now, no run:** the classifier script and its dry run on the existing #597 folded files (if kept under `reports/perf/tick_cost/`), which validates the line-range logic without any new profile.
- **After lead's release:** step 2, then (own go) step 3.
- **Close:** docs update, `make knowledge-index-update`, scoped tests (none new in `src/`), paths guard before any push, tell perf-planner before commits.

## Risks
- py-spy samples can attribute a line to the caller when a C function is running; the classifier reports the share of samples whose `refine` frame line is ambiguous (outside both a timed block and any known untimed span).
- A profile at one commit: the line ranges must be read from the same commit's `pipeline.py`, so the script takes the repo root as input and the header records the sha.
- Sampling slows ticks; compare the tick table with `--sampler none` once (cheap) so the shares are not read as absolute ms.
