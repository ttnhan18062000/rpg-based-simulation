# Phase 28 Implementation Plan

## Goal Description
Integrate relation projection into runtime combat target classification. Ensure that `FactionSemanticsService.is_hostile_compat` is called inside `TacticalDecisionSystem` and `LegalityServiceV2` to evaluate hostility when clean data is available, with explicit legacy fallback and debug reporting.

## Proposed Changes

### Combat Targeting & Legality
- **`src/engine/legality.py`** ([LegalityServiceV2](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/legality.py)):
  - Modify `verify_attack_legality` to verify faction hostility via `FactionSemanticsService.is_hostile_compat` instead of `attacker.identity.faction == target.identity.faction`.
  - Pass a `RelationContext` constructed from target distance and combat state.

- **`src/engine/tactical.py`** ([TacticalDecisionSystem](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/tactical.py)):
  - Modify the hostile candidate filtering loop in `evaluate_entity_intent` to classify hostiles using `FactionSemanticsService.is_hostile_compat` instead of a simple inequality check.
  - Construct `RelationContext` containing distance and visibility properties.

## Verification Plan

### Automated Tests
- Create `tests/integration/combat/test_relation_combat_integration.py` to assert:
  - Clean target classification is called when dynamic relationship data exists.
  - A hero perspective correctly targets goblins as enemies.
  - A hero perspective does not target merchant caravan members as enemies.
  - A wild beast's threat level is contextual (hostile within distance <= 5, neutral otherwise).
  - Legacy monster fallback works correctly.
  - Debug messages logging fallback usage are emitted.
- Run existing unit/integration combat and arena tests to ensure no regressions.
