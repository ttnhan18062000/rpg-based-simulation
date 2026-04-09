# Design 01: Skill & Basic Attack Stat Scaling

## Summary
Define which stats each skill (and basic attack) scales from, and what the multipliers are. Currently unclear how skill `power` interacts with ATK, MATK, and attribute bonuses.

## Questions to Resolve
1. **Basic attack** — scales from ATK only? Or ATK + weapon damage_type modifier?
2. **Physical skills** (power_strike, shield_wall, etc.) — scale from ATK × power? Does STR attribute bonus stack?
3. **Magical skills** (fireball, heal, etc.) — scale from MATK × power? Does INT attribute bonus stack?
4. **Hybrid skills** — any skills that scale from multiple stats?
5. **Healing skills** — scale from MATK? Or a flat `heal_amount`?
6. **Buff/debuff skills** — do modifier values (`atk_mod`, `def_mod`, etc.) scale with any stat, or are they flat?

## Current Implementation
From `SkillDef`:
- `power: float` — damage/heal multiplier
- `atk_mod`, `def_mod`, `spd_mod`, `crit_mod`, `evasion_mod`, `hp_mod` — flat modifiers for buff/debuff skills
- `damage_type` and `element` exist on `ItemTemplate` but not on `SkillDef` directly

From `DamageCalculator` (`src/actions/damage.py`):
- Need to audit how `power` is used in the damage formula
- Need to audit how class scaling grades (S/A/B/C/D/E from `ClassDef`) interact

## Status
DONE

## Final Status
**DONE**: Unified skill damage resolution and deterministic RNG passing via `TCK-20260405-SKILL-SCALING`. Implemented scaling chain: `base_stat → class_scaling → skill_power → final_damage` and verified with automated combat tests.
