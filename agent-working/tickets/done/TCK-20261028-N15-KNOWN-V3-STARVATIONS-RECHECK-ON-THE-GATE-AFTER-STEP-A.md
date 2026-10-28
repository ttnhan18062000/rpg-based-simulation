---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261028-N15-KNOWN-V3-STARVATIONS-RECHECK-ON-THE-GATE-AFTER-STEP-A
phase: done
date: 2026-10-28
tags: [benchmarking]
---

# TCK-20261028-N15-KNOWN-V3-STARVATIONS-RECHECK-ON-THE-GATE-AFTER-STEP-A

## Title
N15 known V3 starvations (crowded_frontier/46 raider 38, frontier_living_world/44 worker 2): re-check on the gate after HUNGER step A, then retire or keep the known-red entry with evidence

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`tools/test_architecture/rpg_gate_known.yaml` holds a scoped V3 fail entry for the N15 v1 known reds
(crowded_frontier/46 raider 38, starved t3778; frontier_living_world/44 worker 2, starved t3736), accepted by the
owner on #715 6337993346, owner rpg-planner, expires 2026-11-05. Its owning ticket was
TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (HUNGER step B and step A). Step A closed with #769, so the
entry needs a live owner (`test_known_reds.py`: a done owner ticket means the entry is stale). Whether steps B and A
cleared these two starvations on the gate has NOT been measured: the gate's V3 reading comes from the gate harness,
not from paired runs. The paired 5000t arms (audit mode) show both entities dying by COMBAT/DEFEAT, not starvation,
at 3533fde71, 358f4cb7f and 957caf8f6, so paired results do not reproduce the gate's case and cannot retire it.
This ticket owns the entry until the gate answers.

## Scope
1. Run the rpg gate (the harness that produced the v1 V3 reading) on main after #769 merges, for at least
   crowded_frontier s46 and frontier_living_world s44. A full gate run on main through the workflow needs the owner's
   go, asked through lead-planner-u24 (#715 6459766303).
2. If neither entity has a V3 fail: retire the entry in the same change, citing the run.
3. If either still fails V3: keep the entry for exactly the cases still failing, and report to rpg-planner with
   the trace (tick, cause, and whether the subject was fleeing a non-acting hostile, the N15 shape). The entry's
   expiry (2026-11-05) is not extended here; an extension is an owner ask.
4. If a different V3 fail appears on these (world, seed) pairs, it is a regression: STOP and report.

## Out of Scope
- Any behaviour change. The held retreat flight (post-M1) is a candidate fix for N15 and is not done here.

## Acceptance Criteria
1. A gate reading at or after the #769 merge for the two (world, seed) pairs, cited by run id.
2. The known-red entry retired or narrowed to what still fails, matching that reading.
3. Done before 2026-11-05, or the expiry question raised to the owner before then.

## Related Tickets
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (steps B and A; the previous owner)
- TCK-20261019-RECORD-BASELINE-V1 (the v1 gate reading)

## Related Docs
- tools/test_architecture/rpg_gate_known.yaml
- v1_disclosure.md M5

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE/

## Related Code Areas
- tools/test_architecture/ (gate harness and known file, read only except the entry)

## Assumptions / Open Questions
- Owner of the entry: rpg-planner (unchanged).

## Implementation Notes
Gate reading: rpg-gate-report run 40653115297 (workflow_dispatch by the owner, #715 6463707752), head 2c4869d61 (includes #769). The report's stale_known_entries lists crowded_frontier/46/38 and frontier_living_world/44/2 as no longer failing V3. Entry removed from tools/test_architecture/rpg_gate_known.yaml.
Earlier runs 40490584465 (2afdba653) and 40314093440 (3533fde71), both before #769, already listed both entries as stale, so step A did not clear them; they were already clear.

## Test Summary
tests/unit/tools/test_known_reds.py: 57 passed.

## Files Changed
- tools/test_architecture/rpg_gate_known.yaml (N15 entry removed)

## Completion Summary
N15 entry retired on the gate reading above. The N14 entry (urban_political/44/28) is also stale at 40653115297 and was left in place (owner-accepted exception, own ticket, expiry 2026-11-05; rpg-planner sequences its retirement). Reported to rpg-planner, not owned by this ticket: unowned V3 frontier_living_world s43 merchant 38 t2518 is new since 2afdba653 (absent in both earlier runs); V6 frontier_living_world s45 and V3 crowded_frontier s42 leader 30 were already present before #769.
