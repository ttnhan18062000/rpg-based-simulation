---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261019-SOAK-WATCHDOG-BUDGET-OVERRUNS-NEED-A-QUIET-HOST-READING
phase: open
date: 2026-10-19
tags: []
---

# TCK-20261019-SOAK-WATCHDOG-BUDGET-OVERRUNS-NEED-A-QUIET-HOST-READING

## Title
The #646 soak logged 30 tick budget overruns; read them again on a quiet host before calling them a defect

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
The 30 min Redis 8.10.2 soak for PR #646 passed (stream lag and pending 0, 0 restarts). Its backend still logged 30 CRITICAL `WatchdogTrip` alerts. These are the kernel's budget-overrun telemetry (`src/engine/kernel.py` `_report_budget_overrun`); they never change outcomes. The soak ran on a shared dev host under contention, and there is no baseline to compare against. This ticket finds out whether the overruns are real engine cost or host noise.

## Scope
- Run the default compose world with the local-dev profile for about 4000 ticks on a quiet host. Run it on main, both with the in-process stream and with redis. Record every `WatchdogTrip` with its site, compute_ms, threshold_ms and phase_costs.
- Classify each overrun:
  - a steady slow phase, which is an engine defect;
  - a single-phase spike of about 60-70 ms that moves between phases, which is a GC pause or host stall;
  - a periodic spike about every 600 ticks, which points to a periodic system to name.
- If an overrun is real, file the fix ticket. If not, close with the reading.

## Out of Scope
- Changing the watchdog thresholds or the adaptive limit.
- Redis or compose changes (platform).

## Acceptance Criteria
- A table of overruns per run (site, tick, compute_ms, threshold_ms, dominant phase), with the host load noted.
- A verdict: engine cost (with a named phase and a fix ticket), periodic system (named), or host noise.
- Redis 8 and the in-process stream are compared in the same quiet-host session.

## Related Tickets
- PR #646 (window: redis 8, starlette 1.x); platform soak comment https://github.com/ttnhan18062000/rpg-based-simulation/pull/646#issuecomment-6258173087
- TCK-20261018-TWO-BARE-KERNEL-TESTS-DEPEND-ON-HOST-MEMORY (host-memory sensitivity of the governor)

## Related Docs
- docs/architecture/simulation_watchdog.md
- docs/engine/performance_contract.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/kernel.py (`_report_budget_overrun`, end_of_tick and mid_tick sites)
- src/observability/alerts/models.py (`create_watchdog_trip`)

## Assumptions / Open Questions
- Evidence so far comes from platform-implementer's transcript, for 7 of the 30 alerts. The soak containers were removed, so the full log is gone. Run id: run_1792349708_5169_1_9cfe67ef.
  - Mid_tick, tick N/A: 202.96 ms against a 50 ms threshold; collection 70.7, init 10.7.
  - End_of_tick, ticks 605, 1211, 1898, 2479, 3125 and 3728 (about 600 apart):
    - 24-77 ms against adaptive thresholds of 20.0-37.8 ms;
    - the dominant phase varies: resolution_overhead about 66 ms (ticks 1898 and 3125), combat_engagement 63.6 ms (3728), advancement plus persistence about 17 ms each (605).
- The setup was the default compose stack, the local-dev profile and the engine's default world, with mem_limit 1g, on a shared host where a docker build had just finished.
- Working hypothesis: GC pauses or host stalls. The roughly 600-tick spacing is the one clue against that and is worth checking first.

## Implementation Notes
After v1. Not a blocker for #646.

## Test Summary

## Files Changed

## Completion Summary
