---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH8-M3-PROGRESSION
artifact_type: plan
tags: [ph8, m3, progression]
---

# PH8 M3: Progression and Leveling

Implement authoritative leveling and stat growth logic.

## Proposed Changes

### [Models] [NEW] [leveling.py](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py)
- Define `LevelingService` with XP curves and stat scaling formulas.

### [Apply Path] [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Implement auto-leveling logic in `_apply_entity_update`:
  - Check `evolution_points` vs `required_xp`.
  - If level up: increment `evolution_level`, reset/deduct points, and scale `CombatComponent` stats.

## Verification Plan

### Automated Tests
- `tests/progression/test_leveling.py`:
  - Verify XP-to-Level conversion.
  - Verify HP/ATK/DEF growth on level up.
  - Verify that level cap is respected.

#### Manual Verification
- CLI inspection of entity stats after multiple quest completions.
