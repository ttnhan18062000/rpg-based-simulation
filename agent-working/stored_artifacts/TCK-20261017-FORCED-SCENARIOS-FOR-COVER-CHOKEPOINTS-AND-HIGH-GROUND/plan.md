---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND
artifact_type: plan
tags: []
---

# plan - TCK-20261017-FORCED-SCENARIOS-FOR-COVER-CHOKEPOINTS-AND-HIGH-GROUND

- Add tests/unit/combat/test_terrain_mechanics_forced_scenarios.py on rpg-next a1e4b6f3a. Stage two bodies on the withdrawal world with set terrain/blocked tiles, run Kernel.tick_once, and observe through a spy on CombatResolutionSystem.resolve_attack (trace/damage) and on identify_chokepoints/evaluate_entity_intent. No src change.
