# World Generation

Technical documentation for the world map, tile types, zone placement, terrain regions, resource nodes, and map structures.

---

## Overview

The simulation world is a **128×128** 2D tile grid generated deterministically from `world_seed`. World generation places town, sanctuary, terrain regions, goblin camps, roads, ruins, dungeon entrances, resource nodes, and treasure chests.

**Primary files:** `src/core/grid.py`, `src/core/enums.py`, `src/api/engine_manager.py`, `src/core/resource_nodes.py`

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
4. Generate **terrain regions** (FOREST, DESERT, SWAMP, MOUNTAIN)
5. Scatter **resource nodes** per region
6. Place **goblin camps** (CAMP tiles, far from town)
7. Place **treasure chests** near camps
8. Generate **roads** from town to nearby camps and regions
9. Place **ruins** (scattered 3×3 patches)
10. Place **dungeon entrances** (remote single tiles)
11. Spawn **hero** at town center
12. Spawn **goblins** on FLOOR tiles
13. Spawn **race-specific mobs** per terrain region
14. Spawn **camp guards** at each camp
15. Place **town buildings**

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

### Region Generation

1. For each terrain type, attempt to place N regions
2. Each center must be ≥ `region_min_distance` from other centers and ≥ `camp_min_distance_from_town` from town
3. Tiles painted in a diamond (Manhattan distance) shape with edge noise for organic feel
4. Radius randomized between `region_min_radius` and `region_max_radius`

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_forest_regions` | 4 | Forest region count |
| `num_desert_regions` | 3 | Desert region count |
| `num_swamp_regions` | 3 | Swamp region count |
| `num_mountain_regions` | 3 | Mountain region count |
| `region_min_radius` | 6 | Minimum region radius (tiles) |
| `region_max_radius` | 12 | Maximum region radius (tiles) |
| `region_min_distance` | 8 | Minimum distance between centers |

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

## Roads

Generated from town center to the 3 closest camps and 2 closest region centers using axis-aligned paths. Only placed on FLOOR tiles. Entities on ROAD tiles receive a +30% movement speed bonus.

Config: `road_from_town: bool` (default `true`).

---

## Ruins

4 scattered 3×3 patches of RUINS tiles placed on FLOOR/ROAD tiles, at least 8 tiles apart and not too close to town.

Config: `num_ruins: int` (default 4).

---

## Dungeon Entrances

2 single-tile DUNGEON_ENTRANCE markers placed in remote locations (FLOOR, MOUNTAIN, or FOREST), far from town. Reserved for future dungeon system.

Config: `num_dungeon_entrances: int` (default 2).
