---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN
artifact_type: test_plan
tags: [combat, world, root-cause]
---

# Test plan

- `tests/unit/combat/test_tactical_destinations.py`: pure derivation (strict containment, away-vector,
  clamp, cornered hold, no-threat hold, home-region fallback, outside-region hold; wander nearby,
  seeded, varies by tick and entity) and each branch through `evaluate_entity_intent`. Regions start at
  x,y >= 5 so `(0,0)` is outside them; each branch test asserts non-empty state first.
- Control: with the old `tactical.py` restored, four of the branch tests fail (measured: 4 failed, 11
  passed), with the new module present.
- Updated pinned tests: `test_anti_stalemate.py::test_stalemate_break`,
  `test_engagement_behavior.py::test_retreat_behavior`. New region-bearing
  `test_pressure_perception_consumers.py::test_safety_pressure_retreat_target_is_inside_a_region_and_away_from_the_threat`.
- Scoped regression: `tests/unit/combat`, `tests/unit/engine`, plus the determinism, certification,
  regression and architecture suites (`-m "not slow"`).
- Not covered: corpus firing rates per branch and entity kind (see investigation, "Not measured").
