---
status: historical
layer: economy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK
tags: []
---

# plan - TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK

## Plan
1. `economy.py` `_without_decay_of_looted_bodies`: take a `readded` set (bodies in `corpses_remove` and in `corpses_add_or_update` of the same resolution) and drop their MEAT_DECAYED record, as whole-body loot already does.
2. Unit fixtures for the two traced cases and a control; the existing whole-loot test unchanged.
3. Parity: add the filter and the tests to the decision-44 meat entry's evidence (TOWN-205).
4. Proof (the acceptance gate): `paired.py --base e6a6a3e10 --new <sha> --seeds 42..46 --self-check off --jobs 1`, 15 runs: start and final hashes equal, every counter equal except MEAT_DECAYED (-3.0 on crowded/44, -1.0 on frontier/46); V2 = 0 on both; `arm_child.py` hash 72320cac.

## Scope guards
No change to `apply_plan.py`, corpse lifecycle, decay timing, world state or the gate metrics ((b1) owns the timing).
