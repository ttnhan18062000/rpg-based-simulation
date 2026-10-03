---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS
artifact_type: plan
tags: [pressure, perception, consumers]
---

# Plan — TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS

## Approach

Singleton bridge module (`behavior_consumers.py`) exposes lazy-init singletons for
PerceptionGate and MotivationPressureResolver, injectable for tests.

Four additive changes in `TacticalDecisionSystem.evaluate_entity_intent`:
1. Resolve entity pressures once at entry (read-only, silent fallback)
2. Perception gate in hostile loop — permissive fallback on exception
3. Safety pressure flee trigger — safety_pressure > 0.75 → RETREAT
4. target_score() closure — pressure_dist_mod reduces effective distance

Resource-seeking priority (hunger/wealth) is a strategic-level concern;
tactical.py follows the already-selected objective, so no hook added here.
