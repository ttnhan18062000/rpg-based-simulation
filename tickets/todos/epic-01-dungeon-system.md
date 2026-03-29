# Epic 01: Dungeon System

## Summary

Implement a full dungeon system that gives the `DUNGEON_ENTRANCE` tiles (already placed on the map) real gameplay purpose. Dungeons are instanced multi-room challenges with unique enemies, traps, puzzles, and boss encounters — the primary endgame content loop.

Inspired by: Diablo dungeon crawling, Darkest Dungeon room progression, roguelike floor mechanics.

---

## Motivation

- `DUNGEON_ENTRANCE` tiles exist on the map but do nothing
- The hero currently has no endgame content after clearing camps and crafting top-tier gear
- Dungeons provide repeatable, scalable challenge content
- Aligns with the "fully automated world" vision — hero autonomously decides when to enter dungeons based on gear/level readiness

---

## Features

### F1: Dungeon Generation
- Each `DUNGEON_ENTRANCE` tile links to a procedurally generated dungeon
- Dungeon is a separate grid (e.g. 32×32) with rooms connected by corridors
- Rooms contain: enemies, treasure, traps, rest points, boss chamber
- Generation uses `DeterministicRNG` with domain `Domain.DUNGEON`
- Dungeon difficulty scales with distance from town and hero level
- **Extensibility:** Dungeon layout defined by a `DungeonTemplate` dataclass — new dungeon types added by registering templates

### F2: Dungeon Entities
- Unique dungeon-only enemy types (e.g. `cave_spider`, `stone_golem`, `shadow_wraith`)
- Boss entity at the final room with special abilities and loot tables
- Enemies do not leave the dungeon instance
- **Extensibility:** Dungeon enemy pools defined per dungeon template, not hard-coded

### F3: Dungeon AI State
- New `AIState.IN_DUNGEON` — hero navigates dungeon rooms, fights, loots
- Hero enters dungeon when: level threshold met, gear power above minimum, HP full
- Hero exits dungeon on: boss defeated, HP critical (emergency exit), or dungeon cleared
- New `GoalScorer`: `DungeonGoal` — scores based on hero readiness and dungeon availability

### F4: Dungeon Traps & Hazards
- Trap tiles that deal damage or apply status effects (poison, slow)
- Environmental hazards (lava pools, collapsing floors)
- Traps detectable via PER attribute — high PER heroes can avoid them
- **Extensibility:** Traps defined as `TrapDef` dataclass with configurable effects

### F5: Dungeon Loot
- Dungeon-exclusive items (rare weapons, armor sets, unique accessories)
- Boss drops guaranteed rare+ loot
- Loot quality scales with dungeon tier
- Chest rooms with higher-tier treasure chests

### F6: Dungeon Cooldown & Respawn
- After clearing, dungeon regenerates after N ticks (configurable)
- New layout generated on respawn (different rooms, enemies, loot)
- Boss respawns with the dungeon

### F7: Frontend Visualization
- Dungeon entry shown on map as animated portal marker
- When hero enters dungeon, canvas switches to dungeon grid view (or picture-in-picture)
- Dungeon minimap separate from world minimap
- InspectPanel shows dungeon progress (rooms cleared, boss status)

---

## Design Principles

- Dungeon grid is a separate `WorldState`-like structure, not part of the main grid
- All dungeon logic runs through the same `WorldLoop` tick cycle
- Dungeon templates are data-driven — adding new dungeons = adding data, not code
- Boss abilities use the existing `SkillDef` system
- Dungeon traps use the existing `StatusEffect` system

---

## Dependencies

- `DUNGEON_ENTRANCE` tiles (already exist)
- Status effect system (already exists)
- Skill system (already exists)
- Treasure chest system (already exists)

---

## Estimated Scope

- Backend: ~15 files new/modified
- Frontend: ~5 components new/modified
- Config: New dungeon parameters in `SimulationConfig`
