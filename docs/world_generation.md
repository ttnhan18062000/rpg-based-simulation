# World Generation

Technical documentation for the world map, tile types, zone placement, terrain regions, resource nodes, and map structures.

---

## Overview

The simulation world is a **128×128** 2D tile grid generated deterministically from `world_seed`. World generation places town, sanctuary, terrain regions, goblin camps, roads, ruins, dungeon entrances, resource nodes, and treasure chests.

**Primary files:** `src/core/grid.py`, `src/core/enums.py`, `src/api/engine_manager.py`, `src/core/resource_nodes.py`, `src/core/regions.py`, `src/systems/terrain_detail.py`

---

## Tile Materials

15 tile types defined in `Material` enum (`src/core/enums.py`):

| Value | Name | Walkable | Description |
|-------|------|----------|-------------|
| 0 | FLOOR | Yes | Default open terrain |
| 1 | WALL | No | Impassable barrier |
| 2 | WATER | No | Impassable (currently) |
| 3 | TOWN | Yes | Hero safe zone |
| 4 | CAMP | Yes | Enemy stronghold |
| 5 | SANCTUARY | Yes | Debuff buffer around town |
| 6 | FOREST | Yes | Dense woodland — wolves |
| 7 | DESERT | Yes | Arid wasteland — bandits |
| 8 | SWAMP | Yes | Dark bogland — undead |
| 9 | MOUNTAIN | Yes | Rocky highlands — orcs |
| 10 | ROAD | Yes | Speed bonus (+30%) for movement |
| 11 | BRIDGE | Yes | Speed bonus, crosses water |
| 12 | RUINS | Yes | Explorable structures |
| 13 | DUNGEON_ENTRANCE | Yes | Future dungeon access point |
| 14 | LAVA | No | Impassable hazard |

### Movement Rules

All factions can enter all walkable tiles. There are no hard movement restrictions per faction — consequences of trespassing are handled by the territory system (debuffs, alerts, aura damage) rather than movement blocking.

### Grid Helpers (`src/core/grid.py`)

```python
grid.is_walkable(pos)    # FLOOR, TOWN, CAMP, SANCTUARY, FOREST–MOUNTAIN, ROAD, BRIDGE, RUINS, DUNGEON_ENTRANCE
grid.is_town(pos)        # TOWN only
grid.is_camp(pos)        # CAMP only
grid.is_sanctuary(pos)   # SANCTUARY only
grid.is_forest(pos)      # FOREST only
grid.is_desert(pos)      # DESERT only
grid.is_swamp(pos)       # SWAMP only
grid.is_mountain(pos)    # MOUNTAIN only
```

---

## Generation Order

World generation in `EngineManager._build()`:

1. Create empty grid (all FLOOR)
2. Place **TOWN** tiles (square at town center)
3. Place **SANCTUARY** tiles (ring around town, only replaces FLOOR)
4. Place **region seeds** (centers for Voronoi tessellation)
5. **Voronoi assignment** — paint every non-town tile with nearest region's terrain
6. Create **Region objects** with sub-locations (camps, ruins, dungeons, shrines, groves, boss arenas)
7. **Terrain detail generation** — add intra-region variety (clearings, streams, cliffs, pools, roads)
8. Generate **roads** from town to nearest 4 regions
9. Place **town buildings** (store, blacksmith, guild, class hall, inn)
10. Spawn **hero** at town center
11. Spawn **initial mobs** (wandering goblins)
12. Spawn **region mobs** — race-specific entities at camps, dungeons, boss arenas
13. Spawn **roaming mobs** throughout each region
14. Place **resource nodes** at resource grove locations
15. Place **wild berry bushes** on FLOOR tiles

---

## Zone: Town

The safe zone where the hero spawns, rests, heals, and accesses buildings.

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `town_center_x` | 12 | Town center X coordinate |
| `town_center_y` | 12 | Town center Y coordinate |
| `town_radius` | 4 | Half-width of the town square |

Creates a **9×9 town** (radius 4 in each direction) centered at (12, 12).

### Behavior

- **Hero healing:** Heroes in `RESTING_IN_TOWN` heal `hero_heal_per_tick` (3) HP/tick
- **Town passive heal:** Heroes in town regenerate `town_passive_heal` (1) HP/tick even outside rest state — blocked when adjacent hostile is in melee range
- **Town aura damage:** Hostile entities on TOWN tiles lose `town_aura_damage` (2) HP/tick
- **Hero respawn:** Dead heroes teleport to town center, enter `RESTING_IN_TOWN`

---

## Zone: Sanctuary

A debuff ring surrounding the town that weakens enemies.

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sanctuary_radius` | 7 | Half-width of the sanctuary square |

Creates a **15×15 sanctuary area** (radius 7) with the **9×9 town** in the center. Only FLOOR tiles are converted — TOWN tiles are preserved.

### Behavior

- Non-hero entities on sanctuary tiles receive territory debuffs (ATK/DEF multiplied by configurable values)
- Enemy AI triggers retreat behavior on sanctuary tiles
- Heroes fight at full strength on sanctuary tiles

---

## Zone: Goblin Camps

Enemy strongholds placed far from town, defended by guards.

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_camps` | 8 | Number of goblin camps |
| `camp_radius` | 2 | Half-width of each camp square |
| `camp_min_distance_from_town` | 25 | Minimum Manhattan distance from town |
| `camp_max_guards` | 5 | Maximum guards per camp |

Each camp is a **5×5 area** of CAMP tiles. Placement uses deterministic RNG with distance constraints (from town and from other camps).

### Camp Spawns

Each camp receives:
- **1 Goblin Chief** (ELITE tier, `GUARD_CAMP` state)
- **Up to N Goblin Warriors** (WARRIOR tier, `GUARD_CAMP` state)

Guards patrol within the camp radius and engage intruders.

---

## Terrain Regions

Four terrain types generated as organic regions across the map. Each hosts a unique mob race and resource nodes.

### Voronoi Tessellation (epic-15)

1. Place region seed centers with distance constraints
2. **Voronoi assignment:** for every non-town tile, find the nearest region center and paint with that region's terrain — no gaps, regions border each other like countries
3. Compute effective radius per region (max distance of any owned tile from center)
4. Assign difficulty tier based on Manhattan distance from town center

This ensures 100% terrain coverage — no FLOOR gaps between regions.

### Region Data Model (`src/core/regions.py`)

| Field | Type | Description |
|-------|------|-------------|
| `region_id` | str | Unique slug |
| `name` | str | Display name (from name tables) |
| `terrain` | Material | FOREST, DESERT, SWAMP, or MOUNTAIN |
| `center` | Vector2 | Voronoi seed position |
| `radius` | int | Effective radius (max tile distance) |
| `difficulty` | int | 1–4 (based on distance from town) |
| `locations` | list[Location] | Sub-locations within region |

### Sub-Locations (3–6 per region)

| Type | Description | Spawns |
|------|-------------|--------|
| `enemy_camp` | CAMP tiles, guards | Chief + warriors + race mobs |
| `resource_grove` | Resource nodes cluster | 3–5 harvestable nodes |
| `ruins` | RUINS tiles | Treasure chest |
| `dungeon_entrance` | DUNGEON_ENTRANCE tile | Elite guards, treasure chest |
| `shrine` | Gameplay marker | (future) |
| `boss_arena` | Boss fight area | Elite boss + guards (difficulty+1) |

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_forest_regions` | 2 | Forest region count |
| `num_desert_regions` | 2 | Desert region count |
| `num_swamp_regions` | 2 | Swamp region count |
| `num_mountain_regions` | 2 | Mountain region count |
| `region_min_distance` | 20 | Minimum distance between centers |
| `min_locations_per_region` | 3 | Min sub-locations per region |
| `max_locations_per_region` | 6 | Max sub-locations per region |
| `location_min_spacing` | 5 | Min distance between locations |

### Difficulty Zones

| Distance from Town | Tier | HP/ATK/DEF Mult | XP/Gold Mult |
|-------------------|------|-----------------|---------------|
| ≤ 35 | 1 | 1.0× | 1.0× |
| ≤ 60 | 2 | 1.5×/1.3×/1.2× | 1.5× |
| ≤ 90 | 3 | 2.5×/2.0×/1.8× | 3.0× |
| > 90 | 4 | 4.0×/3.0×/2.5× | 5.0× |

### Terrain → Race Mapping

| Terrain | Hosted Race | Mobs Spawned Per Region |
|---------|-------------|------------------------|
| FOREST | Wolf | 2–4 basic + 1 elite |
| DESERT | Bandit | 2–4 basic + 1 elite |
| SWAMP | Undead | 2–4 basic + 1 elite |
| MOUNTAIN | Orc | 2–4 basic + 1 elite |

---

## Resource Nodes

Harvestable resource nodes are scattered within terrain regions during world generation.

### Data Model (`src/core/resource_nodes.py`)

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | int | Unique ID |
| `resource_type` | str | e.g. "herb_patch", "ore_vein" |
| `name` | str | Display name |
| `pos` | Vector2 | Grid position |
| `terrain` | Material | Owning terrain type |
| `yields_item` | str | Item ID produced on harvest |
| `remaining` | int | Harvests left before depletion |
| `max_harvests` | int | Total harvests when fully grown |
| `respawn_cooldown` | int | Ticks to regenerate after depletion |
| `harvest_ticks` | int | Ticks to channel a single harvest |
| `cooldown_remaining` | int | Current cooldown counter |

### Resource Definitions (`TERRAIN_RESOURCES`)

| Terrain | Resource Type | Yields | Max Harvests | Respawn | Channel |
|---------|--------------|--------|-------------|---------|---------|
| **FOREST** | herb_patch | herb | 3 | 20 | 2 |
| | timber | wood | 4 | 25 | 3 |
| | berry_bush | wild_berries | 2 | 15 | 1 |
| **DESERT** | gem_deposit | raw_gem | 2 | 30 | 3 |
| | cactus_fiber | fiber | 3 | 20 | 2 |
| | sand_iron | iron_ore | 2 | 25 | 3 |
| **SWAMP** | mushroom_grove | glowing_mushroom | 3 | 20 | 2 |
| | bog_iron | iron_ore | 2 | 25 | 3 |
| | dark_moss | dark_moss | 4 | 15 | 1 |
| **MOUNTAIN** | ore_vein | iron_ore | 3 | 25 | 3 |
| | crystal_node | enchanted_dust | 1 | 35 | 4 |
| | granite_quarry | stone_block | 5 | 20 | 2 |

Wild Berry Bushes (8 total) are also placed on FLOOR tiles.

### Node Lifecycle

```
Available (remaining > 0, cooldown = 0)
    │  hero harvests
    ▼
remaining -= 1, hero receives yields_item
    ├── remaining > 0 → still available
    └── remaining == 0 → depleted
            │  cooldown_remaining = respawn_cooldown
            ▼
        Depleted (grey on map)
            │  each tick: cooldown_remaining -= 1
            ▼  cooldown == 0
        Respawned (remaining = max_harvests)
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `resources_per_region` | 4 | Nodes spawned per region |
| `resource_respawn_ticks` | 30 | Default respawn cooldown |
| `harvest_duration` | 2 | Default channel ticks |

---

## Terrain Detail Generation (epic-09 F9)

After Voronoi paints uniform terrain, `TerrainDetailGenerator` (`src/systems/terrain_detail.py`) adds intra-region variety. Each biome has distinct natural features.

### Per-Biome Features

| Biome | Feature | Material | Chance | Description |
|-------|---------|----------|--------|-------------|
| **Forest** | Clearings | FLOOR | 6% | Open areas amid dense trees |
| | Dense groves | WALL | 3% | Impassable thick trees |
| | Streams | WATER | river | Winding water lines with BRIDGE crossings |
| | Forest paths | ROAD | network | Roads connecting locations |
| **Desert** | Rocky ridges | WALL | 4% | Impassable stone outcrops |
| | Oases | WATER | 0.8% | Rare water patches |
| | Hard ground | FLOOR | 5% | Walkable clearings |
| | Caravan routes | ROAD | network | Roads connecting locations |
| **Swamp** | Stagnant pools | WATER | 12% | Impassable water bodies |
| | Thickets | WALL | 3% | Dead tree barriers |
| | Mudflats | FLOOR | 4% | Walkable clearings |
| | Bog paths | ROAD/BRIDGE | network | Paths with bridges over water |
| **Mountain** | Cliff faces | WALL | 8% | Impassable rock walls |
| | Valleys | FLOOR | 6% | Open areas between peaks |
| | Lava vents | LAVA | 1.5% | Only at difficulty ≥ 3 |
| | Mountain passes | ROAD | network | Roads connecting locations |

### Feature Placement

- **Scatter features:** Deterministic per-tile chance check → cluster of tiles painted around seed point
- **Rivers:** Winding horizontal/vertical water lines with drift, BRIDGE tiles placed at walkable crossings
- **Road networks:** MST-like connection between locations within each region, L-shaped paths, BRIDGE over water
- **Difficulty-gated:** Lava vents only appear in regions with difficulty ≥ 3

### Determinism

All terrain detail generation uses `DeterministicRNG` with `Domain.MAP_GEN`. Same seed = identical terrain.

---

## Roads

Generated from town center to the 4 nearest region centers using axis-aligned L-shaped paths. Only placed on FLOOR tiles (preserves terrain). Additional intra-region roads connect locations (see Terrain Detail above).

Entities on ROAD tiles receive a **+30% movement speed bonus** in `MoveAction.apply()`.

Config: `road_from_town: bool` (default `true`).
