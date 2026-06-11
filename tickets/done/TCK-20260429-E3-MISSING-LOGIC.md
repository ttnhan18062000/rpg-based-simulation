---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260429-E3-MISSING-LOGIC
phase: done
date: 2026-04-29
tags: [e3, missing, logic]
---

# TCK-20260429-E3-MISSING-LOGIC

## Title
Implement Missing RPG Core Logic (E3 Phases Gap Closure)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the missing/incorrect logic identified during the semantic audit of resource_v2_e3_phases_enhanced.md against logic_checklist_exhaustive_v2.md.

## Scope
- Stamina system (drain on attack/move/harvest, regen, exhaustion penalty)
- Wound/scar combat aftermath (massive hit wounds, stat penalties)
- Mob leash and return-to-camp behavior
- Terrain cost in pathfinding (road/swamp cost weights)
- Target stickiness in tactical combat (anti-flicker)
- Skill scaling math (physical/magical/elemental formulas)
- Attribute caps enforcement
- Effective stats recompute (base + gear + traits + modifiers)

## Out of Scope
- Phase guard write authorization (separate ticket)
- Full CI checklist validator (separate ticket)
- RNG call-order independence proof (separate ticket)
- Scar decay, local scar record, AI perception of scars

## Acceptance Criteria
- [x] Stamina component exists on EntityState
- [x] Stamina drains on attack, move, harvest, skill use
- [x] Stamina regens during rest and passively
- [x] Exhaustion penalty applies to combat when stamina is depleted
- [x] Wounds are generated from massive hits (40% max HP threshold)
- [x] Wounds apply stat penalties (atk/def/speed/max_hp)
- [x] Scars persist from healed wounds (30% of wound penalties)
- [x] Mob leash enforces return-to-camp when beyond radius
- [x] Leash chase give-up after timeout/distance (1.5x radius, max_chase_ticks)
- [x] Terrain cost affects pathfinding (ROAD=0.5, SWAMP=3.0, etc.)
- [x] Target stickiness prevents flicker below 30% improvement margin
- [x] Skill scaling uses correct attribute formulas (PHYS/MAG/ELEM)
- [x] Attribute caps enforced (max 99, evasion max 0.95)
- [x] All new logic has tests (54 tests)
- [x] Full test suite passes (669 passed, 0 failed)

## Related Tickets
- None

## Related Docs
- logic_checklist_exhaustive_v2.md (13 items checked off)
- resource_v2_e3_phases_enhanced.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260429-E3-MISSING-LOGIC/

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/core/worker_protocol.py
- src/engine/rpg_depth.py (NEW)
- src/engine/combat.py
- src/engine/movement.py
- src/engine/apply.py
- src/engine/executor.py
- tests/rpg/test_rpg_depth.py (NEW)
- logic_checklist_exhaustive_v2.md

## Assumptions / Open Questions
- Stamina max is derived from endurance attribute (50 + end*5)
- Wound threshold is 40% of max HP in a single hit
- Leash default radius is 10 tiles, chase multiplier is 1.5x
- Scar penalties are 30% of original wound penalties

## Implementation Notes
- StaminaComponent uses frozen dataclass with class-level cost constants
- WoundState/ScarState are list fields on EntityState (not dict-keyed)
- TerrainCostService uses getattr for graceful handling when state_or_context doesn't have terrain
- Recalculation gate now routes through SkillScalingService.get_effective_stats instead of raw LevelingService
- WorkerPacket now carries terrain data for worker-side pathfinding

## Test Summary
- 54 new tests in tests/rpg/test_rpg_depth.py
- Full suite: 669 passed, 2 skipped, 0 failed (up from 615)
- No regressions

## Files Changed
- src/core/state.py (StaminaComponent, WoundState, ScarState, TERRAIN_COST, NavigationComponent leash fields, EntityState)
- src/core/updates.py (StaminaUpdate, WoundUpdate, EntityUpdate fields, merge)
- src/core/worker_protocol.py (terrain field on WorkerPacket)
- src/engine/rpg_depth.py (NEW — all depth services)
- src/engine/combat.py (exhaustion integration)
- src/engine/movement.py (terrain cost, stamina drain)
- src/engine/apply.py (stamina/wound apply, recalculation gate upgrade)
- src/engine/executor.py (terrain in packet construction)
- tests/rpg/test_rpg_depth.py (NEW — 54 tests)
- logic_checklist_exhaustive_v2.md (13 items checked off)

## Completion Summary
Implemented 7 missing RPG core systems identified through semantic audit:
1. **Stamina** — Full drain/regen/exhaustion lifecycle with typed StaminaUpdate
2. **Wounds/Scars** — Massive hit → wound → heal → permanent scar pipeline
3. **Mob Leash** — Distance + timeout chase give-up, return-to-camp
4. **Terrain Cost** — 9-terrain cost table with weighted readiness drain
5. **Target Stickiness** — Margin + loyalty anti-flicker guard
6. **Skill Scaling** — PHY/MAG/ELEM attribute-based formulas
7. **Effective Stats** — Unified stat derivation with wound/scar/gear/trait integration

All 669 tests pass. 13 checklist items marked as verified.
