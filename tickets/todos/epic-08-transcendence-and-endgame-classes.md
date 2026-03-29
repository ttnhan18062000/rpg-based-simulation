# Epic 08: Transcendence & Endgame Classes

## Summary

Implement the Tier 3 "Transcendence" class advancement system, giving heroes a powerful late-game transformation with unique mechanics, ultimate skills, and visual prestige. This completes the class progression tree and provides a long-term goal for high-level heroes.

Inspired by: Final Fantasy job mastery, Diablo III Paragon system, Path of Exile Ascendancy, MapleStory 4th job advancement.

---

## Motivation

- Class progression currently stops at Tier 2 (Breakthrough) — Transcendence is documented as "[future]"
- Heroes that reach level 20 with full breakthrough have no further growth path
- Transcendence provides aspirational endgame content
- Unique ultimate abilities create dramatic combat moments
- Aligns with "realistic RPG simulation" — powerful heroes should feel truly legendary

---

## Features

### F1: Transcendence Requirements
- Level requirement: 20 (max level)
- Primary attribute requirement: ≥ 60 (class-specific attribute)
- Class mastery: 100%
- All 3 class skills at Master tier (100% mastery)
- Special quest completion (Transcendence Trial — unique dungeon challenge)
- **Extensibility:** Requirements defined in `TranscendenceDef` dataclass, not hard-coded gates

### F2: Transcendence Classes

| Base | Breakthrough | Transcendence | Theme |
|------|-------------|---------------|-------|
| Warrior | Champion | **Warlord** | Unstoppable frontline commander |
| Ranger | Sharpshooter | **Windwalker** | Untouchable speed demon |
| Mage | Archmage | **Sage** | Reality-bending spellcaster |
| Rogue | Assassin | **Phantom** | Death incarnate |

### F3: Transcendence Bonuses
- New scaling grade: **SSS** (180%) for primary attribute
- All attribute caps raised by +20
- Unique passive talent per Transcendence class
- Stat growth per level enhanced (+50% over base growth rates)
- **Extensibility:** Bonuses defined in `TranscendenceDef`, reusing existing `ClassDef` structure

### F4: Ultimate Skills (1 per Transcendence class)
- **Warlord — Earthquake:** AoE physical damage in 3-tile radius, stuns all enemies for 2 ticks. CD: 20.
- **Windwalker — Arrow Storm:** Hits all enemies within 4 tiles for 1.5× damage. CD: 15.
- **Sage — Meteor:** Massive AoE magical damage (3× power), 4-tile radius, leaves burning terrain for 3 ticks. CD: 25.
- **Phantom — Death Mark:** Marks target; if target drops below 20% HP within 5 ticks, instant kill. CD: 18.
- Ultimate skills use the existing `SkillDef` + `StatusEffect` + `CombatAction` systems
- **Extensibility:** Ultimates are just `SkillDef` entries with high requirements — no special skill code

### F5: Transcendence Visual Identity
- Transcended heroes get a unique canvas rendering: larger sprite, permanent aura effect
- Aura color matches class theme (Warlord=red, Windwalker=green, Sage=blue, Phantom=purple)
- InspectPanel shows Transcendence badge and ultimate skill with special styling
- Class Hall UI updated with Transcendence tier in the progression tree

### F6: Transcendence Trial
- Unique quest that spawns when hero meets level + attribute requirements
- Trial is a solo challenge (no party help) in a special area
- Trial enemies match the hero's class weakness (Warrior faces fast enemies, Mage faces magic-resistant foes)
- Trial completion triggers the Transcendence class change
- **Extensibility:** Trial definitions use the dungeon system (Epic 01) or a simplified version

### F7: Post-Transcendence Growth
- After Transcendence, hero continues training attributes and mastering the ultimate skill
- Attribute caps continue growing (+5/level via "prestige levels" beyond 20)
- Ultimate skill mastery unlocks enhanced effects at 50% and 100% mastery
- **Extensibility:** Prestige level system reuses existing level-up infrastructure

---

## Design Principles

- Transcendence reuses the existing `ClassDef`/`BreakthroughDef` pattern — no new class hierarchy
- Ultimate skills are standard `SkillDef` entries — no special-case combat code
- Trial quests use the existing `Quest` system or dungeon system
- All Transcendence effects flow through existing stat/effect pipelines
- Visual changes are frontend-only — backend treats Transcended heroes identically to other entities

---

## Dependencies

- Class system with breakthrough (already exists)
- Skill system with mastery (already exists)
- Class Hall building (already exists)
- Quest system (already exists)
- Status effect system (already exists)

---

## Estimated Scope

- Backend: ~5 files modified (classes.py, states.py, buildings.py, config.py, enums.py)
- Frontend: ~3 files modified (ClassHallPanel, InspectPanel, useCanvas)
- Data: 4 Transcendence class definitions, 4 ultimate skill definitions, 4 trial quest definitions
