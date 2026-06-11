---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [skill, scaling]
---

# TCK-20260405-SKILL-SCALING: Unified Skill Damage Resolution

Unify skill damage calculation with the authoritative `DamageResolutionService`. Currently, `ActionSystem._get_use_skill_updates` uses a hardcoded `atk * power` formula that ignores magical scaling (MATK), elemental multipliers, critical hits, and evasion logic.

## User Review Required

> [!IMPORTANT]
> This change will shift skill damage from a simple linear formula (`atk * power - def/2`) to the engine's standard diminishing returns formula (`atk * (atk / (atk + 2*def))`). This may require re-balancing skill `power` values in `SKILL_DEFS`.

## Proposed Changes

### Core Gameplay & Systems

#### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/combat.py)
- Refactor `DamageResolutionService.resolve` signature to:
  `def resolve(attacker: Entity, defender: Entity, world: WorldState, config: SimulationConfig, rng: DeterministicRNG, skill_power: float = 1.0, override_damage_type: DamageType | None = None, override_element: Element | None = None) -> tuple[int, bool, bool, dict]`
- Integrate `skill_power` into the `atk_final` calculation: `atk_final = int(dmg_ctx.atk_power * dmg_ctx.atk_mult * skill_power)`.
- Use `override_damage_type` and `override_element` if provided, otherwise fallback to weapon-based detection.

#### [MODIFY] [action_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/gameplay/action_system.py)
- Refactor `_get_use_skill_updates` to remove hardcoded damage logic.
- Call `DamageResolutionService.resolve` for each skill target.
- Call `CombatAftermathService.process` to ensure skills generate trauma, threat, and memory events consistent with basic attacks.

### Configuration & Content

#### [MODIFY] [skills.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/gameplay/skills.py) (or `src/core/data/skill_defs.py`)
- Ensure all skill definitions include a `damage_type` (Physical vs Magical).
- Identify which skills should scale from `MATK`.

## Verification Plan

### Automated Tests
- `pytest tests/unit/core/test_skill_scaling.py`: New test suite to verify that "Fireball" scales with `MATK` and "Power Strike" scales with `ATK`.
- `python3 -m pytest tests/unit/ai/test_goals.py`: Verify that AI still scores high-damage skills correctly after the formula change.

### Manual Verification
- Run a CLI simulation with `ticks=10` and verify JSON logs for `CombatTraceUpdate` entries originating from skills, ensuring they include `raw_damage`, `mitigation`, and correctly identified `dmg_type`.
