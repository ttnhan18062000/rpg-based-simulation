# TCK-20260426-RPG-CORE-HARDENING

## Title
RPG Core Life-Loop & Arena Hardening

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Recover and verify the authoritative RPG life-loop (rewards, mortality) and extend End-to-End Arena testing to include attrition and status effects.

## Scope
- Multi-entity update resolution (Combat rewards).
- Generation-based mortality (Rebirth vs Permadeath).
- Corpse spawning with loot drop.
- Biological Attrition (Hunger, Sleep, Starvation).
- Status Synergy (Shatter damage vs Frozen).
- Extended E2E Arena Scenarios.

## Out of Scope
- Detailed quest logic (Phase 23+).
- Guild management systems.

## Acceptance Criteria
- [x] XP and Gold gains verified in combat.
- [x] Rebirth at Gen 1-3 (Equipment loss) verified.
- [x] Permadeath at Gen 4 verified.
- [x] Corpse spawning verified.
- [x] High Ground (+20%) and Flanking (+15%) verified.
- [x] Social Synergy (+10%) verified.
- [x] Shatter (1.5x) and Exhaustion (0.8x Atk) verified.
- [x] Starvation (HP decay) and Readiness Penalty verified.

## Related Tickets
- TCK-20260426-PH16-AOE-LEGALITY
- TCK-20260426-PH15-SOCIAL-BONDS

## Related Docs
- arena_extended_rpg_phases.md

## Related Code Areas
- src/engine/apply.py
- src/engine/combat.py
- src/engine/domain_logic.py
- tests/rpg/test_rpg_core_recovery.py

## Implementation Notes
- Promoted V2 patterns to authoritative `src` paths.
- Unified multi-update handling in `SimulationDomainLogic`.
- Consolidated corpse management in `ApplyPath`.

## Test Summary
- Verified via `tests/rpg/test_rpg_core_recovery.py` (6 passed).
- Scenarios: PROGRESSION, MORTALITY, TACTICAL, SOCIAL, ATTRITION.

## Files Changed
- src/engine/apply.py
- src/engine/combat.py
- src/engine/domain_logic.py
- src/certification/scenarios.py
- tests/rpg/test_rpg_core_recovery.py

## Completion Summary
- Authoritative RPG life-loop restored and hardened.
- E2E Arena suite extended to cover high-fidelity tactical/biological mechanics.
- All code promoted to the main `src` directory.
