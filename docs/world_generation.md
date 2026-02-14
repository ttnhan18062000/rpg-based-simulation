# World Generation

Technical documentation for the world map, tile types, zone placement, terrain regions, resource nodes, and map structures.

---

## Overview

The simulation world is a **512×512** 2D tile grid generated deterministically from `world_seed`. World generation places town, sanctuary, 8 biome types via Voronoi tessellation, enemy camps, roads, ruins, dungeon entrances, portals, outposts, watchtowers, graveyards, obelisks, fishing spots, resource nodes, and treasure chests.

**Primary files:** `src/core/grid.py`, `src/core/enums.py`, `src/api/engine_manager.py`, `src/core/resource_nodes.py`, `src/core/regions.py`, `src/systems/terrain_detail.py`, `src/core/faction.py`

---

## Tile Materials

23 tile types defined in `Material` enum (`src/core/enums.py`):

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
| 15 | GRASSLAND | Yes | Open plains — centaurs |
| 16 | SNOW | Yes | Frozen tundra — frost kin |
| 17 | JUNGLE | Yes | Dense tropical canopy — lizardfolk |
| 18 | SHALLOW_WATER | Yes | Wading depth, slow movement |
| 19 | FARMLAND | Yes | Cultivated land, fast movement |
| 20 | CAVE | Yes | Underground passages |
| 21 | VOLCANIC | Yes | Ash and magma terrain — demons |
| 22 | GRAVEYARD | Yes | Haunted burial grounds |

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
6. Create **Region objects** with sub-locations (camps, ruins, dungeons, shrines, groves, boss arenas, outposts, watchtowers, portals, graveyards, obelisks, fishing spots)
7. **Terrain detail generation** — add intra-region variety (clearings, streams, cliffs, pools, roads, shallow water, farmland, caves)
8. Generate **roads** from town to nearest 8 regions (paints over any biome terrain, bridges water)
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
| `town_center_x` | 256 | Town center X coordinate |
| `town_center_y` | 256 | Town center Y coordinate |
| `town_radius` | 6 | Half-width of the town square |

Creates a **13×13 town** (radius 6 in each direction) centered at (256, 256) — the map center.

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
| `sanctuary_radius` | 12 | Half-width of the sanctuary square |

Creates a **25×25 sanctuary area** (radius 12) with the **13×13 town** in the center. Only FLOOR tiles are converted — TOWN tiles are preserved.

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
| `camp_min_distance_from_town` | 60 | Minimum Manhattan distance from town |
| `camp_max_guards` | 5 | Maximum guards per camp |

Each camp is a **5×5 area** of CAMP tiles. Placement uses deterministic RNG with distance constraints (from town and from other camps).

### Camp Spawns

Each camp receives:
- **1 Goblin Chief** (ELITE tier, `GUARD_CAMP` state)
- **Up to N Goblin Warriors** (WARRIOR tier, `GUARD_CAMP` state)

Guards patrol within the camp radius and engage intruders.

---

## Terrain Regions

Eight terrain biomes generated as organic regions across the map. Each hosts a unique mob race, faction, and resource nodes.

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
| `terrain` | Material | FOREST, DESERT, SWAMP, MOUNTAIN, GRASSLAND, SNOW, JUNGLE, or VOLCANIC |
| `center` | Vector2 | Voronoi seed position |
| `radius` | int | Effective radius (max tile distance) |
| `difficulty` | int | 1–4 (based on distance from town) |
| `locations` | list[Location] | Sub-locations within region |

### Sub-Locations (3–6 per region)

| Type | Description | Spawns / Tiles |
|------|-------------|--------|
| `enemy_camp` | CAMP tiles, guards | Chief + warriors + race mobs |
| `resource_grove` | Resource nodes cluster | 3–5 harvestable nodes |
| `ruins` | RUINS tiles | Treasure chest |
| `dungeon_entrance` | DUNGEON_ENTRANCE tile | Elite guards, treasure chest |
| `shrine` | Gameplay marker | (future) |
| `boss_arena` | Boss fight area | Elite boss + guards (difficulty+1) |
| `outpost` | Safe zone building | Placed at difficulty < 3 |
| `watchtower` | Scouting structure | Forest, grassland, jungle biomes |
| `portal` | Fast travel point | Placed at difficulty ≥ 3 |
| `fishing_spot` | Water-adjacent resource | Random fill location |
| `graveyard` | GRAVEYARD tiles (5×5) | Swamp, snow biomes |
| `obelisk` | Ancient buff shrine | Desert, volcanic, mountain biomes |

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_forest_regions` | 4 | Forest region count |
| `num_desert_regions` | 3 | Desert region count |
| `num_swamp_regions` | 3 | Swamp region count |
| `num_mountain_regions` | 3 | Mountain region count |
| `num_grassland_regions` | 4 | Grassland region count |
| `num_snow_regions` | 3 | Snow region count |
| `num_jungle_regions` | 3 | Jungle region count |
| `num_volcanic_regions` | 2 | Volcanic region count |
| `region_min_radius` | 30 | Minimum effective radius |
| `region_max_radius` | 60 | Maximum effective radius |
| `region_min_distance` | 40 | Minimum distance between centers |
| `min_locations_per_region` | 3 | Min sub-locations per region |
| `max_locations_per_region` | 6 | Max sub-locations per region |
| `location_min_spacing` | 5 | Min distance between locations |

### Difficulty Zones

| Distance from Town | Tier | HP/ATK/DEF Mult | XP/Gold Mult |
|-------------------|------|-----------------|---------------|
| ≤ 80 | 1 | 1.0× | 1.0× |
| ≤ 150 | 2 | 1.5×/1.3×/1.2× | 1.5× |
| ≤ 220 | 3 | 2.5×/2.0×/1.8× | 3.0× |
| > 220 | 4 | 4.0×/3.0×/2.5× | 5.0× |

### Terrain → Race → Faction Mapping

| Terrain | Race | Faction | Mob Tiers (Basic → Elite) |
|---------|------|---------|---------------------------|
| FOREST | Wolf | WOLF_PACK | wolf → dire_wolf → alpha_wolf |
| DESERT | Bandit | BANDIT_CLAN | bandit → bandit_archer → bandit_chief |
| SWAMP | Undead | UNDEAD | skeleton → zombie → lich |
| MOUNTAIN | Orc | ORC_TRIBE | orc → orc_warrior → orc_warlord |
| GRASSLAND | Centaur | CENTAUR_HERD | centaur → centaur_lancer → centaur_elder |
| SNOW | Frost | FROST_KIN | frost_wolf → frost_giant → frost_shaman |
| JUNGLE | Lizard | LIZARDFOLK | lizard → lizard_warrior → lizard_chief |
| VOLCANIC | Demon | DEMON_HORDE | imp → hellhound → demon_lord |

### Race Stat Modifiers (`RACE_STAT_MODS`)

| Race | HP Mult | ATK Mult | DEF Mod | SPD Mod | Crit | Evasion | Luck |
|------|---------|----------|---------|---------|------|---------|------|
| Wolf | 0.8× | 1.1× | -1 | +3 | 8% | 6% | 1 |
| Bandit | 1.0× | 1.0× | +1 | +1 | 10% | 4% | 3 |
| Undead | 1.3× | 0.9× | +2 | -2 | 4% | 0% | 0 |
| Orc | 1.4× | 1.2× | +3 | -1 | 6% | 2% | 1 |
| Centaur | 1.1× | 1.1× | 0 | +4 | 6% | 8% | 2 |
| Frost | 1.6× | 1.0× | +4 | -3 | 3% | 0% | 0 |
| Lizard | 0.9× | 1.0× | 0 | +2 | 12% | 10% | 2 |
| Demon | 1.2× | 1.3× | -1 | +1 | 8% | 4% | 1 |

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
|---------|--------------|--------|-------------|---------|----------|
| **FOREST** | herb_patch | herb | 3 | 25 | 2 |
| | timber | wood | 4 | 30 | 3 |
| | berry_bush | wild_berries | 2 | 20 | 1 |
| **DESERT** | gem_deposit | raw_gem | 2 | 35 | 3 |
| | cactus_fiber | fiber | 3 | 20 | 2 |
| | sand_iron | iron_ore | 3 | 30 | 3 |
| **SWAMP** | mushroom_grove | glowing_mushroom | 3 | 25 | 2 |
| | bog_iron | iron_ore | 3 | 30 | 3 |
| | dark_moss | dark_moss | 2 | 20 | 2 |
| **MOUNTAIN** | ore_vein | iron_ore | 4 | 30 | 3 |
| | crystal_node | enchanted_dust | 2 | 40 | 4 |
| | granite_quarry | stone_block | 3 | 35 | 3 |
| **GRASSLAND** | wheat_field | wheat | 4 | 20 | 2 |
| | herb_patch | herb | 3 | 25 | 2 |
| | berry_bush | wild_berries | 2 | 20 | 1 |
| **SNOW** | ice_crystal | frost_shard | 2 | 40 | 3 |
| | frozen_herb | herb | 2 | 30 | 3 |
| | mammoth_bone | bone | 3 | 35 | 3 |
| **JUNGLE** | exotic_plant | herb | 3 | 25 | 2 |
| | venom_gland | venom | 2 | 30 | 2 |
| | timber | wood | 4 | 30 | 3 |
| **VOLCANIC** | obsidian_vein | obsidian | 3 | 35 | 3 |
| | sulfur_pit | sulfur | 2 | 30 | 2 |
| | fire_crystal | enchanted_dust | 2 | 40 | 4 |

Wild Berry Bushes (12 total) are also placed on FLOOR tiles.

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
| **Forest** | Clearings | FLOOR | 4% | Open areas amid dense trees |
| | Dense groves | WALL | 1% | Impassable thick trees (sparse) |
| | Streams | WATER | river | Winding water lines with BRIDGE crossings |
| | Forest paths | ROAD | network | Roads connecting locations |
| **Desert** | Rocky ridges | WALL | 1.5% | Sparse stone outcrops |
| | Oases | WATER | 0.5% | Rare water patches |
| | Hard ground | FLOOR | 3% | Walkable clearings |
| | Caravan routes | ROAD | network | Roads connecting locations |
| **Swamp** | Stagnant pools | WATER | 6% | Impassable water bodies |
| | Shallow areas | SHALLOW_WATER | 4% | Walkable wading areas |
| | Thickets | WALL | 1% | Sparse dead tree barriers |
| | Mudflats | FLOOR | 3% | Walkable clearings |
| | Bog paths | ROAD/BRIDGE | network | Paths with bridges over water |
| **Mountain** | Cliff faces | WALL | 2% | Sparse rock walls |
| | Valleys | FLOOR | 4% | Open areas between peaks |
| | Lava vents | LAVA | 0.8% | Only at difficulty ≥ 3 |
| | Caves | CAVE | 0.5% | Underground passages |
| | Mountain passes | ROAD | network | Roads connecting locations |
| **Grassland** | Wildflowers | FLOOR | 3% | Open meadow clearings |
| | Ponds | SHALLOW_WATER | 0.8% | Small wading pools |
| | Farmland | FARMLAND | 2% | Cultivated patches |
| | Trails | ROAD | network | Roads connecting locations |
| **Snow** | Ice sheets | WATER | 3% | Frozen impassable lakes |
| | Frozen ridges | WALL | 1.5% | Sparse icy barriers |
| | Tundra clearings | FLOOR | 3% | Exposed ground patches |
| | Frost paths | ROAD | network | Roads connecting locations |
| **Jungle** | Canopy gaps | FLOOR | 3% | Light-filled clearings |
| | Dense undergrowth | WALL | 1.5% | Sparse impassable vines |
| | Jungle streams | WATER | river | Winding tropical rivers |
| | Shallow marshes | SHALLOW_WATER | 2% | Wading swamp edges |
| | Jungle trails | ROAD | network | Roads connecting locations |
| **Volcanic** | Lava flows | LAVA | 2% | Impassable molten rock |
| | Obsidian walls | WALL | 1.5% | Sparse volcanic glass barriers |
| | Ash fields | FLOOR | 4% | Walkable ash-covered clearings |
| | Volcanic caves | CAVE | 0.5% | Underground lava tubes |
| | Magma paths | ROAD | network | Roads connecting locations |

> **Wall fix:** Wall generation was drastically reduced from 3–8% to 1–2% chance with max cluster size 2 (was 3–5) to eliminate excessive walls and isolated spots.

### Feature Placement

- **Scatter features:** Deterministic per-tile chance check → cluster of tiles painted around seed point
- **Rivers:** Winding horizontal/vertical water lines with drift, BRIDGE tiles placed at walkable crossings
- **Road networks:** MST-like connection between locations within each region, L-shaped paths, BRIDGE over water
- **Difficulty-gated:** Lava vents only appear in regions with difficulty ≥ 3

### Determinism

All terrain detail generation uses `DeterministicRNG` with `Domain.MAP_GEN`. Same seed = identical terrain.

---

## Roads

Generated from town center to the **8 nearest region centers** using axis-aligned L-shaped paths. Roads paint over any walkable biome terrain (FLOOR, FOREST, DESERT, SWAMP, MOUNTAIN, GRASSLAND, SNOW, JUNGLE, VOLCANIC, FARMLAND, GRAVEYARD). Water tiles are replaced with BRIDGE. Additional intra-region roads connect locations within each region (see Terrain Detail above).

Entities on ROAD or BRIDGE tiles receive a **+30% movement speed bonus** in `MoveAction.apply()`.

Config: `road_from_town: bool` (default `true`).
