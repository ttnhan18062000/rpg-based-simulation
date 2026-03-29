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

## Proposed Deliverable

1. Audit current damage formula in `damage.py`
2. Document the scaling chain: `base_stat → class_scaling → skill_power → final_damage`
3. Propose a clear scaling table for all 22 skills
4. Present to developer for decision

## Affected Code

- `src/actions/damage.py` — damage formula
- `src/actions/combat.py` — how skill power is applied
- `src/core/classes.py` — scaling grades per class

## Notes

> **Decision required from developer** on the scaling design. This is a design document ticket, not a code change.

## Labels

`design`, `combat`, `balance`, `needs-decision`
