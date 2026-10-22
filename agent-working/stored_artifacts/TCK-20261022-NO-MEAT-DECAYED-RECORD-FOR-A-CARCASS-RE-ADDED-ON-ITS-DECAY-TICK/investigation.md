---
status: historical
layer: economy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK
tags: []
---

# investigation - TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK

## Finding (summary of the V2 meat trace, 2026-10-22)
v1 gate run on e6a6a3e10 failed V2 on crowded_frontier/44 (decay records 148 vs vanished 145) and frontier_living_world/46 (139 vs 138). Both are clean on 7b1528861. Traced with the gate harness (audit_mode, PYTHONHASHSEED=0, 5000 ticks):
- crowded/44 tick 1604, body 1000007 (meat 3): the decay step is due and writes MEAT_DECAYED 3.0 from the tick-start state and lists the body in `corpses_remove`; entity 37 eats at the carcass the same tick (EAT, CORPSE_FOOD, raw_meat x1, accepted, hunger 40.1 to 20.2); the economy puts a smaller body (2 meat) in `corpses_add_or_update`; `apply_plan.py` (lines 265-277) pops the body and then re-inserts the replacement, so it survives. The next tick it decays again: a second record of 2.0, vanished 2.0. Balance: 3 = 2 left by decay + 1 eaten. The ledger's second equation holds (made 162 = taken 12 + looted 5 + vanished 145 + remaining 0).
- frontier/46 tick 2575, body 1000030 (meat 1): the same mechanism, the 1 meat eaten by entity 36 (hunger 80.4 to 60.5), the empty body kept and gone a tick later.
- Reproduced at 23fbe0ecf (the dead-are-not-threats step) and e6a6a3e10; absent at 7b1528861 (135 = 135). The mechanism is old code that the step-1 behaviour (living subjects staying near and eating at corpses) exposes.
Conclusion: an emitter gap, conservation holds. The fix (a1) makes the record true about the world as built; the decay timing is (b1).
