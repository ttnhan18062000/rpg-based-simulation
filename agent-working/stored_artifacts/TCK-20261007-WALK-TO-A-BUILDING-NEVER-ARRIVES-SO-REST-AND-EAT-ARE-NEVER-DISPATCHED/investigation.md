---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED
artifact_type: investigation
tags: [combat, bug]
---

# Investigation

- Tick-level trace of entity 31 (crowded_frontier, seed 42, capacity-fix tree, t405-470): fatigue project from t410, walks to the inn (distance 21 down to 1 at t430), then alternates (39,31) distance 1 and (39,32) distance 2 every tick. Legality log: from (39,31) the step to the nav target (40,31) is `False path_not_found` every time; resolve_move's orthogonal sidestep rung picks (39,32) (`LEGAL`); from (39,32) the planner's step is (39,31) (`LEGAL`). The brain ticks at t430, t440, t450 saw start-of-tick positions (39,30), (39,32), (39,32), all distance 2, so the tactical building branch took "still en-route" and no `REST` was decided. At t450 `resolve_blocker` (flat 80, 95.3 after modifiers) replaced the fatigue project (see `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`).
- The inn tile (40,31) of crowded_frontier is in `state.blocked_tiles` (so `verify_occupancy` returns `PATH_NOT_FOUND`); `state.building_tiles` is empty in every compiled world (0 entries), so the `BUILDING_OBSTRUCTION` branch is not what stops the walker here, and `town_resolution.py` (which reads `building_tiles`) cannot match a building tile.
- Corpus (24 worlds, seed 42, 500 ticks, this branch): 844 arrivals, 438 at inns and 406 at town halls, 0 resource nodes, 0 other blocked tiles, 0 arrivals that were not beside a blocked destination; worlds without buildings (dungeon_crawl, highland_traverse, mechanic_scenario_combat_judgement_withdrawal, quest_dense_frontier, wilderness_survival) have none.
- Probes (scratchpad, not committed): `trace31.py`, `measure_arrival.py`, `arrival_corpus.py`.
