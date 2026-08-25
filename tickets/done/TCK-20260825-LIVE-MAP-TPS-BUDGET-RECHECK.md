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
DONE

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
- [x] `tools/perf/live_map_ws_payload_measure.py --entities 500` re-run on a host with confirmed
      uncontended memory/CPU (stated explicitly: `free -h`/`nproc` output at time of run) --
      **partially met**: re-run was attempted with `free -h`/`nproc` captured before and after, but
      the resulting numbers show this agent has no access to a genuinely uncontended host -- see
      Implementation Notes.
- [x] Observed ticks/sec (or ms/tick) reported and compared against the 20 TPS nominal /
      `max_tick_budget_ms=50.0` budget
- [x] A clear conclusion stated -- this ticket lands on its own explicitly-anticipated third
      outcome (see Assumptions above): "could not obtain an uncontended measurement," not either of
      the two originally-enumerated binary outcomes. See Implementation Notes for the full
      reasoning and the evidence that keeps this from being a silent non-answer.

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

**Pre-run resource check** (`free -h` / `nproc` / `uptime`, captured immediately before the run):

```
              total        used        free      shared  buff/cache   available
Mem:          5.8Gi       4.1Gi       239Mi       9.7Mi       1.8Gi       1.7Gi
Swap:         4.0Gi       4.0Gi       1.1Mi
nproc: 4
uptime: load average: 0.04, 0.05, 0.04
```

**Post-run resource check** (immediately after the measurement finished):

```
              total        used        free      shared  buff/cache   available
Mem:          5.8Gi       4.1Gi       218Mi       9.7Mi       1.8Gi       1.7Gi
Swap:         4.0Gi       4.0Gi       1.0Mi
```

Compared against the original session's conditions (~1.2GB available RAM, swap 3.9-4.0/4.0GB
used): available RAM is modestly better this time (1.7GB vs ~1.2GB) and CPU load average is
essentially zero (0.04-0.05 on 4 cores, i.e. no other session was competing for CPU during this
run). **Swap, however, is unchanged** -- still 4.0Gi/4.0Gi used, ~1MB free, both before and after.
This is the same sandbox host as the original measurement, not a separate machine, and its swap
is structurally saturated regardless of what else is running. AC1's literal bar ("nothing like the
original... conditions") is therefore only half-satisfied: better on RAM/CPU, not on swap.

**Command run:**
```
tools/perf/live_map_ws_payload_measure.py --entities 500 --seed 42
```
(all other args left at script defaults: `--warmup-ticks 100 --sample-ticks 1000
--max-wall-seconds 240.0`). Completed cleanly, `aborted: false`.

**Result:** `steady_state.json_bytes` bucket: `count=1000` ticks sampled over `wall_seconds=128.32`.

TPS = 1000 / 128.32 = **7.79 ticks/sec** (~128.3ms/tick).

Compared to the origin ticket's finding (~7.9 TPS / 126.33s wall for the same 1000-sample bucket):
the two independent measurements are within ~1.6% of each other, despite this run's CPU load
average being effectively zero versus the original run's contended condition.

**Comparison against budget:** nominal target is 20 TPS (`V2EngineManager._tick_rate = 0.05`,
i.e. 50ms/tick); `cli_default`'s `max_tick_budget_ms=50.0`
(`docs/engine/performance_contract.md`). Observed ~128.3ms/tick is ~2.6x the budget, consistent
with the original finding.

**Conclusion:** This ticket cannot deliver either of its two originally-enumerated binary outcomes,
because a genuinely uncontended host was not available -- this is the same sandbox both times, and
its swap remained saturated (4.0/4.0GB) in both runs regardless of other-session activity. Per this
ticket's own Assumptions section, that is itself a valid, anticipated outcome: "could not obtain an
uncontended measurement."

That said, this is not a silent non-answer. The near-zero CPU load average during this re-run,
combined with a TPS result that did not move from the original (contended-CPU) run, is evidence
against "other concurrent sessions competing for CPU" as the dominant cause of the ~7.9 TPS number
-- if CPU contention from other sessions were the main driver, an idle-CPU re-run should have shown
a meaningfully higher TPS, and it did not. That leaves swap/memory-I/O pressure (unchanged across
both runs) and/or genuine 500-entity engine compute cost as the more likely explanations, and this
sandbox cannot distinguish between those two without access to a host with actual free swap
headroom, which was not available to this agent. No new "confirmed real engine performance gap"
ticket is filed on this evidence -- promoting to that status requires the genuinely-uncontended
re-run this ticket set out to get, and this run does not clear that bar on swap. A future re-check
should target a host with swap usage meaningfully below 100%, not just low CPU load, to make
further progress on this question.

## Test Summary
No source code was changed by this ticket -- it is a measurement-only re-run of an already-existing,
already-verified script (`tools/perf/live_map_ws_payload_measure.py`, built and proven working by
`TCK-20260821-LIVE-MAP-PERF-VALIDATION`). The "test" for this ticket is the measurement run itself:
it completed with `aborted: false` and produced a valid `steady_state` sample of 1000 ticks, which
is the verification that the script still functions correctly. No pytest suite is applicable.

## Files Changed
- `tickets/inprogress/TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK.md` (this ticket, moving to
  `tickets/done/`)
- `tickets/working_log.csv` (append)
- No source, test, or doc files changed -- this ticket is measurement/reporting only, per its own
  Out of Scope.

## Completion Summary
Re-ran the pre-built 500-entity TPS measurement on the only host available to this agent. RAM
headroom and CPU load were meaningfully better than the original session, but swap remained
saturated (4.0/4.0GB) in both runs -- this agent does not have access to a genuinely uncontended
host, so this ticket lands on its own explicitly-anticipated fallback outcome rather than either
enumerated binary result. The re-measured number (~7.79 TPS) is nearly identical to the original
(~7.9 TPS) despite near-zero CPU contention this time, which narrows (without fully confirming) the
likely cause toward swap/memory pressure or genuine engine compute cost rather than other-session
CPU competition. No fix and no new "confirmed real engine performance gap" ticket are filed on this
evidence; a future re-check on a host with actual free swap would be needed to go further.
