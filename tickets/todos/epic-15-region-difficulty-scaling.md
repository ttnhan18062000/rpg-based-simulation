# Epic 15: Region Difficulty Scaling

## Summary

Implement a distance-based difficulty system where enemies further from the town are progressively stronger. This creates natural game progression — heroes start by fighting weak enemies near town and gradually venture further as they level up and gear up.

Inspired by: Diablo zone levels, WoW zone progression, Path of Exile act areas, Terraria biome difficulty.

---

## Motivation

- Currently all enemies of the same kind have similar stats regardless of location
- No sense of progression — a goblin near town is as dangerous as one far away
- Heroes have no reason to explore further once nearby enemies are cleared
- Aligns with "realistic RPG simulation" — danger increases with distance from civilization

---

## Features

### F1: Region Difficulty Zones

- Divide the map into concentric difficulty zones based on Manhattan distance from town center:
  - **Zone 1 (Safe):** 0–10 tiles from town — weakest enemies, tier 1
  - **Zone 2 (Normal):** 11–25 tiles — standard enemies, tier 2
  - **Zone 3 (Dangerous):** 26–40 tiles — strong enemies, tier 3
  - **Zone 4 (Deadly):** 41+ tiles — elite enemies, tier 4–5
- Zone boundaries configurable in `SimulationConfig`
- **Extensibility:** Zones defined as a list of `(max_distance, difficulty_multiplier)` tuples

### F2: Enemy Stat Scaling

- Enemies spawned in higher zones get stat multipliers:
  - HP: `base_hp × zone_multiplier`
  - ATK: `base_atk × zone_multiplier`
  - DEF: `base_def × zone_multiplier`
  - XP reward: `base_xp × zone_multiplier`
  - Gold drop: `base_gold × zone_multiplier`
- Multipliers per zone:
  - Zone 1: 1.0×
  - Zone 2: 1.5×
  - Zone 3: 2.5×
  - Zone 4: 4.0×
- **Extensibility:** Multipliers defined per stat, not a single global multiplier

### F3: Loot Quality Scaling

- Higher zones drop better loot:
  - Zone 1: common items only
  - Zone 2: common + uncommon
  - Zone 3: uncommon + rare
  - Zone 4: rare + epic
- Loot table selection based on zone at time of enemy death
- **Extensibility:** Zone-to-rarity mapping defined in a registry

### F4: Enemy Type Distribution

- Certain enemy types only appear in higher zones:
  - Zone 1: goblins, wolves
  - Zone 2: goblin warriors, bandits, dire wolves
  - Zone 3: orc warriors, bandit chiefs, alpha wolves, skeletons
  - Zone 4: orc warlords, liches, goblin chiefs (elite)
- Generator uses zone to filter spawn pool
- **Extensibility:** Entity kind to minimum zone mapping in `ENTITY_ZONE_REQUIREMENTS`

### F5: Visual Zone Indicators

- Subtle tint or border on the map showing zone boundaries
- Minimap shows zone rings
- Entity tooltip shows zone level: "Goblin Warrior (Zone 3)"
- InspectPanel shows entity's zone difficulty multiplier

### F6: Hero Difficulty Awareness

- AI goal scoring considers zone difficulty:
  - Low-level heroes avoid high zones (explore score penalized by zone mismatch)
  - High-level heroes prefer higher zones (better rewards)
  - FLEE threshold adjusted by zone (flee earlier in high zones)
- **Extensibility:** Zone awareness integrated into existing `GoalScorer` pipeline

---

## Design Principles

- Zone difficulty is computed from position — no new map data structure needed
- Stat scaling applied at spawn time (deterministic via seed + position)
- All scaling flows through existing `EntityGenerator` and `Entity` stat system
- Loot scaling flows through existing `LOOT_TABLES` selection
- AI zone awareness flows through existing goal evaluation

---

## Dependencies

- Entity generator system (already exists)
- Loot table system (already exists)
- Goal evaluation system (already exists)
- Terrain/region system (already exists)

---

## Estimated Scope

- Backend: ~6 files modified (generator.py, config.py, models.py, scorers.py, loot tables, world_loop.py)
- Frontend: ~4 files modified (useCanvas zone overlay, InspectPanel, minimap, tooltip)
- Data: Zone definitions, multiplier tables, entity zone requirements
