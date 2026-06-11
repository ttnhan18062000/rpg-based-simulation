---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260425-WORLD-DYNAMICS
artifact_type: investigation
tags: [world, dynamics]
---

# Investigation - World Dynamics

## Legacy Parity
- Legacy system used `FactionInfluence` for territory control.
- `Aura of Despair` was a movement debuff near monster-controlled regions.
- `Calamity` events were maturity-based milestones.

## V2 Adaptation
- Use `StateUpdate` for all dynamic entity spawns to preserve authoritative flow.
- `ApplyPath.apply_generation` is the correct hook for injecting new entities during tick transition.
- Proximity-based debuffs in `EnvironmentService` should be efficient (Manhattan distance).
- RNG must be scoped to the correct `Domain`.
