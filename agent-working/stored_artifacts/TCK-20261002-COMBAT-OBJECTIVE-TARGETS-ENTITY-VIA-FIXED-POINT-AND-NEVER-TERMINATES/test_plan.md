---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES
artifact_type: test_plan
tags: [strategy, cognition, combat]
---

# Test plan

`tests/unit/strategic/test_entity_target_objective.py`:
- scorer names the entity it chose and keeps `target_id` as a string; place scorers leave it unset;
  `evaluate_strategic_intent` creates a combat objective carrying the typed id (this fails if any stage
  between scorer and objective drops the field, as `ScoreModifierSystem` used to);
- `_entity_target_outcome`: holds while alive and in range (and exactly at the radius), RESOLVED/COMPLETED
  on death, FAILED/ABANDONED when gone or out of range, untouched for place objectives;
- the same through the real `evaluate_strategic_intent` (project closed, slot freed);
- `_resolve_target_position`: live position not the snapshot, an entity id equal to a node id is not
  resolved as the node, dead or missing gives no position and no stale fallback;
- **legacy unchanged** (`TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`): `"town_center"` falls back to
  `target_position`, an int-castable node id still resolves to the node, a coordinate string still parses;
- canonical dict omits `target_entity_id` when `None` and includes it when set.

End to end: the objective probe (scratch, not in the repo) re-run after the change on `crowded_frontier` and
`frontier_living_world`, reporting objectives observed terminal, dead-target-while-current, and distinct
combat objectives. Plus `tests/unit/{strategic,social,ai,combat,engine,core}` and the determinism,
certification, regression and architecture suites; any moved recorded hash is explained, not regenerated.
