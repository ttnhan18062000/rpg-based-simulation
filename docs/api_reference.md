# API Reference

Technical documentation for the REST API endpoints, request/response schemas, and data contracts.

---

## Overview

The backend exposes a REST API via **FastAPI** under the `/api/v1` prefix. The frontend polls `/state` every ~80ms for dynamic data. Static data (`/map` grid + `/static` world data) is fetched once on mount.

**Primary files:** `src/api/routes/state.py`, `src/api/routes/map.py`, `src/api/schemas.py`, `src/api/app.py`

### Payload Optimization

The API is optimized to minimize recurring payload size:

| Endpoint | Frequency | Typical Size | Strategy |
|----------|-----------|--------------|----------|
| `/map` | Once | ~270 KB | RLE-compressed grid |
| `/static` | Once | ~47 KB | Buildings, regions, resources, chests |
| `/state` | Every 80ms | ~75 KB | Slim entities + optional full selected entity |

Pre-optimization `/state` was ~1.6 MB per poll. Current design achieves **~90% reduction**.

---

## Endpoints

### GET /api/v1/map

Fetch the static tile grid (called once at startup). The grid is **RLE-compressed** as a flat array.

**Response:**

```json
{
  "width": 512,
  "height": 512,
  "grid": [0, 5, 1, 3, 6, 120, ...]
}
```

`grid` is a flat RLE-encoded array: `[value, count, value, count, ...]`. The frontend decodes this into a 2D `number[][]` on load via `decodeRLE()`. Grid values correspond to `Material` enum (0=FLOOR, 1=WALL, ..., 22=GRAVEYARD). See `world_generation.md` for full list.

---

### GET /api/v1/state

Polled by the UI every ~80ms for dynamic simulation state. Returns **slim entities** for all alive entities, plus an optional **full entity** for the selected/inspected entity.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `since_tick` | int (optional) | Only return events newer than this tick |
| `selected` | int (optional) | Entity ID to include full details for (-1 or omitted = none) |

**Response: `WorldStateResponse`**

```json
{
  "tick": 405,
  "alive_count": 42,
  "entities": [ EntitySlimSchema, ... ],
  "selected_entity": EntitySchema | null,
  "events": [ EventSchema, ... ],
  "ground_items": [ GroundItemSchema, ... ]
}
```

> **Note:** Buildings, resource nodes, regions, and treasure chests are **not** included here. They are served by `/static` and fetched once.

---

### GET /api/v1/static

Static world data — fetched once after map load. Contains buildings, resource nodes, treasure chests, and regions.

**Response: `StaticDataResponse`**

```json
{
  "buildings": [ BuildingSchema, ... ],
  "resource_nodes": [ ResourceNodeSchema, ... ],
  "treasure_chests": [ TreasureChestSchema, ... ],
  "regions": [ RegionSchema, ... ]
}
```

---

### GET /api/v1/stats

Simulation-level statistics and counters.

**Response: `SimulationStats`**

```json
{
  "total_spawned": 150,
  "total_deaths": 108,
  "total_kills": 108,
  "running": true,
  "paused": false
}
```

---

### GET /api/v1/config

Returns the current `SimulationConfig` values as a flat JSON object.

---

### POST /api/v1/control/{action}

Control the simulation lifecycle.

**Actions:**

| Action | Description |
|--------|-------------|
| `start` | Begin simulation |
| `pause` | Pause the loop |
| `resume` | Resume from pause |
| `step` | Advance exactly one tick (while paused) |
| `reset` | Rebuild world from scratch |

**Response:** `{ "status": "ok" }`

---

### POST /api/v1/speed

Set the simulation speed (ticks per second).

**Request Body:**

```json
{ "tps": 10 }
```

**Response:** `{ "status": "ok", "tps": 10 }`

---

### POST /api/v1/clear_events

Clear all stored events from the event log.

**Response:** `{ "status": "ok" }`

---

## Metadata Endpoints

All metadata endpoints are under `/api/v1/metadata/`. They expose **core pydantic dataclasses** directly — the single source of truth used by both the game engine and the frontend. The frontend fetches these once at startup via `MetadataContext`.

### GET /api/v1/metadata/enums

All enum-like definitions used across the engine.

**Response: `EnumsResponse`**

```json
{
  "materials": [{ "id": 0, "name": "Floor", "walkable": true }, ...],
  "ai_states": [{ "id": 0, "name": "IDLE", "description": "..." }, ...],
  "tiers": [{ "id": 0, "name": "Normal" }, ...],
  "rarities": [{ "id": 0, "name": "common" }, ...],
  "item_types": [{ "id": 0, "name": "weapon" }, ...],
  "damage_types": [{ "id": 0, "name": "physical" }, ...],
  "elements": [{ "id": 0, "name": "none" }, ...],
  "entity_roles": [{ "id": 0, "name": "melee" }, ...],
  "factions": [{ "id": 0, "name": "Hero Guild" }, ...],
  "faction_relations": [{ "faction_a": 0, "faction_b": 1, "relation": "hostile" }, ...],
  "entity_kinds": [{ "kind": "hero", "faction": "Hero Guild" }, ...]
}
```

---

### GET /api/v1/metadata/items

All item templates. Serialized directly from core `ItemTemplate` pydantic dataclass.

**Response:**

```json
{
  "items": [
    {
      "item_id": "iron_sword",
      "name": "Iron Sword",
      "item_type": "weapon",
      "rarity": "common",
      "weight": 3.0,
      "atk_bonus": 4,
      "def_bonus": 0,
      "spd_bonus": 0,
      "max_hp_bonus": 0,
      "crit_rate_bonus": 0.0,
      "evasion_bonus": 0.0,
      "luck_bonus": 0,
      "matk_bonus": 0,
      "mdef_bonus": 0,
      "damage_type": "physical",
      "element": "none",
      "heal_amount": 0,
      "mana_restore": 0,
      "gold_value": 0,
      "sell_value": 0
    },
    ...
  ]
}
```

---

### GET /api/v1/metadata/classes

Class definitions, skills, breakthroughs, scaling grades, mastery tiers, and race skills.

**Response: `ClassesResponse`**

```json
{
  "classes": [
    {
      "id": "warrior",
      "name": "Warrior",
      "description": "...",
      "tier": 1,
      "role": "DPS",
      "attr_bonuses": { "str": 3, "agi": 0, "vit": 2, ... },
      "cap_bonuses": { "str": 10, "agi": 0, ... },
      "scaling": { "str": "S", "agi": "D", ... },
      "skill_ids": ["power_strike", "shield_wall", "battle_cry"],
      "breakthrough": {
        "from_class": "warrior",
        "to_class": "champion",
        "level_req": 10,
        "attr_req": "str",
        "attr_threshold": 30,
        "talent": "Unyielding",
        "bonuses": { ... },
        "cap_bonuses": { ... }
      }
    },
    ...
  ],
  "skills": [
    {
      "skill_id": "power_strike",
      "name": "Power Strike",
      "description": "A devastating blow dealing 1.8x damage.",
      "skill_type": "active",
      "target": "single_enemy",
      "class_req": "warrior",
      "level_req": 1,
      "gold_cost": 50,
      "cooldown": 4,
      "stamina_cost": 12,
      "power": 1.8,
      "duration": 0,
      "range": 1,
      "mastery_req": "",
      "mastery_threshold": 25.0,
      "atk_mod": 0.0, "def_mod": 0.0, "spd_mod": 0.0,
      "crit_mod": 0.0, "evasion_mod": 0.0, "hp_mod": 0.0
    },
    ...
  ],
  "race_skills": { "hero": ["basic_attack", "first_aid"], ... },
  "scaling_grades": [{ "grade": "E", "multiplier": 0.6 }, ...],
  "mastery_tiers": [{ "name": "Novice", "min_mastery": 0, ... }, ...],
  "skill_targets": [{ "id": 0, "name": "self" }, ...]
}
```

---

### GET /api/v1/metadata/traits

All personality trait definitions. Serialized directly from core `TraitDef` pydantic dataclass.

**Response:**

```json
{
  "traits": [
    {
      "trait_type": 0,
      "name": "Aggressive",
      "description": "Seeks combat eagerly, lower flee threshold.",
      "combat_utility": 0.3,
      "flee_utility": -0.2,
      "explore_utility": 0.0,
      "loot_utility": 0.0,
      "trade_utility": 0.0,
      "rest_utility": -0.1,
      "craft_utility": 0.0,
      "social_utility": 0.0,
      "atk_mult": 1.1,
      "def_mult": 0.95,
      ...
    },
    ...
  ]
}
```

---

### GET /api/v1/metadata/attributes

The 9 primary attribute definitions with effect descriptions.

**Response: `AttributesResponse`**

```json
{
  "attributes": [
    { "key": "str", "label": "STR", "description": "Physical ATK scaling (+2%/pt), carry weight." },
    { "key": "agi", "label": "AGI", "description": "SPD +0.4/pt, Crit +0.4%/pt, Evasion +0.3%/pt." },
    ...
  ]
}
```

---

### GET /api/v1/metadata/buildings

Building type names and descriptions.

**Response: `BuildingsResponse`**

```json
{
  "building_types": [
    { "building_type": "store", "name": "General Store", "description": "Buy and sell items..." },
    { "building_type": "blacksmith", "name": "Blacksmith", "description": "Learn recipes and craft..." },
    ...
  ]
}
```

---

### GET /api/v1/metadata/resources

Resource node types grouped by terrain.

**Response: `ResourcesResponse`**

```json
{
  "resource_types": [
    {
      "resource_type": "oak_tree",
      "name": "Oak Tree",
      "terrain": "Forest",
      "yields_item": "wood",
      "max_harvests": 3,
      "respawn_cooldown": 30,
      "harvest_ticks": 4
    },
    ...
  ]
}
```

---

### GET /api/v1/metadata/recipes

All crafting recipe definitions.

**Response: `RecipesResponse`**

```json
{
  "recipes": [
    {
      "recipe_id": "craft_steel_sword",
      "output_item": "steel_sword",
      "output_name": "Steel Sword",
      "gold_cost": 60,
      "materials": { "iron_ore": 2, "wood": 1 }
    },
    ...
  ]
}
```

---

## Schemas

### EntitySlimSchema

Minimal entity data sent for **all alive entities** in every `/state` poll. Used for map rendering.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique entity ID |
| `kind` | str | Entity type name |
| `x` / `y` | int | Grid position |
| `hp` / `max_hp` | int | Health |
| `state` | str | Current AI state name |
| `level` | int | Entity level |
| `tier` | int | Enemy difficulty tier |
| `faction` | str | Faction name |
| `weapon_range` | int | Attack range (for combat line rendering) |
| `combat_target_id` | int \| null | Current combat target |
| `loot_progress` | int | Loot channel progress |
| `loot_duration` | int | Loot channel total |

~200 bytes per entity in JSON.

### EntitySchema

Full entity data — only sent for the **selected/inspected entity** (via `?selected=<id>` on `/state`).

Includes all `EntitySlimSchema` fields plus:

| Field | Type | Description |
|-------|------|-------------|
| `atk` / `def_` / `spd` | int | Effective combat stats |
| `matk` / `mdef` | int | Effective magical stats |
| `base_atk` / `base_def` / `base_spd` | int | Raw base before equipment |
| `base_matk` / `base_mdef` | int | Raw base magical |
| `xp` / `xp_to_next` | int | Leveling progress |
| `gold` | int | Currency |
| `luck` | int | Luck stat |
| `crit_rate` | float | Critical hit chance |
| `evasion` | float | Dodge chance |
| `stamina` / `max_stamina` | int | Action resource |
| `weapon` / `armor` / `accessory` | str \| null | Equipped item IDs |
| `inventory_items` | str[] | Bag item IDs |
| `vision_range` | int | Perception radius |
| `terrain_memory` | dict\<str, int\> | Explored tiles (`"x,y"` → material) |
| `entity_memory` | EntityMemoryEntry[] | Last-seen entity data |
| `goals` | str[] | Current behavioral goal strings |
| `hero_class` | str | Class name (or "none") |
| `class_mastery` | float | 0.0–100.0 |
| `skills` | SkillSchema[] | Learned skills |
| `known_recipes` | str[] | Recipe IDs known |
| `craft_target` | str \| null | Current crafting goal |
| `traits` | int[] | Personality trait type IDs |
| `attributes` | AttributeSchema \| null | 9 primary attributes |
| `attribute_caps` | AttributeCapSchema \| null | Attribute growth limits |
| `active_effects` | EffectSchema[] | Active buffs/debuffs |
| `quests` | QuestSchema[] | Tracked quests |
| `home_storage_used` | int | Home storage items count |
| `home_storage_max` | int | Home storage capacity |
| `home_storage_level` | int | Home storage upgrade level |

### AttributeSchema

```json
{
  "str": 12, "agi": 8, "vit": 10,
  "int": 6, "spi": 5, "wis": 7,
  "end": 9, "per": 4, "cha": 3
}
```

### AttributeCapSchema

Same shape as `AttributeSchema` but representing caps.

### SkillSchema

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Skill name |
| `skill_type` | str | "active" or "passive" |
| `power` | float | Damage multiplier |
| `stamina_cost` | int | Stamina per use |
| `cooldown` | int | Base cooldown ticks |
| `cooldown_remaining` | int | Current cooldown |
| `mastery` | float | 0.0–100.0 |
| `times_used` | int | Total uses |
| `damage_type` | str | "physical" or "magical" |
| `element` | str | Element name |

### EffectSchema

| Field | Type | Description |
|-------|------|-------------|
| `effect_type` | str | Effect type name |
| `source` | str | Human-readable origin |
| `remaining_ticks` | int | Duration left |
| `atk_mult` / `def_mult` / `spd_mult` | float | Stat multipliers |
| `crit_mult` / `evasion_mult` | float | Crit/evasion multipliers |
| `hp_per_tick` | int | HP change per tick |

### QuestSchema

| Field | Type | Description |
|-------|------|-------------|
| `quest_id` | str | Unique ID |
| `quest_type` | str | "hunt", "explore", "gather" |
| `title` / `description` | str | Display text |
| `progress` | int | Current count |
| `target_count` | int | Required count |
| `gold_reward` / `xp_reward` | int | Rewards |
| `item_reward` | str \| null | Item reward |
| `completed` | bool | Done flag |

### EventSchema

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | When the event occurred |
| `category` | str | Event category (combat, loot, level, etc.) |
| `message` | str | Human-readable event text |

### GroundItemSchema

| Field | Type | Description |
|-------|------|-------------|
| `x` / `y` | int | Position |
| `items` | str[] | Item IDs at this position |

### BuildingSchema

| Field | Type | Description |
|-------|------|-------------|
| `building_id` | str | Unique ID |
| `name` | str | Display name |
| `x` / `y` | int | Position |
| `building_type` | str | "store", "blacksmith", "guild", "class_hall", "inn" |

### ResourceNodeSchema

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | int | Unique ID |
| `resource_type` | str | e.g. "herb_patch" |
| `name` | str | Display name |
| `x` / `y` | int | Position |
| `terrain` | int | Material value |
| `yields_item` | str | Item ID produced |
| `remaining` | int | Harvests left |
| `max_harvests` | int | Max when fully grown |
| `is_available` | bool | Can be harvested |
| `harvest_ticks` | int | Channel duration |

### TreasureChestSchema

| Field | Type | Description |
|-------|------|-------------|
| `chest_id` | int | Unique ID |
| `x` / `y` | int | Position |
| `tier` | int | Chest tier (1–3) |
| `looted` | bool | Currently looted |
| `guard_entity_id` | int \| null | Guard entity ID |

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid action, etc.) |
| 404 | Not found |
| 500 | Internal server error |

---

## CORS

CORS is enabled for all origins during development. In production, the frontend is served from the same origin (`frontend/dist/` at `/`).

---

## Static Files

The FastAPI backend mounts `frontend/dist/` as static files at `/` for production serving.
