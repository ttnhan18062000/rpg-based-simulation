---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07
artifact_type: investigation
tags: [combat, cognition, agency]
---

# Investigation

- `safety_pressure` is `min(1, max(need safety level, drive safety level))` from the catalog profiles (`src/world/motivation/pressure_resolver.py`), a static trait; the gate was `hostiles and safety_pressure > 0.75` (`tactical.py`). `hostiles` come from the saliency window (radius 10, 5 targets), the perception gate and `is_hostile_compat` with the real `combat_engaged`; PANIC_RETREAT uses `are_entities_hostile` with `combat_engaged=True`, a different predicate.
- Standard worlds: every entity has no need or drive profile (38 of 38, 49 of 49), so `safety_pressure` is 0 and the branch is dead; only catalog-spawned campaign entities have profiles.
- Before (main `3e466e132`, campaign, 70 ticks): 19 decisions, all HP 1.0, `safety_pressure` 0.9, 14 with one hostile, none targeted, nearest hostile 0.8 to 12.5 tiles. Profiles: humanoid_survival 14 (drives opportunistic_raider 7, profit_seeker 4, disciplined_protector 2, cautious_commoner 1), goblin_survival 5.
- After (this branch): 12 decisions (7 and 5), each with a named term. Per decision (seed/tick, entity, HP, terms, hostile distances, targeted, power ratio of near hostiles to own): 42+1337 t1 id19 1.0 OUTMATCHED [4.0] no 2.2x; t13 id17 0.914 ADJACENT+TARGETED+CLOSING [0.8,2.3,8.7] yes 1.31x; t16 id14 1.0 ADJACENT+CLOSING [0.5,9.1] no 0.45x; t22 id18 1.0 CLOSING [2.0] no 1.44x; t34 id16 0.657 WOUNDED [7.2,8.7,11.9] no 0.0x; seed 42 only: t27 id13 1.0 TARGETED [11.5] yes 0.0x; t55 id15 1.0 ADJACENT+TARGETED+CLOSING+OUTMATCHED [0.5,0.6,1.5,2.4,2.6] 3 of 5 3.65x. Weakest as threats: id13, id16, id19; kept (the Rule lists them; a cap is tuning).
- Cooperation share (NORMAL pin, `episode` fixture replicated per seed, two identical runs): seed 42 797 of 1512 = 0.5271 to 839 of 1691 = 0.4962; seed 1337 635 of 1375 = 0.4618 to 451 of 1266 = 0.3562. The seed-42 fall is non-cooperation events growing (1512 to 1691), not cooperation shrinking (797 to 839).
- Probes (scratchpad, not committed): `safety_probe.py`, `share_probe.py`.
