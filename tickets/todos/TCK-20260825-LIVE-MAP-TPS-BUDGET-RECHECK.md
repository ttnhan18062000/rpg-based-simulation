---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK
phase: open
date: 2026-08-25
tags: [performance, engine]
---

# TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK

## Title
Re-measure 500-entity tick throughput on uncontended hardware -- disentangle genuine engine compute
cost from sandbox resource noise

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s live measurement session observed ~7.9 ticks/sec at 500
entities against `V2EngineManager`'s nominal 20 TPS (`self._tick_rate = 0.05`), implying ~0.076s of
tick-compute cost -- well above the `cli_default` profile's `max_tick_budget_ms=50.0`. The
measuring ticket explicitly could not disentangle whether this reflects genuine 500-entity pipeline
compute cost on 4 cores, or this specific sandbox's severe resource contention (swap at
3.9-4.0/4.0GB used, ~156-240MB free RAM at session start, confirmed shared with other concurrent
sessions on the same machine) inflating wall-clock cost. This ticket's only job is to re-run the
exact same, already-built measurement on a less-contended host and report the real number --
narrow, self-evident intent, no design decisions involved.

## Scope
- Re-run `tools/perf/live_map_ws_payload_measure.py --entities 500 --seed 42` (built and proven
  working by `TCK-20260821-LIVE-MAP-PERF-VALIDATION`, needs no code changes) on a host with real,
  uncontended headroom -- confirm via `free -h`/`nproc` before running that available RAM and swap
  usage look nothing like the original ~1.2GB-available/near-full-swap conditions.
- Record observed ticks/sec (or ms-per-tick) and compare directly against
  `cli_default`'s `max_tick_budget_ms=50.0` (`docs/engine/performance_contract.md`).
- If the re-measured number is still well below 20 TPS / above the 50ms budget on genuinely
  uncontended hardware, that promotes this from "environment artifact, unconfirmed" to a real
  engine performance finding -- file this as its OWN new follow-up ticket at that point (do not fix
  the performance issue in this ticket; this ticket is measurement-only, same constraint as its
  parent).
- If the re-measured number comes in at or near the 20 TPS nominal target, close this ticket with
  that finding -- "sandbox resource contention was the explanation, no real engine issue" is a
  complete, valid outcome.

## Out of Scope
- Fixing any performance issue this re-measurement confirms (that's a new ticket's job, per Scope
  above).
- Any change to `tools/perf/live_map_ws_payload_measure.py` itself, unless the re-run surfaces a
  genuine bug in the script (not expected -- it already worked correctly in the parent ticket).
- Re-measuring payload size or the CLASS_B(2500-entity) scale -- this ticket is narrowly scoped to
  the TPS/tick-throughput question only.

## Acceptance Criteria
- [ ] `tools/perf/live_map_ws_payload_measure.py --entities 500` re-run on a host with confirmed
      uncontended memory/CPU (stated explicitly: `free -h`/`nproc` output at time of run)
- [ ] Observed ticks/sec (or ms/tick) reported and compared against the 20 TPS nominal /
      `max_tick_budget_ms=50.0` budget
- [ ] A clear conclusion stated: either "sandbox noise explains the original ~7.9 TPS finding, no
      real engine issue" (ticket closes here), or "confirmed real engine performance gap" with a
      newly-filed follow-up ticket cited for the actual fix

## Related Tickets
- TCK-20260821-LIVE-MAP-PERF-VALIDATION (origin of this finding -- report.md's AC4 Finding 3)

## Related Docs
- docs/engine/performance_contract.md (`max_tick_budget_ms`, Scoped Claims discipline)
- docs/performance/perf_baseline_policy.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION (report.md's Finding 3 and "Resource
  Conditions During This Session" section have the full original measurement and its caveats)

## Related Code Areas
- tools/perf/live_map_ws_payload_measure.py
- src/api/engine_manager.py (`V2EngineManager._tick_rate`, `_run_loop`)
- docs/engine/performance_contract.md (`cli_default` profile's `max_tick_budget_ms`)

## Assumptions / Open Questions
- Whether a genuinely uncontended host is available to this project's agents at all -- if every
  available execution environment is similarly resource-constrained, this ticket may itself end up
  reporting "could not obtain an uncontended measurement" as its own honest outcome, same pattern as
  its parent ticket's CLASS_B/Playwright blockers.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
