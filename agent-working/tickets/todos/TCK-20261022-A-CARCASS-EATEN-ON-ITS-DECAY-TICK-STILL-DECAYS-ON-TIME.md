---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME
phase: open
date: 2026-10-22
tags: []
---

# TCK-20261022-A-CARCASS-EATEN-ON-ITS-DECAY-TICK-STILL-DECAYS-ON-TIME

## Title
A carcass partly eaten on its decay tick is re-inserted by the apply order and decays a tick late; its MEAT_DECAYED record overstates (V2 fail on 2 of 15 v1 gate runs)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
v1 gate run 39710919027 (main e6a6a3e10) failed V2 (meat books) on crowded_frontier/44 (meat_decayed_events 148 vs vanished_with_bodies 145) and frontier_living_world/46 (139 vs 138). Traced by rpg-implementer (Lane A), write-up `/mnt/data/scratch-rpg-implementer/v1_v2_meat_trace.md`, evidence `v2meat/focus_crowded44.json`, `v2meat/focus_frontier46.json`.

Mechanism (one record per run): crowded/44 t1604 body 1000007 (meat 3) is due to decay; the world-dynamics step lists it in `corpses_remove` and writes MEAT_DECAYED 3.0 from the tick-start state. The same tick entity 37 EATs at the carcass (EAT, source CORPSE_FOOD, raw_meat x1, accepted) and the economy emits a corpse update (2 meat) in `corpses_add_or_update`. `src/engine/apply_plan.py` ~265-277 pops the body (decay, then `corpses_remove`) and then re-inserts it from `corpses_add_or_update`: the body survives, is edible for one more tick, and decays at t1605 (record 2.0). frontier/46 t2575 body 1000030 (meat 1): entity 36 eats the last meat, the body is re-added with 0 meat, record 1.0, the body leaves at t2576.

Conservation holds (per-body atom balance; ledger made = taken + looted + vanished + remaining, residual 0.0 on both runs). The defect is the one-tick-late decay and a false record. Old code, exposed by step 1 of v1 (the dead are not threats, divergence 2.136): reproduces at 23fbe0ecf (152 vs 149), clean at 7b1528861 (135 = 135).

Designer ruling 2026-10-22 (shape ii is the law; record-only fix is not acceptable): Bible 05 (Corpses: a body stays for a fixed duration, decay_tick, then is permanently removed), Bible 03 3.2 (CORPSE_DECAY is the typed sink for the meat left), Bible 03 Rewards (coin drops as a ground purse at decay).

## Scope
1. On the decay tick a same-tick accepted take (EAT / loot) applies first, against the body's tick-start contents; it stays accepted and its atoms go to the taker.
2. The body then leaves on that tick: no re-insert from `corpses_add_or_update` for a body in `corpses_remove` (apply path). Its remainder after the takes is the CORPSE_DECAY sink; its coin becomes a ground purse as today.
3. MEAT_DECAYED is written from the applied remainder: crowded/44 t1604 = 2.0 and no t1605 event; frontier/46 t2575 remainder 0 follows the existing zero-meat decay convention, body gone at t2575.
4. Generalise `economy.py` `_without_decay_of_looted_bodies` (~261-287): whole-body transfer removal -> no decay record (unchanged); partial take on the decay tick -> remainder record. One rule: the record equals what actually left by decay.
5. Tests: unit fixtures for the two traced cases (partial take on the decay tick; last meat taken on the decay tick) plus the existing whole-body loot case (`tests/unit/engine/test_meat_decay_record_and_whole_loot.py`): conservation residual 0 and the body absent at decay_tick in all three.
6. Docs: parity entry next to the existing MEAT-DECAYED-V2 entry; Bible 03 3.2 clarifying sentence ("a take on the decay tick resolves before the decay; the remainder decays"), drafted by rpg-designer. No divergence (restores the Bible).
7. World-changing (body leaves a tick earlier): needs its own paired step (3 worlds x seeds 42-46 x 5000, audit_mode) and the gate V2 rows green on all 15 runs.

## Out of Scope
The record-only (emitter) fix alone (rejected by the designer). Other corpse lifecycle changes. Any v1 disclosure text (rpg-designer, N16 if the owner chooses disclose).

## Acceptance Criteria
- crowded_frontier/44 and frontier_living_world/46 at the fix sha: V2 0 violations; the traced bodies absent at their decay tick; MEAT_DECAYED equals the applied remainder.
- Unit fixtures as in Scope 5 pass; existing whole-body loot test unchanged and passing.
- Paired step reported with STOP rule; parity entry and Bible sentence landed with designer OK.

## Related Tickets
TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2 (whole-body loot case, done); TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (step 1 that exposes it); TCK-20261019-RECORD-BASELINE-V1.

## Related Docs
docs/mechanics/03_economic_laws.md 3.2; docs/mechanics/05_world_evolution.md (Corpses); docs/parity_ledger/ (MEAT-DECAYED-V2 entry).

## Related Stored Artifacts
/mnt/data/scratch-rpg-implementer/v1_v2_meat_trace.md (scratch, not durable; summarise into investigation.md).

## Related Code Areas
src/engine/apply_plan.py (corpse apply order); src/engine/economy.py (`_without_decay_of_looted_bodies`); src/engine/world_dynamics.py (`_meat_decayed_events`); src/engine/carcass.py.

## Assumptions / Open Questions
- Timing vs v1 is the OWNER's choice: (a) fix before v1 (v1 sha moves; 1b + gate re-run) or (b) disclose as N16 (false record + one-tick-late decay, conservation verified) and fix after v1. Designer recommends (b).
- Zero-meat decay record convention to be confirmed in code at investigation.
- Designer 2026-10-22 recommends SPLIT to the owner: (a1) emitter-only filter before v1 (separate ticket; no apply_plan/world change; proof = 3-world hashes + paired counters equal vs e6a6a3e10 except MEAT_DECAYED down by exactly 3.0 + 1.0) and (b1) = THIS ticket after v1. If (a1) lands first, its filter ("body in corpses_remove AND re-added in corpses_add_or_update -> no decay record") becomes unreachable under shape (ii) and is REMOVED in this ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
