---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260425-WORLD-DYNAMICS
artifact_type: plan
tags: [world, dynamics]
---

# Implementation Plan - World Dynamics

## Objective
Implement Phase 11.2 - 11.5 of the V2 engine roadmap, covering World Dynamics.

## Proposed Changes

### Core Updates
- Add `entities_add` and `entities_remove` to `StateUpdate`.
- Update `ApplyPath` to handle dynamic entity lifecycle.

### World Systems
- `FactionInfluenceService`: Handle influence shifts and conquest lifecycle.
- `RaidService`: Orchestrate periodic faction raids.
- `CalamityService`: Manage world maturity and world boss spawns.
- `EnvironmentService`: Implement "Aura of Despair" debuff.

### Generators
- `EntityGenerator`: Support world boss and stronghold spawning with difficulty scaling.

## Verification
- Unit and integration tests for each service.
- Verification of debuff proximity and effect.
- Verification of deterministic spawning on maturity milestones.
