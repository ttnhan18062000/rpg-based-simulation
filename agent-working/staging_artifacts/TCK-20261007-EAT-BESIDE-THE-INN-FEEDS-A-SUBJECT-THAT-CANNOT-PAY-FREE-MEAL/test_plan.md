---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL
artifact_type: test_plan
tags: []
---

# Test plan
- Constructed: a broke subject at an inn issues EAT: hunger unchanged, gold unchanged, the transfer rejected (ACTION_EXHAUSTION), the building's purse unchanged; a subject holding exactly the price: paid in full, hunger drops by the ruled relief, building credited, in one accepted transfer (atomic: no state where hunger fell and gold did not).
- Same for REST (a broke subject gets no bed, no hp, no readiness).
- EAT with nothing carried and no inn in reach: no hunger change, typed failure reason, task ends (no free 40).
- Carried food and carcass meals unchanged.
- Undeclared-diet kind (merchant) with nothing: no relief (the V1 writer is closed), with food or coin: eats.
- Scorers: EatScorer/FatigueScorer do not offer the inn to a subject that cannot pay; do offer it to one that can.
- Conservation: total coin conserved across a paid meal (building purse +5, subject -5) and across a refused one (0 change).
- Gate: run the gate's compute on a 1500-tick world: V1 = 0 (the known-red entry is removed in the same commit, and the registry test stays green).
- Pinned 5 seeds x 3 worlds, two-run digests, measurement tables as in investigation.md.
