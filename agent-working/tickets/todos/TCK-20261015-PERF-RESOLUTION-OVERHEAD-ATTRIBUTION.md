---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION
phase: open
date: 2026-10-15
tags: [performance, benchmarking]
---

# TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION

## Title
Attribute `resolution_overhead` (12-33 % of every tick) to named call sites, with folded-stack evidence

## Status
OPEN

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
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(to be filled)
