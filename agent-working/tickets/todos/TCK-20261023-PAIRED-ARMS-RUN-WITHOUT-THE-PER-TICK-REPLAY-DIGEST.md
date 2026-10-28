---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST

## Title
Paired arms run with no_replay (Mode 2), after perf's ruling (T3)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
T3 from docs/plans/architecture/faster_feature_testing_draft_tickets.md. rpg implements, testing reviews (agreed 2026-10-23); the gate stays in Mode 1 until this proof passes. Gate and paired arms run with audit_mode and no `no_replay` (rpg_gate_run.py:60-66), so Phase 7 computes the per-tick SHA-256 digest (kernel.py:1125): 9.2 % (strategic_100) to 27.1 % (frontier_extended) of a tick (tick_cost_growth.md section 4, PROVISIONAL), a lower bound because no_replay stops every replay emit. Paired proofs never read it: arm_child.py:58,69 hashes start and final state directly; neutral check paired.py:174-180 and self-check stats.py:125 compare those hashes plus fates and counters.

## Scope
NEEDS FIRST: perf-planner's ruling that no_replay in outcome runs is consistent with PERF-D1 A2 (its 5 conditions).
1. Pass no_replay in the paired arm kernel (arm_child build_kernel path).
2. It turns off every ReplayManager.emit (replay_manager.py:99): REFINED_UPDATE (kernel.py:657) and TICK_END too.
3. Verify: hashes identical with and without (no game logic reads replay_allowed); behaviour counters from simulation_events.jsonl (arm_child.py:35-36) still written; no paired/gate consumer reads the replay stream; the result manifest records the flag.
4. Whether the gate harness adopts it is testing's separate decision.

## Out of Scope
The gate harness switch (testing). Any digest-scheme change (F1, perf).

## Acceptance Criteria
- 3 worlds x seed 42 x 1000 ticks: start and final hashes, fates and counters identical with and without no_replay.
- Paired refuses to compare an arm run with replay against one without, unless the hashes prove them equal.
- Wall time per run before and after, same host (recorded via the T1 ledger row if it has landed).

## Related Tickets
TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (T1, testing); TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (T2, testing).

## Related Docs
docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
tools/rpg_measure/arm_child.py; tools/rpg_measure/paired.py; src/engine/replay_manager.py (read)

## Assumptions / Open Questions
rpg queue: after HUNGER step A and F3/F4 (the M1 record prerequisites).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
