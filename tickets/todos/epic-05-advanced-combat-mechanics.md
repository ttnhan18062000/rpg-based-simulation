# Epic 05: Advanced Combat Mechanics

## Summary

Deepen the combat system with positioning tactics, aggro management, AoE attacks, combo chains, environmental interactions, and status ailments. Combat becomes a richer tactical experience where entity positioning, skill order, and terrain matter.

Inspired by: Final Fantasy Tactics positioning, Dark Souls stamina management, D&D opportunity attacks, Divinity: Original Sin environmental combos.

---

## Motivation

- Current combat is 1v1 melee exchanges with potions — lacks tactical depth
- No AoE damage, no positioning strategy, no environmental interaction
- Engagement lock exists but could be expanded into a full positioning system
- Skills exist but lack combo potential or synergy between damage types/elements
- Aligns with "realistic RPG simulation" — real combat involves terrain, positioning, and teamwork

---

## Features

### F1: AoE Attacks & Skills ✅ DONE
- Skills with `AREA_ENEMIES` / `AREA_ALLIES` target types affect multiple entities in a radius
- AoE skills have a `radius` field (Manhattan distance from center)
- AoE damage reduced by distance from center (configurable `aoe_falloff`)
- Crits only on center target (dist_from_center == 0)
- **Skills added:** Whirlwind (Warrior, melee r=1), Rain of Arrows (Ranger, range=4 r=2), Fireball (Mage, range=4 r=2 magical)
- **AI:** `best_ready_skill()` prefers AoE when `nearby_enemies > 1` (score = power × enemy count)
- **Files:** `src/core/classes.py`, `src/engine/world_loop.py`, `src/ai/states.py`

### F2: Combo System ⏸️ DEFERRED
- Requires F6 (Status Ailments) first
- Combos defined in a `COMBO_REGISTRY` dict: `(existing_effect, incoming_element) → ComboResult`

### F3: Aggro & Threat System ✅ DONE
- `threat_table: dict[int, float]` on Entity model — per-attacker threat tracking
- Threat generated from: basic attacks, skill damage, opportunity attacks
- Tank bonus: Warrior/Champion get 1.5× `threat_tank_class_mult`
- Threat decay: 10%/tick in `_tick_threat_decay()`, dead attacker entries pruned
- AI targeting: mobs use `highest_threat_enemy()`, heroes keep `nearest_enemy()`
- **Config:** `threat_decay_rate=0.10`, `threat_damage_mult=1.0`, `threat_tank_class_mult=1.5`
- **Files:** `src/core/models.py`, `src/actions/combat.py`, `src/engine/world_loop.py`, `src/ai/perception.py`, `src/ai/states.py`, `src/config.py`

### F4: Ranged Combat Positioning ✅ DONE
- `weapon_range` on ItemTemplate; ranged weapons (shortbow, longbow, staves) range 3-5
- Line-of-sight via Bresenham in `Grid.has_line_of_sight()`
- Cover: +10% evasion for defenders adjacent to WALL vs ranged attacks
- AI kites when weapon_range≥3, dist≤1, HP>60%
- **Files:** `src/core/items.py`, `src/core/grid.py`, `src/actions/combat.py`, `src/ai/states.py`, `src/core/classes.py`

### Chase Mechanics ✅ DONE (bonus, not originally in spec)
- Opportunity attacks on melee disengage (`_process_opportunity_attacks`)
- SPD-based chase closing for faster hunters (`_process_chase_closing`)
- **Config:** `opportunity_attack_damage_mult=0.5`, `chase_spd_closing_base=6`

### F5: Environmental Combat ⏸️ DEFERRED
- Terrain combat modifiers (water → Wet, forest → cover, mountain → high ground)

### F6: Status Ailments Expansion ⏸️ DEFERRED
- Stun, Blind, Silence, Burn, Frozen, Wet

### F7: Combat Formations ⏸️ DEFERRED
- Line, Shield Wall, Flanking formation bonuses

---

## Design Principles

- All new combat mechanics flow through the existing `CombatAction.apply()` pipeline
- Status ailments use the existing `StatusEffect` system
- AoE and ranged attacks use the existing `ActionProposal` → `WorldLoop` pipeline
- Environmental effects are data-driven via terrain modifier registries
- Combo system is a pure lookup table — no complex interaction code
- All combat remains fully deterministic via `Domain.COMBAT` RNG

---

## Dependencies

- Skill system with target types (already exists)
- Status effect system (already exists)
- Damage type + element system (already exists)
- Engagement lock mechanic (already exists)
- Territory/terrain system (already exists)

---

## Estimated Scope

- Backend: ~10 files modified
- Frontend: ~3 files modified (combat animations, effect indicators)
- Data: Combo registry, terrain combat mods, new ailment definitions

---

## Dev Notes (from dev_noted_features)

> **[EPIC] combat? ranged combat?**

F4 (Ranged Combat Positioning) is the highest-priority feature from this epic per developer request. Consider implementing F4 as a standalone deliverable before the full epic.
