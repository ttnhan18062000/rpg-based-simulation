---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1
phase: open
date: 2026-10-26
tags: [performance, combat, investigation]
---

# TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1

## Title
Profile and name what is left of combat_engagement's per-pair `_consider` cost after H1 (~1.6 s per tick, 70 % of the tick at 1000 entities)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
H1 (#751, `35e80fb56`) indexed the hostility relation lookups. `combat_engagement` at movement[1000] went from about 1.8 s to about 1.6 s per tick, still about 70 % of a 2.2 to 2.5 s tick. The rest is other per-pair work in `CombatEngagementPhase._consider`, which nobody has profiled.

rpg-planner filed this follow-up on its seat branch and handed it to perf, measurement-only, on the H3/H4 pattern (#593 issuecomment-6420451647). This is the perf-lane copy; rpg drops its own.

History, from H1's Implementation Notes:
- H1's bisect put the step at `132bf09ca`, where the phase started evaluating pairs. The candidates are #190 (`1e075b807`) and #192 (`6dd2ccd12`); the single commit was not named.
- #395 added no per-pair cost.
- H1 itself does not need re-measuring.

This ticket gates the full capacity run (`TCK-20261026-PERF-CAPACITY-SIZING-PROBE-AT-10K-ENTITIES`).

## Scope
1. On a lead-granted heavy-run slot, one process at a time, pinned:
   - Command: `python3 tools/perf/profile_tick.py --scenario movement --entities 1000 --warmup 2 --ticks 6 --contract pinned --sampler none`, seed 42, `PYTHONHASHSEED=0`.
   - Then one py-spy run of the same command, to name the costs inside `_consider` and its per-pair callees.
   - Use 3 serial runs; report the median and range.
2. Optional: time `1e075b807` and `6dd2ccd12` against their parents (`git archive` arms, alternating) to name the step's commit.
3. Propose hash-neutral fixes, for example per-tick memoisation of pair-invariant reads, or candidate-pair pruning. Each fix ships only with `paired --neutral` IDENTICAL on 3 worlds × s42 plus alternating-pair before/after timing. That check measures neutrality, not behaviour coverage.

## Out of Scope
- Engagement semantics. A fix that changes behaviour is a separate decision, gated by the owner and rpg.
- The digest and replay cost (T3, F1).
- The collection-phase growth: `TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION`.

## Acceptance Criteria
- A profile names at least 80 % of `combat_engagement` time, recorded in `docs/performance/tick_cost_growth.md` and staging `evidence.md`, PROVISIONAL.
- Each landed fix has neutral IDENTICAL on 3 worlds × s42 plus alternating-pair timing. Otherwise the ticket closes as an investigation.

## Related Tickets
- `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` (H1, done)
- `TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION`
- `TCK-20261026-PERF-CAPACITY-SIZING-PROBE-AT-10K-ENTITIES`
- `TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION`

## Related Docs
- `docs/performance/tick_cost_growth.md` (§7, the rpg hand-off)
- #593 issuecomment-6420451647

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/combat_engagement/`: rpg-owned. A code fix is co-edited with rpg review, under the same pattern as H1.
- `tools/perf/profile_tick.py`

## Assumptions / Open Questions
- Whether a fix lands here or goes to rpg depends on what the profile names. The perf deliverable is the attribution.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
