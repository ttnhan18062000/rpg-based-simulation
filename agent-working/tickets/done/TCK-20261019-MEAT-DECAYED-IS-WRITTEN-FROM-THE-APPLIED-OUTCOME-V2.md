---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2

## Title
A body that decays and is looted whole on the same tick yields no MEAT_DECAYED record (v1 gate V2, crowded/43)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
v1 gate run 39212800104 failed V2 (meat conservation) in crowded_frontier seed 43: MEAT_DECAYED quantity 179 against 177 of meat that vanished with bodies. Traced (rpg-implementer-3, /mnt/data/scratch-rpg-implementer-3/v1_gate_fails_C.md): one body, 1000026, 2 raw meat, decay_tick 176. `world_dynamics._meat_decayed_events` writes the record from the start-of-tick state, before the transfers resolve; scout 15 took the same body whole by an accepted CORPSE transfer on the same tick (meat 0 to 2, conserved). The run ledger files it as looted, the record says decayed. Designer ruling (via rpg-planner): (a) fix the emitter, never the check: MEAT_DECAYED is written from the applied outcome; a body that leaves by an accepted whole-body loot on the same tick yields no decay record.

## Scope
`src/engine/economy.py` `ResourceTransactionSystem.resolve_all`: after the transfers resolve, drop the MEAT_DECAYED records of bodies an accepted CORPSE transfer removed in this resolution (covers the lifecycle phase's second resolution too). Regression test `tests/unit/engine/test_meat_decay_record_and_whole_loot.py`.

## Out of Scope
The V2 check and the run ledger (unchanged). Any other event emitter, even with the same intent-versus-outcome shape (listed below for the after-v1 audit). No state change: the body is removed exactly as before.

## Acceptance Criteria
- A body due to decay on tick T and looted whole on T gives one record (the loot); the meat ledger and the V2/H7 check agree.
- A body that only decays keeps exactly one MEAT_DECAYED record; a refused loot leaves the record.
- Final state hash identical on crowded seed 43, 5000 ticks, serial, base 864f7b281 against the branch; if it changes, stop and report.

## Related Tickets
v1 gate fails (rpg-planner); D80 decision 44 (meat sink)

## Related Docs
docs/mechanics/03_economic_laws.md (conservation); Bible 03 section 3.2

## Related Stored Artifacts
/mnt/data/scratch-rpg-implementer-3/v1_gate_fails_C.md (trace)

## Related Code Areas
src/engine/economy.py; src/engine/world_dynamics.py (`_meat_decayed_events`, unchanged); src/observability/run_ledger.py; src/observability/rpg_gate_metrics.py

## Assumptions / Open Questions
The event is removed at transfer resolution, not in world_dynamics, because the loot outcome only exists after `resource_transactions` (phase 30) and the lifecycle phase's second resolution; world_dynamics (phase 24) runs earlier. No new phase, so the phase inventory is unchanged.

## Implementation Notes
Same intent-versus-outcome pattern, NOT changed here, for the after-v1 "every event from the applied record" audit:
- `world_dynamics._feeding_kill_event`: FEEDING_KILL is "evaluated from the prior, kill-time state" (by design, noted in its docstring), before the kill is applied.
- The remaining `record_events` written by `WorldDynamicsSystem.resolve_dynamics` in phase 24 (decision-44 records) are written from the pre-transfer state; a same-tick transfer that changes what the record describes would show the same disagreement. Only MEAT_DECAYED has a measured case.
This list comes from reading the call sites near the fix, not an audit.

## Test Summary
- tests/unit/engine/test_meat_decay_record_and_whole_loot.py: 3 passed (first test fails without the fix: it finds the 12-unit MEAT_DECAYED record on a looted body). 65 passed across the meat, carcass, run-ledger, gate-metrics, corpse and economy tests in tests/unit/engine and tests/unit/observability.
- Hash proof, crowded_frontier seed 43, 5000 ticks, audit_mode, PYTHONHASHSEED=0, serial: base 864f7b281 and this branch (origin/main 4f6a44901 + fix) give the same final hash 1d8001bbe0c9cf86a2592a285de6f920d13c993a2e997184c1d64dbb86a67d1a. Ledger meat identical in both (made 191, taken 12, vanished 177, looted 2). Only the record differs: meat_decayed_quantity 179 on base, 177 on the branch, equal to `vanished`, so `_check_meat_books` passes (the 2-unit difference was body 1000026 at tick 176).

## Files Changed
src/engine/economy.py; tests/unit/engine/test_meat_decay_record_and_whole_loot.py

## Completion Summary
The decay record is dropped for a body an accepted whole-body loot takes in the same resolution; state and hash unchanged; V2 agrees on crowded/43.
