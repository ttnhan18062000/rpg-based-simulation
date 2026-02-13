# Epic 15: Region & World Overhaul

## Summary

Overhaul the world map from scattered terrain blobs into a dense, structured world of **named regions** containing **sub-locations** (camps, groves, ruins, shrines, boss arenas). Each region has a terrain type, difficulty tier, unique name, and a roster of content. The map shifts from ~70% empty floor to a rich, layered world where every area has identity and purpose.

Inspired by: WoW's named zones, Diablo region tiers, Skyrim holds, Terraria biomes, Runescape areas.

---

## Motivation — Problems with Current System

| Problem | Current State |
|---------|--------------|
| **Map is mostly empty** | ~70% FLOOR tiles, regions are tiny blobs (radius 6–12) — FIXED: Voronoi fills 99%+ |
| **Regions have no identity** | Just terrain paint — no names, no data model, no structure — FIXED |
| **No locations within regions** | Camps, ruins, dungeons are placed independently of regions |
| **No difficulty progression** | A goblin near town = a goblin at the map edge |
| **No reason to explore** | No content gradient, no reward for venturing further |
| **Minimap shows no region info** | No labels, no named areas, just colored tiles |

---

## Core Architecture Change

### Current: Terrain Blobs
```
Grid[128×128] → tiles are Material enum (FLOOR, FOREST, DESERT, ...)
Regions = just painted tiles, no data model
Camps/ruins/dungeons placed randomly on FLOOR
```

### New: Voronoi-Tessellated Named Regions
```
Region {
  region_id: str          # "whispering_woods"
  name: str               # "Whispering Woods"
  terrain: Material       # FOREST
  center: Vector2         # Voronoi seed point
  radius: int             # computed max extent from Voronoi territory
  difficulty: int         # 1–4
  locations: [Location]   # 3–6 sub-locations each
}

Generation: Voronoi tessellation — place 8 region centers as seeds,
then assign every non-town tile to its nearest center (Manhattan).
Regions border each other like countries on a continent — no empty gaps.
find_region_at(pos, regions) returns nearest-center region (O(n) lookup).
```

Location {
  location_id: str        # "goblin_outpost_1"
  name: str               # "Goblin Outpost"
  location_type: str      # camp | resource_grove | ruins | dungeon | shrine | boss_arena
  pos: Vector2
  region_id: str
}
```

---

## Features

### F1: Region Data Model & Generation

- New `Region` dataclass in `src/core/regions.py`
- New `Location` dataclass in same file
- `WorldState` gains `regions: list[Region]`
- `Snapshot` gains `regions: tuple[Region, ...]`
- Map generation in `engine_manager._build()` refactored:
  - Place **6–8 large regions** (radius 15–25) around the map
  - Each region is a named area with a unique identity
  - Regions **fill most of the map** — only narrow "wilds" gaps between them
  - Town and sanctuary remain at center
  - Difficulty tiers assigned by distance from town:
    - **Tier 1 (Outskirts):** nearest 2 regions — level 1–3 enemies
    - **Tier 2 (Frontier):** middle 2–3 regions — level 3–6 enemies
    - **Tier 3 (Wilds):** far 2 regions — level 5–10 enemies
    - **Tier 4 (Depths):** farthest 1–2 regions — level 8–15 enemies

**Region Name Tables** (per terrain):
- Forest: Whispering Woods, Verdant Hollow, Thornwood, Mossy Glen, Eldergrove
- Desert: Scorched Wastes, Dustwind Basin, Sunfire Plateau, Sandstone Reach
- Swamp: Rotmire Bog, Gloomfen, Witchwater Marsh, Deadtide Swamp
- Mountain: Ironpeak Ridge, Stormcrag Heights, Frostbreak Summit, Ashvein Slopes

### F2: Sub-Locations Within Regions

Each region contains **3–6 locations** drawn from:

| Location Type | Description | Content |
|--------------|-------------|---------|
| **enemy_camp** | Fortified mob outpost | Camp guards + chief, loot drops |
| **resource_grove** | Cluster of 3–5 harvestable nodes | Terrain-specific resources |
| **ruins** | Ancient structure | Treasure chest, lore, rare spawn |
| **dungeon_entrance** | Gateway to danger | Elite guards, high-tier chest |
| **shrine** | Passive buff zone | Temporary buff for heroes who visit |
| **boss_arena** | Open area with a named boss | Unique elite with boosted stats + special loot |

Location placement rules:
- Locations placed within the region's radius
- Minimum spacing between locations (5+ tiles)
- At least 1 enemy_camp and 1 resource_grove per region
- Dungeons and boss_arenas only in tier 3+ regions
- Shrines only in tier 1–2 regions (help newer heroes)

### F3: Enemy Stat Scaling by Region Difficulty

Enemies spawned in a region inherit its difficulty tier as a stat multiplier:

| Stat | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|------|--------|--------|--------|--------|
| HP | 1.0× | 1.5× | 2.5× | 4.0× |
| ATK | 1.0× | 1.3× | 2.0× | 3.0× |
| DEF | 1.0× | 1.2× | 1.8× | 2.5× |
| XP reward | 1.0× | 1.5× | 3.0× | 5.0× |
| Gold drop | 1.0× | 1.5× | 2.5× | 4.0× |
| Level range | 1–3 | 3–6 | 5–10 | 8–15 |

- Multipliers applied at spawn time via `EntityGenerator`
- Entity stores `region_id` and `difficulty_tier` for display/AI use
- Boss arena mobs get an additional 1.5× on top of region multiplier

### F4: Loot Quality Scaling

| Tier | Loot Pool | Chest Tier |
|------|-----------|------------|
| 1 | Common only | 1 |
| 2 | Common + Uncommon | 1–2 |
| 3 | Uncommon + Rare | 2–3 |
| 4 | Rare + Epic | 3–4 |

- Loot table selection keyed by `region.difficulty` at time of enemy death
- Treasure chests placed in locations inherit the region's tier

### F5: Enemy Type Distribution by Terrain + Tier

| Terrain | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---------|--------|--------|--------|--------|
| Forest | wolves | dire_wolves | alpha_wolf (boss) | — |
| Desert | bandits | bandit warriors | bandit_chief (boss) | — |
| Swamp | undead | skeleton warriors | lich (boss) | — |
| Mountain | orcs | orc warriors | orc_warlord (boss) | — |
| Mixed | goblins | goblin warriors | goblin_chief | goblin_chief (elite) |

- Generator filters spawn pool by `region.terrain` + `region.difficulty`
- Each terrain has a native race; goblins appear in any terrain
- Boss-tier enemies only spawn in boss_arena locations

### F6: Frontend — Region Labels on Minimap

- Draw **semi-transparent region name text** on the minimap canvas at each region center
  - Font: 7–8px, white with ~40% opacity, text-shadow for readability
  - Only shown when minimap zoom ≥ 1.5× (avoid clutter at default zoom)
- Region boundary shown as a subtle colored outline (terrain color at 15% opacity)

### F7: Frontend — Locations List (Below Minimap)

Enhance the existing **Locations panel** to include:
- **Region headers** — collapsible groups, e.g., "🌲 Whispering Woods (Tier 2)"
- **Sub-locations** — indented under region, clickable to focus map
  - Icon by type: ⚔️ camp, 🌿 grove, 🏚️ ruins, 🕳️ dungeon, ⛩️ shrine, 💀 boss
- **Difficulty badge** — colored tier indicator (green/yellow/orange/red)
- **Entity count** — live count of alive enemies in each region
- Clicking a location centers the main canvas on it (existing `jumpToLocation`)

### F8: Hero Difficulty Awareness (AI)

- `GoalScorer` considers region difficulty vs hero level:
  - **Explore penalty**: heroes avoid regions where `difficulty × 3 > hero_level + 3`
  - **Explore bonus**: heroes prefer regions where difficulty matches their power
  - **Flee adjustment**: `flee_hp_threshold` increased by `+0.1` per difficulty tier above hero's comfort zone
- Heroes naturally progress: town → tier 1 → tier 2 → etc.

### F9: Region Events

- Emit enriched events when heroes enter/leave regions:
  - `"region_enter"` — `{region_id, region_name, difficulty}`
  - `"region_leave"` — `{region_id}`
- Track `entity.current_region_id` for fast lookup

---

## Implementation Plan (Feature Order)

| Phase | Features | Effort |
|-------|----------|--------|
| **A** | F1 (data model + generation) + F2 (sub-locations) + F6 (minimap) + F7 (locations list) | L | ✅ DONE |
| **B** | F3 (stat scaling) + F5 (enemy types) | M | ✅ DONE |
| **C** | F4 (loot scaling) + F9 (region events) | M | ✅ DONE |
| **D** | F8 (AI awareness) | S | ✅ DONE |

Total estimated effort: **XL** (largest ticket so far)

---

## Design Principles

- Regions are first-class data objects, not just terrain paint
- All region/location data flows through Snapshot to frontend
- Stat scaling at spawn time — deterministic via seed + position
- Backward compatible: existing camps/ruins become locations within regions
- Dense map: Voronoi tessellation achieves **<1% empty floor** (vs original ~70%)

---

## Files Affected

**New files:**
- `src/core/regions.py` — Region + Location dataclasses, name tables, difficulty config

**Backend (modified):**
- `src/config.py` — region count, radius range, difficulty zone boundaries
- `src/core/world_state.py` — add `regions` list
- `src/core/snapshot.py` — add `regions` tuple
- `src/core/models.py` — add `region_id`, `difficulty_tier` to Entity
- `src/api/engine_manager.py` — refactor `_build()` for new region generation
- `src/systems/generator.py` — spawn scaling by difficulty tier
- `src/core/items.py` — loot table keyed by difficulty
- `src/ai/goals/` — region-aware goal scoring
- `src/api/schemas.py` — RegionSchema, LocationSchema
- `src/api/routes/state.py` — serialize regions in state response

**Frontend (modified):**
- `frontend/src/types/api.ts` — Region, Location types
- `frontend/src/components/GameCanvas.tsx` — minimap region labels + boundaries
- `frontend/src/components/GameCanvas.tsx` — enhanced Locations panel with region groups
