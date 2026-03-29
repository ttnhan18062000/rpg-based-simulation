# Epic 13: Ruins Exploration & Lore System

## Summary

Give the existing RUINS tiles gameplay purpose with explorable structures containing lore fragments, hidden caches, puzzles, and environmental storytelling. Introduce a lore collection system that rewards thorough exploration with permanent bonuses and world knowledge.

Inspired by: Dark Souls item descriptions, Hollow Knight lore tablets, Skyrim books/notes, Elden Ring environmental storytelling.

---

## Motivation

- RUINS tiles (12) exist on the map but have no gameplay purpose
- The world has no history or narrative context — it just "exists"
- Lore fragments reward explorers and give meaning to the world's factions and structures
- Ruins exploration fills the gap between combat and crafting with a discovery loop
- Aligns with "realistic RPG simulation" — fantasy worlds have ancient history

---

## Features

### F1: Ruins Structures
- Each 3×3 ruins patch becomes an explorable location
- Ruins contain: lore fragments, hidden caches, traps, and ambient enemies
- Ruins difficulty based on distance from town (farther = harder guardians, better loot)
- Some ruins are "cleared" after exploration; others are repeatable
- **Extensibility:** `RuinsDef` dataclass defines contents, difficulty, lore, and loot — new ruins = new data

### F2: Lore Fragment System
- `LoreFragment` dataclass: `id`, `title`, `text`, `category`, `rarity`
- Categories: World History, Faction Origins, Ancient Magic, Hero Legends, Monster Ecology
- Fragments collected by exploring ruins, defeating bosses, or finding hidden items
- Each fragment is unique — collecting all fragments in a category grants a permanent bonus
- **Extensibility:** Lore fragments defined in a data registry — adding lore = adding entries

### F3: Lore Collection Bonuses

| Category | Fragments | Completion Bonus |
|----------|-----------|-----------------|
| World History | 8 | +5% XP gain permanently |
| Faction Origins | 6 | +10 starting reputation with all factions |
| Ancient Magic | 5 | +3 MATK, +3 MDEF permanently |
| Hero Legends | 4 | +1 to all attribute caps permanently |
| Monster Ecology | 10 | +10% damage vs all monster types |

- Partial collection grants scaled partial bonuses
- **Extensibility:** Bonuses defined per category in a `LoreBonusDef`, using existing stat/effect systems

### F4: Hidden Caches
- Ruins contain hidden item caches that require PER checks to discover
- Cache discovery: `roll = rng.next_float(LOOT, entity_id, tick)`, success if `roll < PER * 0.02`
- Caches contain: gold, rare materials, occasionally unique items
- Each cache can only be discovered once per hero
- **Extensibility:** Cache contents defined per ruins difficulty tier in loot tables

### F5: Ruins Guardians
- Some ruins have guardian entities (stone golems, spectral knights, ancient constructs)
- Guardians only activate when a hero enters the ruins area
- Guardian types and difficulty scale with ruins distance from town
- Defeating guardians unlocks the ruins lore and cache
- **Extensibility:** Guardian pools defined per ruins tier in `RUINS_GUARDIAN_TABLES`

### F6: AI Exploration Behavior
- `ExploreGoal` scorer gains bonus when unexplored ruins are known (via guild intel or memory)
- New handler behavior in `WanderHandler`: when near ruins, hero investigates
- Hero spends N ticks "investigating" ruins (channeled action, like harvesting)
- Investigation yields: lore fragment + cache check + guardian encounter
- **Extensibility:** Investigation behavior uses existing HARVEST-like channel pattern

### F7: Frontend
- Ruins tiles get a special canvas rendering (crumbled stone pattern or icon)
- Investigated ruins shown with a checkmark overlay
- New "Lore" section in InspectPanel showing collected fragments
- Lore fragments viewable in a collapsible list with flavor text
- Collection progress bars per category
- Ruins hover tooltip shows: name, difficulty, explored status

---

## Design Principles

- Ruins exploration uses the existing channel action pattern (like HARVEST)
- Lore fragments stored on the hero entity in a `lore_collected: set[str]`
- Collection bonuses applied as persistent `StatusEffect`s with `remaining_ticks = -1`
- Guardian spawning uses existing `EntityGenerator` and `EntityBuilder`
- All ruins content is deterministic (same seed = same ruins = same lore placement)

---

## Dependencies

- RUINS tiles on the map (already exist, `num_ruins = 4`)
- Harvest/channel action pattern (already exists)
- Status effect system for permanent bonuses (already exists)
- Entity memory for tracking explored ruins (already exists)
- PER attribute for cache discovery (already exists)

---

## Estimated Scope

- Backend: ~6 files new/modified
- Frontend: ~3 files modified (InspectPanel, useCanvas, colors)
- Data: Lore fragment definitions, ruins definitions, guardian tables, cache loot tables
