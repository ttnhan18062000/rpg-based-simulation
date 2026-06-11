---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260426-PHASE-24-SOVEREIGNTY
phase: done
date: 2026-04-26
tags: [phase, sovereignty]
---

# TCK-20260426-PHASE-24-SOVEREIGNTY

## Title
Phase 24: Regional Sovereignty & Taxation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Restore regional ownership, influence shifts, and taxation to the V2 authoritative engine. Port macroscopic logic from legacy `StrategySystem` to the `ApplyPath`.

## Scope
- Implement `RegionalSovereigntyService` to handle taxation and debuffs.
- Integrate influence shifts into `ApplyPath.apply_generation` (via refinement pipeline).
- Implement `TaxationService` for regional gold collection.
- Restore `CONQUERED_DEBUFF` (Aura of Despair) for regions controlled by monsters.
- Add regional ownership persistence and state hash coverage.

## Acceptance Criteria
- [x] Killing monsters increases regional influence (towards Hero Guild).
- [x] Hero deaths decrease regional influence (towards Monster Horde).
- [x] Factions collect taxes from entities/buildings in their owned regions.
- [x] Heroes in monster-controlled regions receive combat penalties.
- [x] Regional state transitions (Ownership change) are deterministic and persistent.

## Related Docs
- [docs/world_evolution_and_resilience.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/world_evolution_and_resilience.md)
- [resource_v2_e_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e_phases.md)

## Related Code Areas
- `src/engine/apply.py`
- `src/world/influence.py`
- `src/world/regional_sovereignty.py`

## Implementation Notes
- Influence Shift: Hero death = -5.0; Monster death = +5.0.
- Ownership Thresholds: Conquest at <= -50.0; Liberation at >= 50.0.
- Taxation: Every 100 ticks. Entity: 2.0 gold. Building: 10.0 gold.
- Debuff: 0.8x Atk/Def, 0.9x Speed.

## Test Summary
- `tests/arena/test_arena_regional_control.py`: PASS (Influence, Conquest, Taxation, Debuffs verified).

## Files Changed
- [src/world/regional_sovereignty.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/regional_sovereignty.py)
- [src/world/influence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/influence.py)
- [src/engine/apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- [src/certification/scenarios.py](file:///home/vboxuser/Work/rpg-based-simulation/src/certification/scenarios.py)
- [tests/arena/test_arena_regional_control.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/arena/test_arena_regional_control.py)
- [docs/world_evolution_and_resilience.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/world_evolution_and_resilience.md)

## Completion Summary
Phase 24 is complete. Regional sovereignty and macroscopic taxation are now fully integrated into the authoritative V2 engine. The system supports dynamic influence shifts, conquest/liberation cycles, and deterministic economic drains.
