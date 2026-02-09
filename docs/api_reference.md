# REST API Reference

Technical documentation for all REST API endpoints, request/response schemas, and data fields.

---

## Overview

The simulation exposes a REST API via FastAPI, served by default at `http://127.0.0.1:8000`. The frontend polls these endpoints to render the simulation. All responses are JSON.

**Primary files**: `src/api/routes/state.py`, `src/api/routes/control.py`, `src/api/routes/map.py`, `src/api/schemas.py`

---

## Base URL

```
/api/v1
```

---

## Endpoints

### GET /api/v1/map

Returns the static tile grid. Called once on frontend init.

**Response**: `MapResponse`

```json
{
    "width": 32,
    "height": 32,
    "grid": [[0, 0, 1, ...], ...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `width` | int | Grid width in tiles |
| `height` | int | Grid height in tiles |
| `grid` | int[][] | 2D array of Material enum values (row-major: `grid[y][x]`) |

**Material values**: 0=Floor, 1=Wall, 2=Water, 3=Town, 4=Camp, 5=Sanctuary, 6=Forest, 7=Desert, 8=Swamp, 9=Mountain

---

### GET /api/v1/state

Returns current world state: entities and events. Polled every ~80ms by the frontend.

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since_tick` | int | 0 | Only return events since this tick |

**Response**: `WorldStateResponse`

```json
{
    "tick": 150,
    "alive_count": 12,
    "entities": [ ... ],
    "events": [ ... ],
    "ground_items": [ ... ],
    "buildings": [ ... ],
    "resource_nodes": [ ... ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Current simulation tick |
| `alive_count` | int | Number of alive entities |
| `entities` | EntitySchema[] | All alive entities with full data |
| `events` | EventSchema[] | Events since `since_tick` |
| `ground_items` | GroundItemSchema[] | Dropped loot on the ground |
| `buildings` | BuildingSchema[] | Town buildings (store, blacksmith, guild) |
| `resource_nodes` | ResourceNodeSchema[] | All resource nodes with availability state |

---

### GET /api/v1/stats

Returns simulation metadata and control state.

**Response**: `SimulationStats`

```json
{
    "tick": 150,
    "alive_count": 12,
    "total_spawned": 25,
    "total_deaths": 13,
    "running": true,
    "paused": false
}
```

---

### GET /api/v1/config

Returns the simulation configuration parameters.

**Response**: `SimulationConfigResponse`

```json
{
    "world_seed": 42,
    "grid_width": 32,
    "grid_height": 32,
    "max_ticks": 1000,
    "num_workers": 4,
    "initial_entity_count": 10,
    "generator_spawn_interval": 20,
    "generator_max_entities": 30,
    "vision_range": 6,
    "flee_hp_threshold": 0.3,
    "tick_rate": 0.05
}
```

---

### POST /api/v1/control/{action}

Control the simulation lifecycle.

| Action | Description |
|--------|-------------|
| `start` | Start the simulation (builds world if needed) |
| `pause` | Pause the simulation loop |
| `resume` | Resume from pause |
| `step` | Execute a single tick (while paused) |
| `reset` | Stop and rebuild the world from scratch |

**Response**: `ControlResponse`

```json
{
    "status": "ok",
    "message": "Simulation started.",
    "tick": 0
}
```

---

### POST /api/v1/speed?tps={tps}

Set the simulation speed in ticks per second.

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `tps` | int | 1–60 | Target ticks per second |

---

## Entity Schema

Full schema for each entity in the `/state` response:

```json
{
    "id": 1,
    "kind": "hero",
    "x": 5,
    "y": 3,
    "hp": 45,
    "max_hp": 67,
    "atk": 19,
    "def": 9,
    "spd": 11,
    "luck": 3,
    "crit_rate": 0.11,
    "evasion": 0.05,
    "level": 2,
    "xp": 35,
    "xp_to_next": 150,
    "gold": 125,
    "tier": 0,
    "faction": "hero_guild",
    "state": "WANDER",
    "weapon": "iron_sword",
    "armor": "chainmail",
    "accessory": null,
    "inventory_count": 6,
    "inventory_items": ["small_hp_potion", "small_hp_potion", "medium_hp_potion"],
    "vision_range": 6,
    "terrain_memory": {"5,3": 3, "6,3": 0, "4,2": 5, ...},
    "entity_memory": [
        {"id": 3, "x": 10, "y": 8, "kind": "goblin", "hp": 15, "max_hp": 21, "tick": 148, "visible": true},
        {"id": 7, "x": 20, "y": 15, "kind": "goblin_warrior", "hp": 30, "max_hp": 37, "tick": 120, "visible": false}
    ],
    "goals": ["Grow stronger — gain XP from enemies", "Explore unknown territory"],
    "known_recipes": ["craft_steel_sword", "craft_battle_axe"],
    "craft_target": "craft_enchanted_blade"
}
```

### Field Reference

#### Identity
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique entity identifier |
| `kind` | str | Entity type: `hero`, `goblin`, `goblin_scout`, `goblin_warrior`, `goblin_chief`, `wolf`, `dire_wolf`, `alpha_wolf`, `bandit`, `bandit_archer`, `bandit_chief`, `skeleton`, `zombie`, `lich`, `orc`, `orc_warrior`, `orc_warlord` |
| `x`, `y` | int | Grid position |
| `tier` | int | Enemy tier: 0=Basic, 1=Scout, 2=Warrior, 3=Elite |
| `faction` | str | Faction identity: `hero_guild`, `goblin_horde`, `wolf_pack`, `bandit_clan`, `undead`, `orc_tribe` |
| `state` | str | Current AI state (see AI States table below) |

#### Combat Stats
| Field | Type | Description |
|-------|------|-------------|
| `hp` | int | Current health points |
| `max_hp` | int | Maximum health points |
| `atk` | int | Effective attack (base + equipment + status effects) |
| `def` | int | Effective defense (base + equipment + status effects) |
| `spd` | int | Effective speed (base + equipment + status effects) |
| `luck` | int | Luck stat (affects crit/evasion bypass) |
| `crit_rate` | float | Effective critical hit rate (0.0–1.0) |
| `evasion` | float | Effective evasion rate (0.0–0.75) |

#### Progression
| Field | Type | Description |
|-------|------|-------------|
| `level` | int | Current level (1–50) |
| `xp` | int | Current experience points |
| `xp_to_next` | int | XP required for next level |
| `gold` | int | Gold currency |

#### Equipment
| Field | Type | Description |
|-------|------|-------------|
| `weapon` | str\|null | Equipped weapon item ID |
| `armor` | str\|null | Equipped armor item ID |
| `accessory` | str\|null | Equipped accessory item ID |
| `inventory_count` | int | Number of items in bag |
| `inventory_items` | str[] | List of item IDs in bag |

#### Vision & Memory
| Field | Type | Description |
|-------|------|-------------|
| `vision_range` | int | Manhattan distance vision range (from config) |
| `terrain_memory` | dict[str, int] | Remembered tiles: `"x,y"` → Material value |
| `entity_memory` | dict[] | Remembered entity sightings (see below) |
| `goals` | str[] | Current behavioral goals (derived server-side) |

#### Economy (hero only)
| Field | Type | Description |
|-------|------|-------------|
| `known_recipes` | str[] | Recipe IDs learned from blacksmith (e.g. `craft_steel_sword`) |
| `craft_target` | str\|null | Recipe ID the hero is currently working toward |

#### AI States
| State | Description |
|-------|-------------|
| `IDLE` | Default / just spawned |
| `WANDER` | Exploring (frontier-based) |
| `HUNT` | Moving toward visible enemy |
| `COMBAT` | Adjacent to enemy, fighting |
| `FLEE` | Low HP, retreating |
| `RETURN_TO_TOWN` | Heading to town to heal |
| `RESTING_IN_TOWN` | Healing in town |
| `RETURN_TO_CAMP` | Goblin returning to camp |
| `GUARD_CAMP` | Goblin guarding camp |
| `LOOTING` | Channeling loot pickup |
| `ALERT` | Defender responding to territory intrusion |
| `VISIT_SHOP` | Hero visiting the General Store |
| `VISIT_BLACKSMITH` | Hero visiting the Blacksmith |
| `VISIT_GUILD` | Hero visiting the Adventurer's Guild |
| `HARVESTING` | Hero channeling a resource harvest or moving to a node |

### Entity Memory Entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Remembered entity ID |
| `x`, `y` | int | Last known position |
| `kind` | str | Entity kind |
| `hp` | int | Last known HP |
| `max_hp` | int | Last known max HP |
| `tick` | int | Tick when last observed |
| `visible` | bool | Currently within vision range? |

---

## Ground Item Schema

```json
{
    "x": 12,
    "y": 8,
    "items": ["iron_sword", "small_hp_potion"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `x`, `y` | int | Grid position of the loot pile |
| `items` | str[] | List of item IDs dropped at this position |

Ground items are created when entities die (all inventory + equipment is dropped) and consumed when entities pick them up via the `LOOT` action.

---

## Building Schema

```json
{
    "building_id": "store",
    "name": "General Store",
    "x": 3,
    "y": 3,
    "building_type": "store"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `building_id` | str | Unique identifier (`store`, `blacksmith`, `guild`) |
| `name` | str | Display name |
| `x`, `y` | int | Grid position |
| `building_type` | str | Building category: `store`, `blacksmith`, `guild` |

Buildings are static — they do not move or change during the simulation. Three buildings are placed in the town at world generation.

---

## Resource Node Schema

```json
{
    "node_id": 1,
    "resource_type": "herb_patch",
    "name": "Herb Patch",
    "x": 37,
    "y": 36,
    "terrain": 6,
    "yields_item": "herb",
    "remaining": 3,
    "max_harvests": 3,
    "is_available": true,
    "harvest_ticks": 2
}
```

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | int | Unique node identifier |
| `resource_type` | str | Resource category (e.g. `herb_patch`, `ore_vein`, `timber`) |
| `name` | str | Display name |
| `x`, `y` | int | Grid position |
| `terrain` | int | Material enum value of the terrain this node belongs to (6–9) |
| `yields_item` | str | Item ID produced when harvested |
| `remaining` | int | Harvests remaining before depletion |
| `max_harvests` | int | Total harvests when fully grown |
| `is_available` | bool | `true` if harvestable (not depleted, not on cooldown) |
| `harvest_ticks` | int | Number of ticks to channel a single harvest |

Resource nodes deplete after `max_harvests` harvests, then enter a cooldown period before respawning. See `docs/terrains_resources.md` for full lifecycle details.

---

## Event Schema

```json
{
    "tick": 42,
    "category": "ATTACK",
    "message": "Entity 1 (hero) hits Entity 5 (goblin) for 12 CRIT!! damage [HP: 3/21]"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Tick when event occurred |
| `category` | str | Event type: `ATTACK`, `MOVE`, `REST`, `SPAWN`, `DEATH`, `LEVEL_UP`, `LOOT`, `USE_ITEM` |
| `message` | str | Human-readable event description |

---

## Error Responses

| Status | Description |
|--------|-------------|
| 503 | No snapshot available yet (simulation not started) |
| 500 | Internal server error (check server logs) |

---

## CORS & Static Files

- The API serves the frontend as static files from `frontend/` directory at `/`
- CORS is configured to allow all origins for development
- The frontend HTML is served at the root path `/`
