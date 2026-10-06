---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING
phase: done
date: 2026-10-05
tags: [world]
---

# plan — TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING

1. Measure first (scopes 1, 3, 4): the loop, its cadence, the per-world death split by cause and boss/non-boss, the wounded-within-window test, victim faction provenance, the dragonkin branch, and parallel trauma series. Findings in `investigation.md`.
2. Options (a)-(e) reported with evidence and no recommendation; the owner ratified decision 14 (default-OFF flag over all three boss branches) and decision 15 (`ENV-07`, violent-cause-only trauma).
3. Implement decision 14: `ENABLE_WORLD_BOSS_SPAWN` (default OFF, registered in `feature_flags.py`, read through `state.feature_flags`) gating `BossService.check_for_boss_spawn`, `BossService.check_for_lair_spawn` and the calamity boss; keep the code, gates and the calamity cadence.
4. Implement decision 15: one set of violent death causes in `src/core/violent_cause.py`; the death block in `WorldDynamicsSystem.resolve_dynamics` and the building `+2.0` in `apply_plan.py` consult it. Worded as cause, not "has a killer".
5. Bible 05, DEV-010, DEV-011, WORLD-125, WORLD-126. Existing tests that asserted a boss spawn set the flag ON explicitly.
Out of scope, untouched: spawn siting, the origin-radius town guard, boss faction identity, the spawn-path faction defect, `src/core/state.py`.
