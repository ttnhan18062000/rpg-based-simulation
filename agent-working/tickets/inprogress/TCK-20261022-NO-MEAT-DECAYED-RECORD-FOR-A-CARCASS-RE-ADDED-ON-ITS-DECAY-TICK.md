---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK
phase: open
date: 2026-10-22
tags: []
---

# TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK

## Title
No MEAT_DECAYED record for a carcass that a same-tick partial take re-adds on its decay tick (emitter-only, hash-neutral; (a1) of the v1 V2 split)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
v1 gate run 39710919027 (main e6a6a3e10) failed V2 on crowded_frontier/44 (decay records 148 vs vanished 145) and frontier_living_world/46 (139 vs 138). Trace (rpg-implementer, `/mnt/data/scratch-rpg-implementer/v1_v2_meat_trace.md`): a carcass due to decay is partly eaten the same tick (EAT, CORPSE_FOOD, accepted); the world-dynamics step has written MEAT_DECAYED from the tick-start state; `apply_plan.py` ~265-277 pops the body and re-inserts it from `corpses_add_or_update`, so the body survives a tick and the record is false (crowded/44 t1604 body 1000007 3.0; frontier/46 t2575 body 1000030 1.0). Conservation holds (residual 0).

OWNER DECISION 2026-10-22 14:07 +07 (AskUserQuestion in the rpg-planner session, "Split (Recommended)"), designer recommendation: SPLIT. (a1) = THIS ticket before v1: make the record true about the world as built, without changing the world. (b1) = TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME after v1 (apply order, the law), disclosed in v1 as N16.

## Scope
1. Extend the MEAT_DECAYED filter in `src/engine/economy.py` (`_without_decay_of_looted_bodies`, ~261-287): a body that is in the update's `corpses_remove` AND re-added in `corpses_add_or_update` in the same resolution gets no decay record (it did not leave; it is recorded when it actually leaves). Whole-body loot behaviour unchanged. Cover the lifecycle phase's second resolution as the existing filter does.
2. Tests: unit fixtures for the two traced cases (partial take on the decay tick -> no record that tick, record of the remainder the tick it leaves; last meat taken on the decay tick -> no meat record) plus the existing `tests/unit/engine/test_meat_decay_record_and_whole_loot.py` unchanged.
3. Parity: amend the existing MEAT-DECAYED-V2 parity entry's evidence for the re-added case (no Bible change; the decay-timing deviation is N16, owned by (b1)).

## Out of Scope
Any change to `apply_plan.py`, corpse lifecycle, decay timing or world state ((b1)). Gate metric changes (fix the emitter, never the check). v1 disclosure text (rpg-designer).

## Acceptance Criteria
- HASH-NEUTRAL PROOF (designer condition 1): `paired.py --base e6a6a3e10 --new <fix sha> --seeds 42..46 --self-check off --jobs 1`, 3 worlds, 5000 ticks, PYTHONHASHSEED=0, audit_mode: start and final hashes equal in all 15 runs and every counter equal EXCEPT the MEAT_DECAYED count/quantity, which drops by exactly 3.0 on crowded_frontier/44 and 1.0 on frontier_living_world/46 and nowhere else. Any other difference: STOP, report to rpg-planner (the split collapses; back to the owner).
- V2 0 violations on crowded/44 and frontier/46 at the fix sha (ledger check); unit tests pass; code health 0 new / 0 worse; mypy clean.
- `tools/rpg_measure/arm_child.py` hash unchanged (72320cac).

## Related Tickets
TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME ((b1), removes this filter); TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2 (whole-body case); TCK-20261019-RECORD-BASELINE-V1.

## Related Docs
docs/mechanics/03_economic_laws.md 3.2; docs/parity_ledger/ (MEAT-DECAYED-V2 entry).

## Related Stored Artifacts
agent-working/staging_artifacts/TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK/ (plan, investigation with the trace summary, test_plan); the full trace report is scratch (v1_v2_meat_trace.md) and is summarised in the investigation.

## Related Code Areas
src/engine/economy.py; src/engine/world_dynamics.py (`_meat_decayed_events`); src/observability/run_ledger.py (reader only).

## Assumptions / Open Questions
- MEAT_DECAYED is read only by observability (run_ledger, rpg_gate_metrics) and world events are not in CanonicalStateHasher, so hash-neutral is expected; the proof decides.

## Implementation Notes
`src/engine/economy.py` `ResourceTransactionSystem._without_decay_of_looted_bodies(events, removed_by_transfer, readded=None)`: besides the bodies an accepted whole-body loot removes, a body that is in the resolution's `corpses_remove` AND in its `corpses_add_or_update` gets no MEAT_DECAYED record (`readded=set(new_corpses_remove) & {c.id for c in new_corpses_update}` at the call site in `resolve_all`). Both lists include the earlier resolution's entries (the second, lifecycle-phase resolution starts from the update with its lists and world events), so the second resolution is covered too. No change to `apply_plan.py`, the corpse lifecycle, decay timing, world state or the gate metrics. The body that is re-added decays a tick late (the apply path pops the decayed body and then re-inserts the replacement); that is (b1). The parity ledger has no entry named MEAT-DECAYED-V2; the decision-44 meat entry TOWN-205 carries the evidence line.

## Test Summary
tests/unit/engine/test_no_meat_decay_record_for_a_readded_carcass.py (3): the crowded/44 case (3 meat, one eaten on the decay tick: no record that tick, the 2 left recorded the tick the body leaves, books agree: made 3 = taken 1 + vanished 2); the frontier/46 case (1 meat eaten on the decay tick: no meat record at all, made 1 = taken 1); the control (a body that decays with nobody eating keeps its one record). The first two fail without the fix, all pass with it. tests/unit/engine/test_meat_decay_record_and_whole_loot.py unchanged (3 pass). tests/unit/engine + observability + core: 2197 passed, 4 skipped. `codebase.health check`: 0 new, 0 worse. mypy gate 0. lint-imports 17 kept. The paired hash-neutral proof is recorded in the Completion Summary.

## Files Changed
src/engine/economy.py; docs/parity_ledger/town_resource.yaml (TOWN-205 evidence); tests/unit/engine/test_no_meat_decay_record_for_a_readded_carcass.py (new).

## Completion Summary
