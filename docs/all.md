# ai_system

# AI System

Technical documentation for the hybrid AI architecture, goal evaluation, state machine, state handlers, perception, memory, and personality traits.

---

## Overview

Entity AI uses a **hybrid architecture** combining **Utility AI** for goal evaluation with a **State Machine** for execution. The goal evaluator picks *what* to do; the state handler executes *how* to do it.

**Primary files:** `src/ai/brain.py`, `src/ai/goals/`, `src/ai/states.py`, `src/ai/perception.py`, `src/core/traits.py`

---

## 1. Hybrid Architecture

### Decision Flow

```
AIBrain.decide(ctx: AIContext) → (AIState, ActionProposal)
    │
    ├── Entity in DECISION state? (IDLE, WANDER, RESTING_IN_TOWN, GUARD_CAMP)
    │       │
    │       ▼
    │   GoalEvaluator.evaluate(ctx) → sorted GoalScore list
    │   GoalEvaluator.select(scores, rng) → winning GoalScore
    │       │
    │       ▼
    │   Transition to winner's target_state
    │
    └── Entity in EXECUTION state? (HUNT, COMBAT, FLEE, LOOTING, VISIT_*, HARVESTING, ALERT)
            │
            ▼
        STATE_HANDLERS[ai_state].handle(ctx) → (new_state, ActionProposal)
```

### AIContext

All AI logic receives an `AIContext` dataclass:

```python
@dataclass(slots=True)
class AIContext:
    actor: Entity
    snapshot: Snapshot
    config: SimulationConfig
    rng: DeterministicRNG
    faction_reg: FactionRegistry
```

---

## 2. Goal Evaluation (Utility AI)

### Plugin System (`src/ai/goals/`)

Each goal is a `GoalScorer` subclass with:
- `name` — unique goal identifier
- `target_state` — `AIState` to transition to
- `score(ctx)` — returns float utility score (0.0–1.0+)

Scorers are registered in `GOAL_REGISTRY` via `register_all_goals()` in `src/ai/goals/registry.py`.

### Selection

`GoalEvaluator.evaluate(ctx)` scores all registered goals and returns sorted `GoalScore` list. `GoalEvaluator.select(scores, rng)` picks the winner via weighted random from the top 3 scores.

### Built-in Goals (9)

| Goal | Scorer | Maps to | Key Factors |
|------|--------|---------|-------------|
| COMBAT | `CombatGoal` | HUNT | Enemy proximity, power comparison, HP ratio, traits |
| FLEE | `FleeGoal` | FLEE | HP ratio vs flee threshold (trait-modified), enemy presence |
| EXPLORE | `ExploreGoal` | WANDER | HP/stamina health, no enemies, trait curiosity |
| LOOT | `LootGoal` | LOOTING | Ground items nearby, inventory space (0.0 if bag full) |
| TRADE | `TradeGoal` | VISIT_SHOP | Sellable items, buying needs (+0.4 urgency when bag nearly full) |
| REST | `RestGoal` | RESTING_IN_TOWN | Low HP, low stamina |
| CRAFT | `CraftGoal` | VISIT_BLACKSMITH | Recipes, materials available |
| SOCIAL | `SocialGoal` | VISIT_GUILD | Intel needs, class hall needs |
| GUARD | `GuardGoal` | GUARD_CAMP | Non-hero, home territory proximity |

### Trait Influence

Each entity's traits add `UtilityBonus` values to goal scores. See section 7.

---

## 3. State Machine (18 States)

| State | Value | Description |
|-------|-------|-------------|
| IDLE | 0 | Waiting, re-evaluates goals |
| WANDER | 1 | Exploring, seeking targets |
| HUNT | 2 | Moving toward a target enemy |
| COMBAT | 3 | In melee, attacking |
| FLEE | 4 | Running from danger |
| RETURN_TO_TOWN | 5 | Navigating back to town |
| RESTING_IN_TOWN | 6 | Healing at town |
| RETURN_TO_CAMP | 7 | Enemy returning to camp |
| GUARD_CAMP | 8 | Patrolling camp radius |
| LOOTING | 9 | Picking up ground items |
| ALERT | 10 | Responding to territory intrusion |
| VISIT_SHOP | 11 | Buying/selling at store |
| VISIT_BLACKSMITH | 12 | Crafting at blacksmith |
| VISIT_GUILD | 13 | Getting intel at guild |
| HARVESTING | 14 | Channeling resource harvest |
| VISIT_CLASS_HALL | 15 | Learning skills, breakthroughs |
| VISIT_INN | 16 | Resting at inn |
| VISIT_HOME | 17 | Storing items at home |

Each state has a `StateHandler` subclass registered in `STATE_HANDLERS` dict.

---

## 4. State Handlers

### IdleHandler
- Re-evaluates goals via the `GoalEvaluator`
- Transitions to the winning goal's target state

### WanderHandler
- Moves toward unexplored tiles (frontier exploration)
- **Leash enforcement (enhance-04):** mobs with `leash_radius > 0` return to camp when beyond leash range
- Checks for nearby loot, resources, and enemies during movement
- Heroes with inventory space look for resources within 5 tiles → transition to HARVESTING
- Enemies in town retreat when below 60% HP or no target visible

### HuntHandler
- Moves toward target using **A* pathfinding** for distances > 2 tiles, greedy fallback for short distances
- Transitions to COMBAT when within weapon range (melee: Manhattan ≤ 1, ranged: ≤ weapon_range)
- **Diagonal deadlock prevention (bug-01):** when two mutually aggressive entities are at Manhattan distance 2, the higher-ID entity yields (rests) so the lower-ID entity can close the gap unimpeded
- **Leash enforcement (enhance-04):** abandons chase if distance from home > leash_radius × 1.5, or after `mob_chase_give_up_ticks` (20) without engaging
- Transitions to FLEE if HP drops below threshold
- Enemies abort hunts in town at 60% HP

### CombatHandler
- Proposes ATTACK or USE_SKILL actions against enemies within weapon range
- **Skill selection:** `best_ready_skill()` considers distance, range, and nearby enemy count (AoE preference)
- **Kiting:** Ranged entities (weapon_range ≥ 3) move away when adjacent and HP > 60%
- Uses potions when HP < 50%
- Transitions to FLEE if HP below flee threshold
- Enemies disengage in town at 50% HP (higher than normal 30%)
- On target death: re-evaluates for new targets or transitions

### FleeHandler
- Moves away from the nearest threat (maximizes distance)
- Heroes flee toward town; enemies flee toward camp
- Transitions to RETURN_TO_TOWN (heroes) or RETURN_TO_CAMP (enemies) when safe

### ReturnToTownHandler
- Navigates toward town center using greedy pathfinding
- Transitions to RESTING_IN_TOWN on arrival

### RestingInTownHandler
- Heals at `hero_heal_per_tick` rate until full HP
- After full heal, runs economy decision flow:
  1. Has sellable items → VISIT_SHOP
  2. Can afford upgrade → VISIT_SHOP
  3. Needs recipes or can craft → VISIT_BLACKSMITH
  4. Lacks camp intel or needs quest → VISIT_GUILD
  5. Needs class skills or breakthrough → VISIT_CLASS_HALL
  6. Nothing to do → WANDER

### ReturnToCampHandler
- Enemy navigates back to nearest camp
- Transitions to GUARD_CAMP on arrival

### GuardCampHandler
- Patrols within camp radius
- Engages intruders within vision_range / 2
- Re-evaluates goals periodically

### LootingHandler
- Moves toward nearest ground loot
- Channels loot pickup (`loot_progress` increments each tick)
- Proposes LOOT action when channel completes
- Interrupts: flee if low HP, engage if enemy within 3 tiles

### AlertHandler
- Triggered by territory intrusion
- Seeks and engages the intruder
- Returns to GUARD_CAMP or retreats if no enemy visible

### VisitShopHandler
- Walks to General Store
- Sells: gold pouches, excess materials, inferior equipment
- Buys: potions (if < 2), equipment upgrades, buff potions

### VisitBlacksmithHandler
- Walks to Blacksmith
- Learns recipes, picks best upgrade as craft target
- Crafts when materials + gold available

### VisitGuildHandler
- Walks to Adventurer's Guild
- Reveals camp locations and resource nodes (intel)
- Generates quests (if < 3 active)
- Provides material hints and terrain tips

### VisitClassHallHandler
- Walks to Class Hall
- Learns available skills (deducts gold)
- Attempts breakthrough if eligible

### VisitInnHandler
- Walks to Traveler's Inn
- Rapid HP/stamina recovery

### VisitHomeHandler
- Walks to hero's home position
- Upgrades storage if affordable
- Stores low-priority items: materials not needed for crafting, weaker equipment, excess consumables (keep 2)

### HarvestingHandler
- Finds nearest available resource node within 8 tiles
- Moves toward node, then channels harvest
- Proposes HARVEST action when channel completes
- Interrupts: flee if low HP, engage if enemy within 3 tiles

---

## 5. Perception (`src/ai/perception.py`)

### Methods

| Method | Description |
|--------|-------------|
| `nearest_enemy(actor, visible, faction_reg)` | Closest hostile entity (tie-break: lowest ID) |
| `highest_threat_enemy(actor, visible, faction_reg)` | Visible hostile with highest threat score; falls back to nearest |
| `nearest_ally(actor, visible, faction_reg)` | Closest allied entity |
| `ground_loot_nearby(actor, snapshot, radius)` | Nearest ground loot position |
| `is_on_enemy_territory(actor, snapshot, reg)` | True if on hostile tile |
| `is_on_home_territory(actor, snapshot, reg)` | True if on own faction's tile |

All perception is limited to the entity's `vision_range` (Manhattan distance).

### Threat-Based Targeting (epic-05 F3)

`AIContext.nearest_enemy()` dispatches based on faction:
- **Mobs** (non-HERO_GUILD) with threat entries → `highest_threat_enemy()`
- **Heroes** and mobs without threat data → `nearest_enemy()`

---

## 6. Memory System

### Terrain Memory

Each entity tracks which tiles it has explored in `terrain_memory: set[tuple[int, int]]`. Tiles within vision range are added each tick. Used for:
- Frontier exploration (WanderHandler seeks unexplored tiles)
- Fog-of-war overlay on the frontend
- Exploration progress tracking

### Entity Memory

Each entity tracks last-seen positions of other entities in `entity_memory: dict[int, ...]`. Updated each tick for entities within vision. Used for:
- Chasing enemies last seen at a position
- Ghost markers on the frontend overlay
- Territory awareness

---

## 7. Personality Traits (`src/core/traits.py`)

Rimworld-style discrete personality traits assigned at spawn.

### Assignment

- Each entity gets **2–4 traits** via `assign_traits()`
- Incompatible pairs enforced (e.g. AGGRESSIVE + CAUTIOUS cannot coexist)
- Race-biased selection: certain races more likely to get specific traits

### Trait Categories (20 traits)

| Category | Traits |
|----------|--------|
| **Combat** | Aggressive, Cautious, Brave, Cowardly, Bloodthirsty |
| **Social** | Greedy, Generous, Charismatic, Loner |
| **Work Ethic** | Diligent, Lazy, Curious |
| **Combat Style** | Berserker, Tactical, Resilient |
| **Magic** | Arcane Gifted, Spirit Touched, Elementalist |
| **Perception** | Keen-Eyed, Oblivious |

### Trait Effects (Typed Dataclasses)

Traits modify two things via typed dataclasses (no string-keyed dicts):

1. **`UtilityBonus`** — additive bonuses to goal evaluation
   - Fields: `.combat`, `.flee`, `.explore`, `.loot`, `.trade`, `.rest`, `.craft`, `.social`

2. **`TraitStatModifiers`** — multiplicative/additive passive stat modifiers
   - Fields: `.atk_mult`, `.def_mult`, `.matk_mult`, `.mdef_mult`, `.crit_bonus`, `.evasion_bonus`, `.vision_bonus`, `.hp_regen_mult`, `.interaction_speed_mult`, `.flee_threshold_mod`

### Aggregation

```python
bonus = aggregate_trait_utility(entity.traits)   # → UtilityBonus
mods = aggregate_trait_stats(entity.traits)       # → TraitStatModifiers
```

---

## 8. A* Pathfinding (epic-09)

**Primary file:** `src/ai/pathfinding.py`

### Pathfinder Class

`Pathfinder(grid, max_nodes=200)` computes optimal paths using A* with Manhattan heuristic.

| Method | Returns | Description |
|--------|---------|-------------|
| `find_path(start, goal, occupied)` | `list[Vector2] \| None` | Full path excluding start, including goal |
| `next_step(start, goal, occupied)` | `Vector2 \| None` | First step of the path |

### Terrain Cost Weights

`TERRAIN_MOVE_COST` registry determines step cost per tile type:

| Tile | Cost | Effect |
|------|------|--------|
| ROAD / BRIDGE | 0.7 | Preferred routes |
| GRASSLAND / FARMLAND | 0.9 | Open terrain, fast |
| FLOOR / TOWN / SANCTUARY | 1.0 | Baseline |
| CAVE / GRAVEYARD | 1.1 | Slightly slower |
| DESERT | 1.2 | Arid terrain |
| FOREST / VOLCANIC | 1.3 | Dense/rough terrain |
| MOUNTAIN / SNOW | 1.4 | Rocky/icy terrain |
| SWAMP / SHALLOW_WATER | 1.5 | Difficult terrain |
| JUNGLE | 1.6 | Very dense terrain |

### Integration

`propose_move_toward()` in `src/ai/states.py`:
- **Distance ≤ 2:** greedy movement (fast, no pathfinding overhead)
- **Distance > 2:** A* pathfinding with terrain cost awareness
- **A* fails:** falls back to greedy movement with perpendicular fallback

### Path Caching

Entity fields `cached_path` and `cached_path_target` store the last computed A* path. Cache is reused when the target hasn't changed and the entity is at the expected position.

---

## 9. Thread Safety

- AI logic runs in worker threads, reading only immutable `Snapshot` data
- Workers produce `ActionProposal` objects pushed to a thread-safe `ActionQueue`
- No shared mutable state between AI workers
- Entity memory is updated only by the `WorldLoop` thread after actions are applied

---

# all



---

# api_reference

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

---

# architecture

# System Architecture

Technical documentation for the runtime architecture, concurrency model, and project structure.

---

## Overview

The RPG simulation engine is a **deterministic concurrent system** that simulates a living 2D world with autonomous entities. The core principle: heavy AI logic runs in parallel threads while world mutation is strictly single-threaded.

**Key guarantees:**

1. **Single-Writer / Multi-Reader** — Only `WorldLoop` mutates `WorldState`; workers read immutable snapshots
2. **Absolute Determinism** — Given a `WorldSeed`, the simulation reproduces the exact same state on any machine
3. **Intent vs Effect** — Workers produce `ActionProposal` (intent); `WorldLoop` resolves and applies effects
4. **Atomic Ticks** — All actions for tick N are resolved before tick N+1 begins

**Primary files:** `src/engine/world_loop.py`, `src/core/world_state.py`, `src/core/snapshot.py`, `src/api/engine_manager.py`

---

## Concurrency Model

### Thread Layout

| Thread | Role | Reads | Writes |
|--------|------|-------|--------|
| **Main** (uvicorn) | HTTP request handling | `latest_snapshot`, `EventLog` | Control signals |
| **Engine** (`WorldLoop`) | Tick cycle, mutation | `WorldState` | `WorldState`, `Snapshot` |
| **Workers** (ThreadPool) | AI computation | `Snapshot` (immutable) | `ActionQueue` (thread-safe) |

### Data Flow

```
WorldLoop ──1. creates──▶ Snapshot (immutable)
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                Worker 1   Worker 2   Worker 3
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                     ActionQueue (thread-safe)
                              │
                    ◀─2. consumed by── WorldLoop
                              │
                    3. mutates ──▶ WorldState
```

Workers never see partial updates. The `ActionQueue` is the only shared mutable structure between workers and the engine thread.

---

## Tick Cycle (4 Phases)

Each tick in `WorldLoop._step()` executes:

### Phase 1: Scheduling

- Identify entities whose `next_act_at <= current_tick`
- Generators execute immediately (spawn actions)
- Characters are dispatched to the worker pool with an immutable `Snapshot`

### Phase 2: Wait & Collect

- Workers compute `ActionProposal` from the snapshot and push to `ActionQueue`
- Hard timeout (`worker_timeout_seconds`, default 2s) prevents engine stalls — late entities miss their turn

### Phase 3: Conflict Resolution & Application

- Sort proposals deterministically (by `next_act_at`, then `entity_id`)
- Validate each proposal (bounds, adjacency, alive checks)
- Apply valid actions to `WorldState` (move, attack, loot, harvest, use_skill, use_item)
- Reject invalid actions with logged reasons

### Phase 4: Cleanup & Effects

- Remove dead entities, drop loot
- Process territory effects (debuffs, alerts, aura damage)
- Tick status effects (decrement durations, apply hp_per_tick, prune expired)
- Tick resource node cooldowns
- Check level-ups (stat growth + attribute gains)
- Regenerate stamina, tick skill cooldowns
- Update entity memory (terrain + entity)
- Tick quests (EXPLORE completion, pruning)
- Update entity goals (display text)
- Advance tick counter

---

## Core Data Structures

### WorldState (Mutable, Private)

The authoritative "truth". Never exposed directly to workers.

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Current simulation tick |
| `entities` | dict[int, Entity] | All living entities by ID |
| `grid` | Grid | 2D tile grid |
| `ground_items` | dict[tuple, list[str]] | Dropped loot by position |
| `buildings` | list[Building] | Town buildings |
| `camps` | list[Vector2] | Camp center positions |
| `resource_nodes` | dict[int, ResourceNode] | Harvestable nodes by ID |
| `treasure_chests` | dict[int, TreasureChest] | Lootable chests by ID |

### Snapshot (Immutable, Public)

Point-in-time read-only view for workers and the API layer. Created at the start of each tick.

Uses `MappingProxyType` for entity dict and tuples for lists to prevent mutation. Contains only what AI needs: entities, grid, camps, buildings, resource nodes, treasure chests.

### ActionProposal

```python
@dataclass
class ActionProposal:
    actor_id: int
    verb: ActionType      # MOVE, ATTACK, REST, USE_ITEM, LOOT, HARVEST, USE_SKILL
    target: Any           # Coordinates, EntityID, or item ID
    reason: str           # Debug string
```

---

## Deterministic RNG

All randomness uses `DeterministicRNG` (`src/systems/rng.py`) with **domain-separated hashing**.

**Formula:** `value = hash64(world_seed, domain, entity_id, tick)`

### RNG Domains

| Domain | Value | Usage |
|--------|-------|-------|
| COMBAT | 0 | Damage variance, crit rolls, evasion rolls |
| LOOT | 1 | Item drops, chest loot |
| AI_DECISION | 2 | Goal tie-breaking |
| SPAWN | 3 | Entity stat rolls, tier selection |
| WEATHER | 4 | (Reserved) |
| LEVEL_UP | 5 | Level-up variance |
| ITEM | 6 | Item-related rolls |
| HARVEST | 7 | Harvest-related rolls |
| MAP_GEN | 8 | World generation |

**Key benefit:** Adding a new feature with a new domain does not change existing RNG sequences.

---

## API Layer

The FastAPI backend (`src/api/`) bridges the simulation to HTTP clients.

### EngineManager

Singleton wrapper that:
1. Builds the world (grid, zones, buildings, entities) during startup
2. Runs `WorldLoop` in a background daemon thread
3. Holds a thread-safe `latest_snapshot` reference (atomic swap after each tick)
4. Manages an unbounded `EventLog` for simulation events
5. Exposes control signals (start, pause, resume, step, reset)

### Lifespan

```
FastAPI startup → EngineManager._build() → WorldLoop thread starts
FastAPI shutdown → WorldLoop thread joins
```

### Endpoints

All under `/api/v1/`. See `api_reference.md` for full specification.

| Group | Routes | Purpose |
|-------|--------|---------|
| **State** | `/state`, `/stats` | Live simulation state (polled every ~80ms). `/state` returns slim entities + optional full selected entity |
| **Static** | `/static` | Buildings, regions, resources, chests (fetched once) |
| **Map** | `/map` | RLE-compressed tile grid (fetched once) |
| **Control** | `/control/{action}`, `/speed` | Simulation lifecycle |
| **Config** | `/config` | Read-only simulation config |
| **Metadata** | `/metadata/*` (8 endpoints) | Game definitions — serialized core pydantic dataclasses |

### Shared Schema Architecture

Core game definitions (`ItemTemplate`, `SkillDef`, `ClassDef`, `BreakthroughDef`, `TraitDef`) are **pydantic dataclasses** that serve as the single source of truth for both the engine and the API:

- **Runtime:** Fields like `item_type: ItemType` remain `IntEnum` for fast game logic comparisons
- **Serialization:** `Annotated[EnumType, PlainSerializer(...)]` converts enums to lowercase strings in JSON
- **No duplication:** `metadata.py` uses `TypeAdapter(CoreModel).dump_python()` to serialize core objects directly
- **Mutable types stay stdlib:** `SkillInstance`, `TreasureChest`, `Building` use standard `dataclasses.dataclass`

See `docs/design_patterns.md` §7 for full details.

### API Documentation

Three views available:
- **In-app API Docs** — custom React page in the frontend (fetches `/openapi.json`)
- **Swagger UI** — `/docs`
- **ReDoc** — `/redoc`

---

## Event System

`EventLog` (`src/utils/event_log.py`) stores `SimEvent` records. Thread-safe via a simple lock.

- **Unbounded** — all events kept since simulation start
- **Writers** append batches (once per tick)
- **Readers** snapshot slices (non-blocking copies)
- **Manual clear** via `POST /api/v1/clear_events`

---

## Configuration

`SimulationConfig` (`src/config.py`) is a frozen dataclass with all tunable parameters. Key defaults:

| Category | Parameter | Default |
|----------|-----------|---------|
| World | `grid_width` / `grid_height` | 512 × 512 |
| World | `world_seed` | 42 |
| Timing | `max_ticks` | 1000 |
| Workers | `num_workers` | 4 |
| Workers | `worker_timeout_seconds` | 2.0 |
| Entities | `initial_entity_count` | 40 |
| Entities | `generator_max_entities` | 200 |
| Town | `town_center_x/y` | 256, 256 |
| Town | `town_radius` | 6 |
| Camps | `camp_min_distance` | 60 |
| AI | `vision_range` | 6 |
| Combat | `max_level` | 20 |

Full parameter list in `src/config.py`.

---

## Project File Map

```
src/
├── __main__.py                  # CLI entry point
├── config.py                    # SimulationConfig dataclass
├── core/                        # Data models (pydantic shared schemas)
│   ├── enums.py                 # ActionType, AIState, Material, Domain, etc.
│   ├── grid.py                  # 2D tile grid with walkability + LoS (Bresenham)
│   ├── models.py                # Entity dataclass
│   ├── world_state.py           # Mutable world state
│   ├── snapshot.py              # Immutable snapshot for workers
│   ├── items.py                 # ItemTemplate (pydantic), Inventory, ITEM_REGISTRY
│   ├── classes.py               # ClassDef, SkillDef, BreakthroughDef (pydantic)
│   ├── traits.py                # TraitDef (pydantic), UtilityBonus, TraitRegistry
│   ├── buildings.py             # Building, Recipe, shop config
│   ├── faction.py               # Faction, FactionRelation, FactionRegistry (10 factions)
│   ├── effects.py               # StatusEffect, EffectType
│   ├── attributes.py            # Attributes, derived stats, training
│   ├── quests.py                # Quest, QuestType, templates
│   ├── resource_nodes.py        # ResourceNode, TERRAIN_RESOURCES (8 biomes)
│   ├── regions.py               # Region, Location dataclasses, name tables, difficulty config
│   └── entity_builder.py        # Fluent builder for Entity construction
├── engine/
│   ├── world_loop.py            # 4-phase tick cycle (the engine core)
│   ├── action_queue.py          # Thread-safe MPSC queue
│   ├── worker_pool.py           # ThreadPoolExecutor for AI workers
│   └── conflict_resolver.py     # Deterministic conflict resolution
├── actions/
│   ├── base.py                  # ActionProposal dataclass
│   ├── combat.py                # CombatAction (damage pipeline, AoE, ranged, cover)
│   ├── damage.py                # DamageCalculator strategy pattern
│   ├── move.py                  # MoveAction (validate + apply)
│   └── rest.py                  # RestAction
├── ai/
│   ├── brain.py                 # AIBrain (hybrid: goals + state machine)
│   ├── states.py                # StateHandler subclasses (18 states)
│   ├── perception.py            # Vision, memory, faction-aware queries
│   ├── pathfinding.py           # A* pathfinder, terrain costs, path caching
│   ├── goal_evaluator.py        # Backward-compat shim
│   └── goals/
│       ├── base.py              # GoalScorer ABC, GoalEvaluator, registry
│       ├── scorers.py           # 9 built-in goal scorers
│       └── registry.py          # register_all_goals()
├── systems/
│   ├── rng.py                   # DeterministicRNG (domain-separated hashing)
│   ├── spatial_hash.py          # O(1) spatial neighbor lookups
│   ├── generator.py             # EntityGenerator (spawn, spawn_race)
│   └── terrain_detail.py        # Intra-region terrain features (per-biome)
├── utils/
│   ├── event_log.py             # Ring-buffer EventLog (10k cap)
│   ├── logging.py               # Structured logging setup
│   └── replay.py                # JSON replay recorder
└── api/
    ├── app.py                   # FastAPI app factory (OpenAPI tags, CORS)
    ├── engine_manager.py        # World builder + background thread manager
    ├── dependencies.py          # FastAPI dependency injection
    ├── schemas.py               # Pydantic response models (EntitySlim, RLE map)
    └── routes/
        ├── __init__.py          # Router registration (api_router)
        ├── state.py             # GET /state, /stats, /static
        ├── map.py               # GET /map (RLE-compressed)
        ├── control.py           # POST /control/{action}, /speed
        ├── config.py            # GET /config
        └── metadata.py          # GET /metadata/* (8 endpoints, uses core schemas)

frontend/
├── src/
│   ├── App.tsx                  # Root layout + page toggle (Simulation | API Docs)
│   ├── main.tsx                 # Entry point (wraps App with MetadataProvider)
│   ├── types/
│   │   ├── api.ts               # Simulation state types
│   │   └── metadata.ts          # Metadata types (mirrors core pydantic schemas)
│   ├── contexts/
│   │   └── MetadataContext.tsx   # MetadataProvider + useMetadata() hook
│   ├── constants/
│   │   └── colors.ts            # Visual-only: colors, icons, cell size
│   ├── hooks/
│   │   ├── useSimulation.ts     # API polling + state management
│   │   └── useCanvas.ts         # Canvas rendering
│   └── components/
│       ├── Header.tsx           # Status bar + Simulation/API Docs nav toggle
│       ├── ApiDocsPage.tsx      # Interactive API docs (OpenAPI explorer + Try It)
│       ├── GameCanvas.tsx       # 3-layer canvas + minimap
│       ├── Sidebar.tsx          # Tab container
│       ├── ControlPanel.tsx     # Simulation controls
│       ├── InspectPanel.tsx     # Entity inspector (6 tabs, uses useMetadata)
│       ├── BuildingPanel.tsx    # Building info (uses useMetadata)
│       ├── ClassHallPanel.tsx   # Class browser (uses useMetadata)
│       ├── LootPanel.tsx        # Ground item detail (uses useMetadata)
│       ├── EventLog.tsx         # Event history with clear button
│       ├── EntityList.tsx       # Sorted entity list
│       └── Legend.tsx           # Tile/entity color legend
└── ...
```

---

# poposal

This is a comprehensive technical proposal that synthesizes the architectural core of **v1** with the advanced deterministic, AI, and optimization strategies of **v2**.

This document is designed to serve as a **specification for implementation**.

---

# Technical Specification: Deterministic Concurrent RPG Engine

**Version:** 2.0 (Merged & Revised)
**Status:** Approved for Implementation

---

## 1. Executive Summary

The goal is to engineer a high-fidelity **2D RPG simulation** that balances complex entity behavior with absolute architectural strictness. The system simulates a living world containing autonomous agents (NPCs), generators, and environmental rules.

**Key Technical Differentiators:**
1.  **Concurrency without Race Conditions:** Heavy AI logic runs in parallel threads; world mutation is serialized and single-threaded.
2.  **Absolute Determinism:** Given a `WorldSeed` and `InputLog`, the simulation will reproduce the exact same state, byte-for-byte, on any machine.
3.  **Observability:** The split between "Intent" (AI) and "Result" (World) allows for deep debugging and replayability.

---

## 2. Architectural Axioms (The Hard Rules)

These constraints are non-negotiable. Breaking them breaks the engine.

1.  **Single-Writer / Multi-Reader:**
    *   Only the `WorldLoop` thread may mutate the `WorldState`.
    *   Worker threads (AI) only read **Immutable Snapshots**.
2.  **Intent vs. Effect:**
    *   Workers produce **Intent** (e.g., `ActionProposal: Move(North)`).
    *   The World produces **Effect** (e.g., `Entity moves to (x, y-1)` OR `Blocked by Wall`).
3.  **Deterministic Randomness:**
    *   `random()` is banned in logic code.
    *   All entropy is derived from hashed seeds keyed by `(Domain, EntityID, Tick)`.
4.  **Atomic Ticks:**
    *   Time advances in discrete steps (ticks). All actions scheduled for `Tick N` are resolved before `Tick N+1` begins.

---

## 3. High-Level Architecture

```mermaid
graph TD
    subgraph "Parallel Worker Pool"
        W1[Worker Thread 1]
        W2[Worker Thread 2]
        W3[Worker Thread 3]
    end

    subgraph "Shared Memory"
        Q[Action Queue (Thread-Safe)]
        S[Immutable Snapshot (Read-Only)]
    end

    subgraph "Authoritative Core"
        WL[WorldLoop (Single Thread)]
        WS[Mutable World State]
        RNG[Deterministic Seed Generator]
    end

    WL -- 1. Creates --> S
    S -.-> W1 & W2 & W3
    W1 & W2 & W3 -- 2. Compute Intent --> Q
    Q -- 3. Consumed by --> WL
    WL -- 4. Mutates --> WS
    RNG -.-> WL
```

---

## 4. The Data Model

### 4.1 World State (Mutable, Private)
The "Truth" acts as a database. It is never exposed directly to workers.

```python
class WorldState:
    tick: int
    entities: Dict[int, Entity]
    map: Grid[Material]
    spatial_index: SpatialHash  # Optimization for neighbor lookups
    
    # Global RNG Configuration
    seed: int
```

### 4.2 The Entity
Entities are strictly identifiers with attached state components.

```python
@dataclass
class Entity:
    id: int             # Unique, Monotonic, Never Reused
    kind: str           # "goblin", "generator", "hero"
    pos: Vector2        # (x, y)
    stats: Stats        # HP, ATK, SPD, Level
    state: AIState      # "IDLE", "COMBAT", "FLEEING"
    next_act_at: float  # The absolute time this entity can act again
```

### 4.3 The Immutable Snapshot (Public)
To prevent locking, the WorldLoop generates a "View" of the world.
*   **Optimization:** Uses `MappingProxyType` or Copy-on-Write to avoid deep copying the whole world every tick.
*   **Scope:** Contains only what is necessary for AI (Map, Visible Entities).

---

## 5. The WorldLoop (Engine Core)

The `WorldLoop` is the heartbeat. It does not "sleep" on individual entities; it manages a priority queue of events.

### 5.1 The Loop Cycle
1.  **Phase 1: Scheduling**
    *   Identify entities whose `next_act_at <= current_time`.
    *   If Entity is a `Generator`: Immediate execution (Spawn).
    *   If Entity is a `Character`: Dispatch to **Worker Pool**.
2.  **Phase 2: Wait & Collect**
    *   Wait for workers to return `ActionProposals`.
    *   *Hard Timeout:* If a worker hangs, the entity misses its turn (prevents engine stall).
3.  **Phase 3: Conflict Resolution & Application**
    *   Sort actions deterministically (see Section 7).
    *   Apply valid actions to `WorldState`.
    *   Reject invalid actions (log reason).
4.  **Phase 4: Cleanup & Advancement**
    *   Remove dead entities.
    *   Update Spatial Index.
    *   Advance `current_time` to the next scheduled event.

---

## 6. The Intelligence Layer (AI)

AI logic is stateless. It receives a Snapshot and outputs a Proposal.

### 6.1 State Machine + Utility Scoring
Instead of simple if/else, AI uses a tiered approach:
1.  **State Check:** (e.g., Am I low HP? $\to$ Switch to `FLEE`).
2.  **Utility Scoring:** Score all possible actions.
    *   `Score(MoveAway) = Distance * SafetyWeight`
    *   `Score(Attack) = Damage * AggressionWeight`
3.  **Tie-Breaking:** If scores are equal, prefer the action with the lowest internal enum ID.

### 6.2 Perception
AI is not omniscient. The Worker calculates:
*   **Vision:** Raycast or Manhattan distance check against the Snapshot.
*   **Memory:** If the entity saw a player 5 ticks ago, it remembers the location (stored in `AIState`), even if the player is now hidden.

### 6.3 Output: Action Proposal
```python
@dataclass
class ActionProposal:
    actor_id: int
    verb: ActionType    # MOVE, ATTACK, REST
    target: Any         # Coordinates or EntityID
    reason: str         # For debugging ("Fleeing low HP")
```

---

## 7. Determinism & Randomness (The RNG Model)

To guarantee replayability, we implement **Domain-Separated Hashing**.

### 7.1 The Golden Rule
**The outcome of Tick `T` depends ONLY on WorldSeed + State at `T-1`.** It implies that thread scheduling order must strictly **not** matter.

### 7.2 RNG Domains
We do not use a single `random` object. We use a hashing function to generate pseudo-random numbers on the fly.

**Formula:**
`RNG_Value = Hash(WorldSeed, Domain, EntityID, Tick)`

**Domains:**
*   `COMBAT`: Hit chance, Crit chance, Damage variance.
*   `LOOT`: Item drops.
*   `AI_DECISION`: Choosing between two equal-score tiles.
*   `SPAWN`: Stats of newly generated monsters.

**Example Implementation:**
```python
def get_combat_roll(attacker_id, tick):
    # Returns float 0.0 to 1.0
    return xxhash64(seed + "COMBAT" + attacker_id + tick) / MAX_UINT64
```
*Benefits:* If we add a new feature (e.g., Weather) using a `WEATHER` domain, it will not change the combat rolls of existing replays.

---

## 8. Conflict Resolution Policies

When parallel workers submit conflicting intents, the WorldLoop arbitrates deterministically.

### 8.1 Movement Conflicts (The "Doorway Problem")
*Scenario:* Entity A and Entity B both try to move to $(5, 5)$ in the same tick.
*   **Policy:** The Entity with the **earliest** `next_act_at` wins.
*   **Tie-Breaker:** If times are equal, the **lowest EntityID** wins.
*   **Result:** Winner moves. Loser stays put (or performs a "Wait" action) and is rescheduled slightly later.

### 8.2 Combat Conflicts
*Scenario:* A and B both attack C. C dies from A's hit.
*   **Policy:** Actions are processed sequentially based on initiative (Speed).
*   **Result:** A kills C. B's attack validates against C (who is now dead), fails validation, and converts to a "Whiff" or "Look confused" action.

---

## 9. Optimization Strategy

### 9.1 Spatial Hashing
Instead of iterating 1000 entities to find "nearest enemy":
*   The World maintains a dictionary: `Map<(int, int), List[EntityID]>`.
*   Workers query this map (via Snapshot) for O(1) adjacency checks.

### 9.2 Data-Oriented Design (Future Proofing)
While Python classes are used for the prototype, the design is compatible with **ECS (Entity Component System)** arrays (using `numpy` or `structs`) if performance becomes a bottleneck > 10,000 entities.

---

## 10. Roadmap

### Phase 1: The Skeleton
*   Implement `WorldLoop`, `ActionQueue`, and basic `Entity`.
*   Implement `Snapshot` generation.
*   **Goal:** A dot moving on a grid with deterministic logs.

### Phase 2: The Brain
*   Implement Worker ThreadPool.
*   Implement `MoveAction` and `RestAction`.
*   Implement Domain-RNG.
*   **Goal:** Multiple dots wandering randomly but reproducibly.

### Phase 3: The Conflict
*   Implement `CombatAction` and `Stats`.
*   Implement Conflict Resolution (Resolution Policy).
*   **Goal:** Entities kill each other until one remains. Replay file works.

### Phase 4: The Simulation
*   Implement Generators and AI State Machines (Flee/Hunt).
*   Add Spatial Hashing.
*   **Goal:** Self-sustaining ecosystem.

---

# visual_proposal

> **Note:** This is the original design proposal. The backend API was implemented as described. The frontend was later redesigned from a single `index.html` to a **React 19 + TypeScript + Vite + Tailwind CSS v4** SPA — see [docs/frontend.md](frontend.md) for the current frontend architecture.

This is a technical proposal to wrap your existing deterministic RPG engine with a **FastAPI** layer.

The core challenge here is **Concurrency integration**. Your current engine likely runs a blocking `while` loop. To serve a Web API, we must move the simulation loop to a **background thread** while the main thread handles HTTP requests, utilizing a thread-safe "latest snapshot" buffer for the API to read.

---

# Proposal: Real-Time Visualization via REST API

## 1. System Architecture Update

We will transform the application from a CLI tool into a Web Service.

**Current:** `Main Process -> WorldLoop (Blocking)`
**New:** `Main Process (FastAPI) -> Background Thread (WorldLoop)`

### Modified Directory Structure
We add an `api/` directory and update `src/__main__.py`.

```text
src/
├── api/                     # NEW: Web Server Layer
│   ├── app.py               # FastAPI app instance
│   ├── routes.py            # Endpoints (GET /state, POST /control)
│   ├── schemas.py           # Pydantic models for JSON response
│   └── engine_manager.py    # Singleton wrapper managing the WorldLoop thread
├── __main__.py              # UPDATED: Starts uvicorn server
└── ... (existing core/engine files remain generic)
```

---

## 2. The Integration Strategy (EngineManager)

We cannot have the API query the `WorldState` directly while the `WorldLoop` is writing to it (violates Single-Writer principle).

**Solution: Atomic Reference Swapping**
1.  The `WorldLoop` creates an immutable `Snapshot` at the end of every tick (as it already does for workers).
2.  The `EngineManager` holds a thread-safe reference to `latest_snapshot`.
3.  The API reads from `latest_snapshot`.

### The `EngineManager` Class
```python
import threading
from src.engine.world_loop import WorldLoop

class EngineManager:
    def __init__(self, config):
        self.loop = WorldLoop(config)
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.running = False
        self.latest_snapshot = None # The atomic buffer
        self.lock = threading.Lock()

    def _run_loop(self):
        """The background simulation loop."""
        while self.running:
            # 1. Tick the engine
            self.loop.tick()
            
            # 2. Update the shared buffer safely
            new_snap = self.loop.create_snapshot()
            with self.lock:
                self.latest_snapshot = new_snap
            
            # 3. Rate limiting (optional, to not burn 100% CPU)
            time.sleep(0.05) 

    def start(self):
        self.running = True
        self.thread.start()
```

---

## 3. REST API Specification

We need endpoints for **Static Data** (Map), **Dynamic Data** (Entities), and **Controls**.

### 3.1 Data Endpoints

**`GET /api/v1/map`**
*   **Purpose:** Fetch the static grid (walls, water, grass) once at startup.
*   **Response:**
    ```json
    {
      "width": 100,
      "height": 100,
      "grid": [ [1, 1, 0...], ... ] // 0=Grass, 1=Wall
    }
    ```

**`GET /api/v1/state`**
*   **Purpose:** Polled by the UI (e.g., every 100ms) to get moving parts.
*   **Response:**
    ```json
    {
      "tick": 405,
      "entities": [
        { "id": 101, "kind": "hero", "x": 10, "y": 15, "state": "COMBAT", "hp": 80 },
        { "id": 102, "kind": "goblin", "x": 11, "y": 15, "state": "COMBAT", "hp": 20 }
      ],
      "events": [ "Combat: Hero hit Goblin for 12 dmg" ]
    }
    ```

### 3.2 Control Endpoints

**`POST /api/v1/control/{action}`**
*   **Actions:** `start`, `pause`, `resume`, `step`, `reset`.
*   **Purpose:** debugging and playback control.

---

## 4. Frontend Visualization (The 2D Grid)

Since the map might be large (e.g., 50x50 or 100x100), DOM manipulation (creating 10,000 `<div>`s) is too slow.

**Recommendation: HTML5 Canvas**

### Concept
1.  **Layer 1 (Background Canvas):** Draws the `GET /map` data once.
2.  **Layer 2 (Entity Canvas):** Cleared and redrawn every time `GET /state` returns new data.

### Frontend Logic (Pseudocode)
```javascript
async function gameLoop() {
  // 1. Fetch State
  const state = await fetch('/api/v1/state');
  
  // 2. Clear Entity Canvas
  ctx.clearRect(0, 0, width, height);
  
  // 3. Draw Entities
  state.entities.forEach(ent => {
    // Interpolate position for smoothness if needed
    drawSprite(ent.kind, ent.x, ent.y);
    drawHealthBar(ent.x, ent.y, ent.hp);
  });
  
  // 4. Update UI Stats
  document.getElementById('tick-counter').innerText = state.tick;
  
  // 5. Schedule next frame
  requestAnimationFrame(gameLoop);
}
```

---

## 5. Implementation Roadmap

### Phase 1: Serialization (Backend)
*   Update `Snapshot` and `Entity` classes to have a `to_dict()` or Pydantic `model_dump()` method.
*   Ensure Enums (ActionType, AIState) serialize to strings, not Python objects.

### Phase 2: The Manager (Backend)
*   Create `api/engine_manager.py`.
*   Implement the background thread logic.
*   Ensure the `WorldLoop` can be paused/unpaused cleanly.

### Phase 3: FastAPI Setup (Backend)
*   Install FastAPI: `pip install fastapi uvicorn`.
*   Create routes that access the `EngineManager` singleton.
*   Enable CORS (Cross-Origin Resource Sharing) so a frontend hosted on a different port can talk to it.

### Phase 4: Basic UI (Frontend)
*   Create a simple `index.html`.
*   Use `fetch()` to grab JSON.
*   Render a simple HTML Table first to verify data, then upgrade to Canvas.

---

## 6. Example Code Snippets

### `src/api/schemas.py` (Pydantic)
```python
from pydantic import BaseModel
from typing import List, Optional

class EntitySchema(BaseModel):
    id: int
    kind: str
    x: int
    y: int
    hp: int
    state: str

class WorldStateResponse(BaseModel):
    tick: int
    entities: List[EntitySchema]
```

### `src/api/app.py`
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.api.routes import router

# Global singleton
engine_mgr = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_mgr
    config = SimulationConfig(seed=42)
    engine_mgr = EngineManager(config)
    engine_mgr.start() # Starts the background thread
    yield
    engine_mgr.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(router)
```

## 7. Performance Considerations

1.  **Payload Size:** If you have 10,000 entities, sending the full list every 100ms is heavy.
    *   *Optimization:* Implement a `since_tick` parameter. `GET /state?since=500`. The backend only sends entities that changed since tick 500.
2.  **Visual Smoothness:** The simulation might run at 10 ticks/sec, but screens run at 60fps.
    *   *Frontend:* Use Linear Interpolation (Lerp) between the previous (x,y) and current (x,y) to make movement look smooth.

## 8. Requirements Addition
Add these to your `requirements.txt`:
```text
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pydantic>=2.0.0
```

---

# attributes_and_classes

# Attributes & Classes

Technical documentation for the 9 primary attributes, derived stats, stamina, hero classes, breakthroughs, skills, and mastery.

---

## Overview

Every entity can have an `Attributes` dataclass with **9 primary stats** that feed into derived combat and non-combat stats. Heroes are assigned a **class** at spawn that provides attribute bonuses, scaling grades, learnable skills, and a breakthrough path to an elite class.

**Primary files:** `src/core/attributes.py`, `src/core/classes.py`, `src/core/models.py`

---

## 1. Primary Attributes

| Attribute | Field | Effect |
|-----------|-------|--------|
| **STR** | `str_` | Physical ATK (+2%/pt), carry weight |
| **AGI** | `agi` | SPD (+0.4/pt), crit (+0.4%/pt), evasion (+0.3%/pt) |
| **VIT** | `vit` | Max HP (+2/pt), physical DEF (+0.3/pt) |
| **INT** | `int_` | XP gain (+1%/pt), MATK (+0.2/pt), cooldown reduction |
| **SPI** | `spi` | MATK (+0.6/pt), MDEF (+0.15/pt) — primary magic offense |
| **WIS** | `wis` | MDEF (+0.4/pt), luck (+0.3/pt), XP gain (+0.5%/pt) |
| **END** | `end` | Max stamina (+2/pt), max HP (+0.5/pt), HP regen |
| **PER** | `per` | Vision range (+0.3/pt), loot quality, detection |
| **CHA** | `cha` | Trade prices (+1%/pt), interaction speed, social influence |

### Attribute Caps

Each attribute has a cap (`AttributeCaps` dataclass):
- **Default cap:** 15 per attribute
- **Class bonuses:** Each class adds +5–10 to primary attribute caps
- **Level-up:** All caps increase by +5 per level

---

## 2. Derived Stats

Attributes feed into derived stats via formulas in `attributes.py`:

### Combat Stats

| Derived Stat | Formula |
|-------------|---------|
| Max HP | `base + VIT×2 + END×0.5` |
| ATK | `base + STR×0.5` |
| DEF | `base + VIT×0.3` |
| MATK | `base + SPI×0.6 + INT×0.2` |
| MDEF | `base + WIS×0.4 + SPI×0.15` |
| SPD | `base + AGI×0.4` |
| Crit Rate | `base + AGI×0.004` |
| Evasion | `base + AGI×0.003` |
| Luck | `base + WIS×0.3` |
| Max Stamina | `base + END×2` |
| HP Regen | `1.0 + END×0.15 + VIT×0.05` |
| Cooldown Reduction | `max(0.5, 1.0 - INT×0.005 - WIS×0.003)` |

### Non-Combat Stats

| Derived Stat | Formula |
|-------------|---------|
| XP Multiplier | `1.0 + INT×0.01 + WIS×0.005` |
| Vision Range | `base + PER×0.3` |
| Loot Bonus | `1.0 + PER×0.008 + WIS×0.003` |
| Trade Bonus | `1.0 + CHA×0.01` |
| Interaction Speed | `1.0 + CHA×0.005 + INT×0.005` |
| Rest Efficiency | `1.0 + END×0.008 + WIS×0.004` |

### Derived Stats Recalculation

`recalc_derived_stats(stats, attrs)` in `attributes.py`:

| Mode | When Used | Behavior |
|------|-----------|----------|
| **Creation** (`old_attrs=None`) | `EntityBuilder.build()` | Adds attribute bonuses on top of raw base stats |
| **Delta** (`old_attrs` provided) | Level-up, training | Strips old contributions, applies new ones |

---

## 3. Attribute Training

Attributes grow fractionally through actions using `train_attributes()`:

| Action | Trained Attributes |
|--------|-------------------|
| `attack` | STR +0.015, AGI +0.008 |
| `magic_attack` | SPI +0.015, INT +0.008 |
| `move` | AGI +0.008, END +0.005, PER +0.003 |
| `harvest` | END +0.010, WIS +0.005, PER +0.004 |
| `loot` | WIS +0.005, PER +0.006 |
| `skill` | INT +0.010, WIS +0.005, SPI +0.008 |
| `rest` | WIS +0.006, END +0.003 |
| `trade` | CHA +0.012, WIS +0.003 |
| `explore` | PER +0.010, AGI +0.005 |
| `interact` | CHA +0.008, INT +0.004 |
| `defend` | VIT +0.010, END +0.008 |

Fractional accumulation (e.g. 67 attacks → +1 STR). Training never exceeds the cap. Uses a data-driven `_TRAIN_MAP`.

### Level-Up Attribute Gains

On each level-up (`level_up_attributes()`):
- All **9** primary attributes: **+2** (capped)
- All **9** attribute caps: **+5**

---

## 4. Stamina System

Every entity has `stamina` and `max_stamina` fields on `Stats`.

### Stamina Costs

| Action | Cost |
|--------|------|
| Attack | 3 |
| Move | 1 |
| Harvest | 2 |

### Stamina Regeneration (per tick)

| State | Regen |
|-------|-------|
| RESTING_IN_TOWN, IDLE | 5 |
| VISIT_SHOP, VISIT_BLACKSMITH, VISIT_GUILD, VISIT_CLASS_HALL, VISIT_INN | 4 |
| All other states | 1 |

Capped at `max_stamina`.

---

## 5. Hero Classes

### Scaling Grades

| Grade | Mult | Description |
|-------|------|-------------|
| E | 60% | Minimal benefit |
| D | 75% | Below average |
| C | 90% | Average |
| B | 100% | Baseline |
| A | 115% | Strong |
| S | 130% | Excellent — primary stat |
| SS | 150% | Outstanding — breakthrough |
| SSS | 180% | Legendary — reserved |

### Base Classes (Tier 1)

| Class | Primary Scaling | Bonuses | Cap Bonuses | Breakthrough |
|-------|----------------|---------|-------------|-------------|
| **Warrior** | STR=S, VIT=A | STR+3, VIT+2, END+1 | STR+10, VIT+5 | → Champion (Lv10, STR≥30) |
| **Ranger** | AGI=S, END=A | AGI+3, WIS+2, END+1 | AGI+10, WIS+5, PER+3 | → Sharpshooter (Lv10, AGI≥30) |
| **Mage** | SPI=S, WIS=A | INT+2, SPI+3, WIS+2 | SPI+10, INT+5, WIS+5 | → Archmage (Lv10, SPI≥30) |
| **Rogue** | AGI=S, STR=B | STR+2, AGI+2, WIS+1 | AGI+8, STR+5, WIS+3 | → Assassin (Lv10, AGI≥25) |

### Breakthrough Classes (Tier 2)

| Class | From | Talent |
|-------|------|--------|
| **Champion** | Warrior | Unyielding — Below 25% HP → +30% DEF, +20% ATK for 5 ticks |
| **Sharpshooter** | Ranger | Precision — Crits deal +25% damage; Quick Shot range +1 |
| **Archmage** | Mage | Arcane Mastery — Skill durations +1 tick; cooldowns −1 tick |
| **Assassin** | Rogue | Lethal — Guaranteed crit vs targets below 30% HP; Backstab → 2.8× |

### Progression Tiers

```
Warrior  → Champion      → [Transcendence] (future)
Ranger   → Sharpshooter  → [Transcendence]
Mage     → Archmage      → [Transcendence]
Rogue    → Assassin      → [Transcendence]
```

---

## 6. Skills

### Skill Definitions (`SkillDef`)

Each skill has: `name`, `skill_type` (ACTIVE/PASSIVE), `target`, `power`, `stamina_cost`, `cooldown`, `level_req`, `class_req`, `gold_cost`, `description`, `mastery_req`, `mastery_threshold`.

### Learning Prerequisites

Skills form a prerequisite chain. To learn tier-2 or tier-3 skills:
1. Meet level requirement (`level_req`)
2. Have sufficient gold (`gold_cost`)
3. Know the prerequisite skill (`mastery_req`)
4. Have prerequisite at mastery ≥ threshold (default 25.0)

### Class Skills

| Warrior | Ranger | Mage | Rogue |
|---------|--------|------|-------|
| Power Strike (Lv1, 1.8×, CD4) | Quick Shot (Lv1, 1.5×, CD3, range 3) | Arcane Bolt (Lv1, 2.0×, CD4, range 4) | Backstab (Lv1, 2.2×, CD4, CRIT+15%) |
| Shield Wall (Lv3, DEF+50% 3t, CD8) | Evasive Step (Lv3, EVA+30% 3t, CD7) | Frost Shield (Lv3, DEF+40% 3t, CD8) | Shadowstep (Lv3, EVA+40% SPD+30% 2t, CD7) |
| Battle Cry (Lv5, AoE ATK+20% 3t, CD12) | Mark Prey (Lv5, DEF-25% 4t, CD10) | Mana Surge (Lv5, ATK+30% 4t, CD12) | Poison Blade (Lv5, DoT 4t, CD10) |

### Race Skills (Innate, Free)

| Race | Skills |
|------|--------|
| Hero | Rally (AoE ATK+10% DEF+10% 3t), Second Wind (Heal 20% max HP, CD20) |
| Wolf | Pack Hunt, Feral Bite |
| Goblin | Ambush, Quickdraw |
| Orc | Berserker Rage, War Cry |
| Undead | Drain Life |

### Skill Instances (`SkillInstance`)

Runtime state per entity:
- `cooldown_remaining` — ticks until ready
- `mastery` — 0.0 to 100.0, gained by using the skill
- `times_used` — total use count

### Mastery Tiers

| Tier | Mastery | Power Bonus | Stamina Reduction | Cooldown Reduction |
|------|---------|-------------|-------------------|--------------------|
| Novice | 0–24% | — | — | — |
| Apprentice | 25–49% | — | −10% | — |
| Adept | 50–74% | +20% | −10% | — |
| Expert | 75–99% | +20% | −20% | −1 tick |
| Master | 100% | +35% | −25% | −1 tick |

### Skill Modifiers & Effects

Skills can define stat modifiers that create temporary `StatusEffect`s:

| Modifier | Description |
|----------|-------------|
| `atk_mod` | % change to ATK (e.g. +0.2 = +20%) |
| `def_mod` | % change to DEF |
| `spd_mod` | % change to SPD |
| `crit_mod` | % change to crit rate |
| `evasion_mod` | % change to evasion |
| `hp_mod` | Instant heal as % of max HP (SELF skills) |
| `duration` | Ticks the buff/debuff lasts |

- **SELF / AREA_ALLIES** → `SKILL_BUFF` effect on caster/allies
- **SINGLE_ENEMY / AREA_ENEMIES** → `SKILL_DEBUFF` effect on enemies

Modifiers convert to multipliers: `atk_mod=0.2` → `atk_mult=1.2`. Multiple effects stack multiplicatively.

---

## 7. Enhanced Stats (`Stats` dataclass)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `hp` / `max_hp` | int | 20 | Health |
| `atk` | int | 5 | Base physical attack |
| `def_` | int | 0 | Base physical defense |
| `spd` | int | 10 | Speed |
| `luck` | int | 0 | Crit/evasion modifier |
| `crit_rate` / `crit_dmg` | float | 0.05 / 1.5 | Critical hit stats |
| `evasion` | float | 0.0 | Dodge chance |
| `matk` | int | 0 | Base magical attack |
| `mdef` | int | 0 | Base magical defense |
| `level` / `xp` / `xp_to_next` | int | 1/0/100 | Leveling |
| `gold` | int | 0 | Currency |
| `stamina` / `max_stamina` | int | 50 | Action resource |
| `vision_range` | int | 6 | Perception radius |
| `elem_vuln` | dict | {} | Element → vulnerability multiplier |

---

# buildings_and_economy

# Buildings & Economy

Technical documentation for town buildings, shop system, crafting, guild services, quests, and treasure chests.

---

## Overview

Six buildings are placed in the town during world generation. Each provides services that the hero interacts with via dedicated AI states. The economy loop drives the hero to fight, loot, sell, buy, craft, and quest in a continuous cycle.

**Primary files:** `src/core/buildings.py`, `src/core/quests.py`, `src/core/items.py` (TreasureChest), `src/ai/states.py`

---

## 1. Town Buildings

### Data Model (`src/core/buildings.py`)

```python
@dataclass(slots=True)
class Building:
    building_id: str       # "store", "blacksmith", "guild", "class_hall", "inn", "hero_house"
    name: str
    pos: Vector2
    building_type: str
```

Buildings are static locations stored in `WorldState.buildings` and exposed in the API as `BuildingSchema`.

### Building List

| Building | Type | Position | AI State | Service |
|----------|------|----------|----------|---------|
| General Store | `store` | Top-left of town | VISIT_SHOP | Buy/sell items |
| Blacksmith | `blacksmith` | Top-right of town | VISIT_BLACKSMITH | Learn recipes, craft items |
| Adventurer's Guild | `guild` | Bottom-center of town | VISIT_GUILD | Intel, quests, tips |
| Class Hall | `class_hall` | Bottom-left of town | VISIT_CLASS_HALL | Learn skills, breakthroughs |
| Traveler's Inn | `inn` | Bottom-right of town | VISIT_INN | Rapid HP/stamina recovery |
| Hero's House | `hero_house` | Near town center | VISIT_HOME | Store/retrieve items |

---

## 2. General Store

### Selling

Heroes sell items they don't need:
- **Gold pouches/treasure** — always sold (converted to gold)
- **Materials** — sold unless needed for current craft target
- **Inferior equipment** — sold if hero has better gear equipped

Sell prices: Common 5g, Uncommon 15g, Rare 40g. Materials use their explicit `sell_value`.

### Buying

The store stocks consumables, equipment, and accessories:

| Category | Items |
|----------|-------|
| **Healing** | Small/Medium/Large HP Potion, Herbal Remedy |
| **Buff Potions** | ATK/DEF/SPD Elixir, Critical Elixir, Antidote |
| **Weapons** | Wooden Club, Bandit Dagger, Iron Sword, Orc Axe, Steel Greatsword |
| **Magic Weapons** | Apprentice Staff, Fire Staff |
| **Armor** | Leather Vest, Chainmail, Orc Shield, Plate Armor |
| **Magic Armor** | Cloth Robe, Silk Robe |
| **Accessories** | Lucky Charm, Speed Ring, Mana Crystal, Spirit Pendant |
| **Materials** | Mana Shard, Silver Ingot, Phoenix Feather |

### AI Purchase Priorities (`hero_wants_to_buy()`)

1. **Healing potions** if total < 2 (best tier affordable)
2. **Equipment upgrades** — best power gain across all slots
3. **Buff potions** if none owned
4. **Craft materials** for active craft target

---

## 3. Blacksmith

### Recipe Learning

When a hero first visits, they learn all available recipes. The blacksmith helps pick a **craft target** — the most powerful item that would be an upgrade.

### Recipes

#### Goblin-Material Recipes

| Recipe | Output | Gold | Materials |
|--------|--------|------|-----------|
| Steel Sword | `steel_sword` | 60g | 2× Iron Ore, 1× Wood |
| Battle Axe | `battle_axe` | 90g | 3× Iron Ore, 1× Steel Bar |
| Enchanted Blade | `enchanted_blade` | 200g | 2× Steel Bar, 2× Enchanted Dust |
| Iron Plate | `iron_plate` | 70g | 3× Iron Ore, 1× Leather |
| Enchanted Robe | `enchanted_robe` | 150g | 2× Leather, 1× Enchanted Dust |
| Ring of Power | `ring_of_power` | 120g | 1× Iron Ore, 1× Enchanted Dust |
| Evasion Amulet | `evasion_amulet` | 80g | 2× Leather, 1× Wood |

#### Race-Specific Recipes

| Recipe | Output | Gold | Materials | Terrain |
|--------|--------|------|-----------|---------|
| Wolf Cloak | `wolf_cloak` | 50g | 2× Wolf Pelt, 1× Leather | Forest |
| Fang Necklace | `fang_necklace` | 45g | 2× Wolf Fang, 1× Fiber | Forest + Desert |
| Desert Composite Bow | `desert_bow` | 75g | 1× Raw Gem, 2× Fiber | Desert |
| Bone Shield | `bone_shield` | 65g | 3× Bone Shard, 1× Dark Moss | Swamp |
| Spectral Blade | `spectral_blade` | 180g | 2× Ectoplasm, 1× Enchanted Dust | Swamp |
| Mountain Plate | `mountain_plate` | 160g | 3× Stone Block, 2× Iron Ore | Mountain |
| Herbal Remedy | `herbal_remedy` | 15g | 3× Herb, 1× Glowing Mushroom | Forest + Swamp |

### Crafting Flow

1. Hero visits blacksmith → learns recipes → picks best upgrade as craft target
2. Hero adventures to gather materials and gold
3. When hero has all required materials + gold, returns to blacksmith
4. Blacksmith consumes materials + gold, produces item
5. Item auto-equipped if better than current gear
6. `craft_target` cleared after successful crafting

---

## 4. Adventurer's Guild

### Camp Intel

Reveals all enemy camp locations by adding them to the hero's `terrain_memory`.

### Resource Node Intel

Reveals all harvestable resource node locations across terrain regions.

### Material Hints

If the hero has a craft target, provides tips about where to find each required material (covering all races and terrains). Added to hero's `goals` list.

### Terrain Tips

General tips about which terrains host which races and materials:
- **Forests** → wolves → wolf pelts, wolf fangs
- **Deserts** → bandits → fiber, raw gems
- **Swamps** → undead → bone shards, ectoplasm
- **Mountains** → orcs → stone blocks, iron ore

### Quest Generation

See section 6 below.

---

## 5. Class Hall

### Services

1. **Learn class skills** — costs gold, requires level + prerequisites
2. **Attempt breakthroughs** — when level and attribute thresholds met

### AI Integration

`hero_should_visit_class_hall()` returns true when:
- Hero has unlearned skills available at their level + affordable gold
- Hero meets breakthrough requirements

`VisitClassHallHandler`:
1. Walks to Class Hall
2. Learns available skills (deducts gold)
3. Attempts breakthrough if eligible (applies bonuses, changes class)

See `attributes_and_classes.md` for full class/skill details.

---

## 6. Quest System (`src/core/quests.py`)

### Quest Types

| Type | Target | Completion Condition |
|------|--------|---------------------|
| **HUNT** | Enemy kind | Kill `target_count` enemies of that kind |
| **EXPLORE** | Map coordinate | Move within 2 tiles of `target_pos` |
| **GATHER** | Item ID | Collect `target_count` items via loot or harvest |

### Quest Model

| Field | Type | Description |
|-------|------|-------------|
| `quest_id` | str | Unique identifier |
| `quest_type` | QuestType | HUNT, EXPLORE, GATHER |
| `title` / `description` | str | Display text |
| `target_kind` | str | Enemy kind or item ID |
| `target_pos` | Vector2 \| None | For EXPLORE quests |
| `target_count` | int | Required kills/items |
| `progress` | int | Current count |
| `completed` | bool | True when done |
| `gold_reward` / `xp_reward` | int | Completion rewards |
| `item_reward` | str | Optional item reward |

### Quest Templates (10 built-in)

| Template | Type | Min Level | Targets |
|----------|------|-----------|---------|
| hunt_goblin | HUNT | 1 | goblin, goblin_scout, goblin_warrior |
| hunt_wolf | HUNT | 1 | wolf, dire_wolf |
| hunt_bandit | HUNT | 2 | bandit, bandit_archer, bandit_chief |
| hunt_undead | HUNT | 3 | skeleton, zombie |
| hunt_orc | HUNT | 4 | orc, orc_warrior |
| gather_herbs | GATHER | 1 | herb |
| gather_ore | GATHER | 2 | iron_ore |
| gather_pelts | GATHER | 1 | wolf_pelt |
| explore_region | EXPLORE | 1 | random map coordinate |

Rewards scale with `count` and `hero_level` (×1.0 + level×0.1).

### Quest Limits

- **MAX_ACTIVE_QUESTS:** 3 per hero
- Completed quests pruned every 50 ticks

### Quest Progress Tracking

| Quest Type | Hook Location | Trigger |
|-----------|--------------|--------|
| HUNT | `CombatAction.apply()` | On enemy kill, matches `defender.kind` |
| GATHER | `WorldLoop._process_item_actions()` | On LOOT or HARVEST, matches item ID |
| EXPLORE | `WorldLoop._tick_quests()` | Each tick, checks manhattan distance ≤ 2 |

On completion, rewards (gold + XP) immediately added to hero's stats.

### Guild Integration

`VisitGuildHandler`:
1. Reveals camp locations and resource nodes
2. If hero has < 3 active quests → generates new quest via `generate_quest()`
3. Provides material hints and terrain tips

---

## 7. Treasure Chest System (`src/core/items.py`)

Chests are placed near camps during world generation.

### Chest Tiers

| Tier | Loot Quality | Respawn Time | Guard Tier |
|------|-------------|-------------|------------|
| 1 (Common) | Basic potions, ore, leather | 200 ticks | WARRIOR |
| 2 (Rare) | Medium potions, buff elixirs, steel, accessories | 250 ticks | ELITE |
| 3 (Legendary) | Large potions, rare materials, elite gear | 300 ticks | ELITE |

### Mechanics

- **Guards:** Each chest has a guard entity (spawned from local terrain race). Guard must be defeated before looting.
- **Looting:** When hero performs LOOT at a chest's position and guard is dead/absent, loot generated from `CHEST_LOOT_TABLES` and dropped on ground.
- **Respawning:** `_tick_treasure_chests()` checks each tick. When `respawn_at` reached, chest becomes available and new guard spawns.

### Loot Table Format

```python
CHEST_LOOT_TABLES[tier] = [
    (item_id, drop_chance, min_count, max_count),
    ...
]
```

### Integration

- Spawned in `engine_manager.py` during world init (near each camp)
- `WorldState.treasure_chests` dict
- `Snapshot.treasure_chests` tuple (immutable copy)
- API: `TreasureChestSchema` with `chest_id`, position, `tier`, `looted`, `guard_entity_id`

---

## 8. Economy Decision Flow

After fully healing in town (`RestingInTownHandler`):

1. **Sell items** → has sellable items → `VISIT_SHOP`
2. **Buy upgrades** → enough gold for upgrade → `VISIT_SHOP`
3. **Visit blacksmith** → needs recipes or can craft → `VISIT_BLACKSMITH`
4. **Visit guild** → lacks intel or needs quest → `VISIT_GUILD`
5. **Visit class hall** → can learn skills or breakthrough → `VISIT_CLASS_HALL`
6. **Leave town** → nothing to do → `WANDER`

Each handler moves the hero to the building, then performs the interaction when adjacent.

---

# combat_and_progression

# Combat & Progression

Technical documentation for combat formulas, damage types, elements, leveling, death/respawn, and the speed/delay system.

---

## Overview

Combat is resolved deterministically using effective stats (base + equipment + attribute bonuses + status effects). The system supports dual damage types (physical/magical), elemental vulnerabilities, evasion, critical hits, potion use, and skill-based attacks. Killing enemies awards XP and gold, with level-ups granting permanent stat and attribute growth.

**Primary files:** `src/actions/combat.py`, `src/actions/damage.py`, `src/engine/world_loop.py`

---

## Damage Types (Strategy Pattern)

Each damage type is a `DamageCalculator` subclass registered in `DAMAGE_CALCULATORS`. Combat code calls `get_damage_calculator(damage_type)` and uses the returned `DamageContext` — no if/else branching.

| Type | Calculator | Stat Pair | Attribute Scaling |
|------|-----------|-----------|-------------------|
| **PHYSICAL** (0) | `PhysicalDamageCalculator` | ATK vs DEF | STR boosts attack (+2%/pt), VIT boosts defense (+1%/pt) |
| **MAGICAL** (1) | `MagicalDamageCalculator` | MATK vs MDEF | SPI boosts attack (+2%/pt), WIS boosts defense (+1%/pt) |

The weapon's `damage_type` field selects the calculator. Training action is `attack` for physical, `magic_attack` for magical.

---

## Combat Resolution Pipeline

Each attack is processed in `CombatAction.apply()`:

### Step 1: Evasion Check

```
effective_evasion = defender.effective_evasion() - attacker.stats.luck * 0.002
evasion_chance = clamp(effective_evasion, 0.0, 0.75)
if random_roll < evasion_chance → MISS (no damage)
```

- Attacker's `luck` reduces defender's evasion
- Evasion capped at 75%

### Step 2: Base Damage (Attribute-Enhanced)

```
atk_power = attacker.effective_atk() * sanctuary_atk_mult    # or effective_matk()
def_power = defender.effective_def() * sanctuary_def_mult     # or effective_mdef()

atk_mult = 1.0 + attacker_primary_attr * 0.02
def_mult = 1.0 + defender_primary_attr * 0.01

damage = int(atk_power * atk_mult) - int(def_power * def_mult) // 2
damage = max(damage, 1)
```

- Minimum 1 damage guaranteed
- Sanctuary multipliers apply to non-hero entities on sanctuary tiles (default 0.5×)

### Step 2b: Stamina Cost

Each attack costs 3 stamina. If stamina reaches 0, the entity can still attack but gains no attribute training.

### Step 3: Damage Variance

```
variance_roll = rng.next_float(Domain.COMBAT, attacker.id, tick)
damage = damage * (1.0 + damage_variance * (variance_roll - 0.5))
```

- `damage_variance` defaults to 0.3 (±15% spread)
- Uses deterministic RNG seeded by attacker ID and tick

### Step 4: Critical Hit

```
crit_chance = attacker.effective_crit_rate() + attacker.stats.luck * 0.003
crit_chance = clamp(crit_chance, 0.0, 0.80)
if random_roll < crit_chance:
    damage = damage * attacker.stats.crit_dmg
```

- Luck adds 0.3% per point; capped at 80%
- `crit_dmg` default: 1.5× (hero starts at 1.8×)

### Step 5: Elemental Vulnerability

```
element = weapon_element or skill_element  (default NONE)
vulnerability = defender.stats.elem_vuln.get(element, 1.0)
damage = damage * vulnerability
```

- Values > 1.0 = weakness, < 1.0 = resistance, 0.0 = immune

### Step 6: Apply Damage

```
defender.stats.hp -= int(damage)
attacker.next_act_at += speed_delay(attacker.effective_spd(), "attack")
```

---

## Elements

| Element | Value |
|---------|-------|
| NONE | 0 |
| FIRE | 1 |
| ICE | 2 |
| LIGHTNING | 3 |
| DARK | 4 |
| HOLY | 5 |

Each entity has an `elem_vuln` table on `Stats` (dict mapping Element → float). Default is 1.0 for all.

---

## On-Kill Rewards

### XP Award

```
base_xp = xp_per_kill_base * defender.level * (1 + defender.tier * 0.5)
xp_mult = 1.0 + attacker.attributes.int_ * 0.01 + attacker.attributes.wis * 0.005
xp_gained = int(base_xp * xp_mult)
```

- **INT** adds +1% XP per point; **WIS** adds +0.5% XP per point

### Gold Transfer

All of the defender's gold is transferred to the attacker.

### Attribute Training

Combat trains STR (+0.015/action) and AGI (+0.008/action) for physical attacks, SPI (+0.015) and INT (+0.008) for magical attacks.

---

## Leveling System (epic-18 Phase A)

Level-ups checked each tick in `WorldLoop._check_level_ups()`.

### Level-Up Condition

Each entity is bound to a specific `RACE_PROFILE` defining their `train_rate`, `level_cap`, and `evolves` logic.
- Entities without a profile or a `train_rate=0.0` (like `skeleton`) earn 0 XP.

```python
while entity.stats.xp >= entity.stats.xp_to_next and level < profile.level_cap:
    level up
```

Excess XP carries over.

### Stat Growth Per Level

Base dimishing returns stat growth based on the current level bracket:
- Levels 1-10: HP +5, ATK/DEF/SPD +1
- Levels 11-20: HP +3, ATK/DEF/SPD +1
- Levels 21-30: HP +2, ATK/DEF/SPD +0

**Milestone Levels (5, 10, 15, 20, 25, 30)**:
Whenever these levels are crossed, instead of base growth, the entity receives roughly **3x massive stat spikes** (+15 HP, +3 ATK/DEF/SPD). An event is emitted highlighting the milestone.

### Attribute Growth Per Level

On each level-up, `level_up_attributes()` is called:
- All **9** primary attributes: **+2** (capped at current cap)
- All **9** attribute caps: **+5**

### XP Curve

XP to next level dynamically scales by the current level:

- Levels 1-10: `xp_to_next *= 1.4`
- Levels 11-20: `xp_to_next *= 1.6`
- Levels 21-30: `xp_to_next *= 2.0`

---

## Veterancy & Innate Talents (epic-18 Phase B)

### Veterancy Ranks
Entities earn veterancy points in combat (+1 per hit dealt, +1 survived hit, +5 to +10 per kill). This grants multiplier bonuses over time.
- **GREEN**: 1.0x (0 points)
- **BLOODED**: 1.03x ATK/DEF (25 points)
- **VETERAN**: 1.06x ATK/DEF, 1.05x HP (80 points)
- **ELITE**: 1.1x ATK/DEF/HP, 1.05x SPD (200 points)
- **LEGEND**: 1.15x All Stats (500 points)

### Innate Talents
Every entity generates with 2 random `talents` and 1 `weakness` across the 9 core attributes.  
- Attacking, taking damage, and working adds fractional EXP to `attributes`.
- **Talented** attributes train at `2.0x` speed.
- **Weaknesses** train at `0.5x` speed.

---

## Potion Use in Combat

When in `COMBAT` state with HP below 50%:

1. Check inventory for potions (priority: large > medium > small)
2. Propose `USE_ITEM` action instead of `ATTACK`
3. Potion consumed, entity heals by `template.heal_amount` (capped at `effective_max_hp()`)
4. Action delay: 0.5 ticks (half a normal action)

| Potion | Heal |
|--------|------|
| `small_hp_potion` | 20 HP |
| `medium_hp_potion` | 40 HP |
| `large_hp_potion` | 80 HP |

---

## Skill-Based Attacks

Skills are used via `USE_SKILL` action when:
- Skill is off cooldown
- Entity has enough stamina
- Target is in range

Skill damage uses `power` multiplier on base damage, skill-specific `damage_type` and `element`, and applies buff/debuff effects based on skill modifiers. See `attributes_and_classes.md` for skill details.

---

## Ranged Combat (epic-05 F4)

Ranged weapons and skills can hit targets beyond melee range, with line-of-sight and cover mechanics.

**Primary files:** `src/core/items.py`, `src/core/grid.py`, `src/actions/combat.py`, `src/ai/states.py`

### Weapon Range

Each weapon has a `weapon_range` field on `ItemTemplate` (default 1 = melee). Ranged weapons:

| Weapon | Range | Type |
|--------|-------|------|
| Swords/Daggers | 1 | Melee |
| Shortbow | 3 | Ranged |
| Longbow/Hunting Bow | 4 | Ranged |
| Staves/Wands | 3 | Ranged (magical) |
| Windpiercer | 5 | Ranged |

### Line of Sight

Ranged attacks require clear LoS via Bresenham's line algorithm (`Grid.has_line_of_sight()`). Any WALL tile between attacker and defender blocks the attack.

### Cover System

Defenders adjacent to a WALL tile get **+10% evasion** against ranged attacks. Checked via `Grid.has_adjacent_wall()`.

### AI Kiting

Ranged entities (weapon_range ≥ 3) kite when:
- Adjacent to enemy (dist ≤ 1)
- HP > 60%
- Propose `MOVE` away instead of attacking

---

## AoE Attacks & Skills (epic-05 F1)

Skills with `AREA_ENEMIES` or `AREA_ALLIES` target types hit multiple entities in a radius.

**Primary files:** `src/core/classes.py` (SkillDef), `src/engine/world_loop.py` (resolution)

### SkillDef Fields

| Field | Type | Description |
|-------|------|-------------|
| `radius` | int | AoE spread from impact point (0 = single target) |
| `aoe_falloff` | float | Damage reduction per tile from center (default 0.15) |

### AoE Skills

| Skill | Class | Range | Radius | Falloff | Power | Type |
|-------|-------|-------|--------|---------|-------|------|
| Whirlwind | Warrior | 1 | 1 | 0.0 | 1.5 | Physical |
| Rain of Arrows | Ranger | 4 | 2 | 0.15 | 1.4 | Physical |
| Fireball | Mage | 4 | 2 | 0.20 | 1.8 | Magical |

### AoE Resolution

1. Impact point = nearest hostile within cast range
2. Collect all valid targets within `radius` of impact point
3. Per target: `damage *= max(0, 1.0 - dist_from_center * aoe_falloff)`
4. Crits only on center target (`dist_from_center == 0`)
5. Damage variance uses unique seed per target (`tick + 5 + eid`)

### AI AoE Preference

`best_ready_skill()` scores AoE skills as `power * nearby_enemies` when multiple enemies are clustered (nearby_enemies > 1), preferring AoE over single-target.

---

## Aggro & Threat System (epic-05 F3)

Enemies track threat per attacker and target the highest-threat entity instead of nearest.

**Primary files:** `src/core/models.py`, `src/actions/combat.py`, `src/engine/world_loop.py`, `src/ai/perception.py`, `src/ai/states.py`

### Threat Table

Each entity has `threat_table: dict[int, float]` mapping attacker IDs to accumulated threat scores.

### Threat Generation

| Source | Formula |
|--------|---------|
| Basic attack damage | `damage * threat_damage_mult` (1.0) |
| Skill damage | `damage * threat_damage_mult` (1.0) |
| Opportunity attack | `damage * threat_damage_mult` (1.0) |
| Tank class bonus | Warrior/Champion get `threat_tank_class_mult` (1.5×) |

### Threat Decay

`_tick_threat_decay()` runs every core tick:
- All threat entries decay by `threat_decay_rate` (10%) per tick
- Entries below 1.0 are pruned
- Dead attacker entries removed

### AI Targeting

- **Mobs** (non-HERO_GUILD): use `highest_threat_enemy()` — target visible hostile with highest threat score, fallback to nearest
- **Heroes**: always use `nearest_enemy()` for intuitive behavior

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `threat_decay_rate` | 0.10 | 10% decay per tick |
| `threat_damage_mult` | 1.0 | Threat per point of damage |
| `threat_heal_mult` | 0.5 | Threat per point of healing (future) |
| `threat_tank_class_mult` | 1.5 | Multiplier for Warrior/Champion |

---

## Chase Mechanics (epic-05)

Two systems that add depth to melee engagement and pursuit.

**Primary files:** `src/engine/world_loop.py`

### Opportunity Attacks

When an entity moves away from an adjacent hostile (Manhattan distance increases), the hostile gets a free reduced-damage hit:

```
damage = max(1, int(attacker_atk * opportunity_attack_damage_mult) - defender_def // 2)
```

- `opportunity_attack_damage_mult`: 0.5 (half-damage)
- No crit, no evasion check
- Generates threat on the mover
- Emits `"combat"` event with `verb=OPPORTUNITY_ATTACK`

### SPD-Based Chase Closing

Faster hunters periodically gain a bonus tile of movement when chasing slower prey:

```
interval = ceil(chase_spd_closing_base * target_spd / hunter_spd)
if chase_ticks % interval == 0 → bonus move toward target
```

- `chase_spd_closing_base`: 6
- Only triggers for HUNT-state entities with higher SPD than target
- Emits `"movement"` event with `verb=CHASE_SPRINT`

---

## Speed & Action Delay System

Defined in `src/core/attributes.py` via `speed_delay()`. Uses logarithmic diminishing returns with action-type multipliers.

### Formula

```
delay = action_mult / (1.0 + ln(max(spd, 1)))
```

Clamped to `[0.15, 2.0]` seconds.

### SPD → Delay Table (move action)

| SPD | Delay | Actions/tick |
|-----|-------|-------------|
| 1 | 1.00 | 1.0 |
| 5 | 0.53 | 1.9 |
| 10 | 0.38 | 2.6 |
| 20 | 0.31 | 3.2 |
| 50 | 0.24 | 4.2 |

### Action-Type Multipliers

| Action | Multiplier | Effect |
|--------|-----------|--------|
| Move | ×1.0 | Baseline |
| Attack | ×0.9 | Slightly faster than moving |
| Skill | ×1.2 | Slower (powerful abilities) |
| Loot | ×0.7 | Fast pickup |
| Harvest | ×0.7 | Fast gathering |
| Use Item | ×0.6 | Fastest (potions should be quick) |
| Rest | ×1.0 | Same as baseline |

For non-combat actions, the `interaction_speed` derived stat further scales delay.

### Engagement Lock (Anti-Kite)

Tracked via `Entity.engaged_ticks`, incremented each tick adjacent (Manhattan ≤ 1) to a hostile. Reset to 0 when no hostiles adjacent.

When `engaged_ticks >= 2`, moving away costs **double** the normal delay:
- Slow tanky builds can pin down fast enemies
- Fast builds still act more often but can't kite indefinitely
- Penalty paid once per disengage, then `engaged_ticks` resets

---

## Death & Respawn

### Hero Death

1. All **bag items** dropped as ground loot at death position
2. **Equipment** preserved (weapon, armor, accessory stay)
3. HP restored to `max_hp`
4. Teleported to `home_pos` (town center)
5. AI state set to `RESTING_IN_TOWN`
6. Action cooldown: `hero_respawn_ticks` (10 ticks)
7. Combat memory cleared

### Enemy Death

1. All items (bag + equipment) dropped as ground loot
2. Entity removed from the world permanently
3. Generator may spawn replacements on schedule

---

## Determinism

All combat calculations use `DeterministicRNG` with domain `Domain.COMBAT`:

- Damage variance: `rng.next_float(COMBAT, attacker_id, tick)`
- Crit roll: `rng.next_bool(COMBAT, attacker_id, tick + 1, chance)`
- Evasion roll: `rng.next_bool(COMBAT, attacker_id, tick + 2, evasion)`

Identical outcomes given the same world seed, regardless of thread scheduling.

---

# design_patterns

# Design Patterns & Extension Guide

Technical documentation for the OOP design patterns used in the simulation engine and how to extend each system.

---

## Overview

The engine uses five core patterns to maintain extensibility and the Open/Closed Principle. Each system can be extended by adding new classes and registering them — without modifying existing code.

---

## 1. Goal Evaluation — Plugin Pattern

**Location:** `src/ai/goals/`

### Pattern

Each AI goal is a self-contained `GoalScorer` subclass. The `GoalEvaluator` iterates all registered scorers without knowing their internals. New goals are added by creating a class and registering it — zero changes to existing code.

```
GoalScorer (ABC)
├── CombatGoal      → AIState.HUNT
├── FleeGoal        → AIState.FLEE
├── ExploreGoal     → AIState.WANDER
├── LootGoal        → AIState.LOOTING
├── TradeGoal       → AIState.VISIT_SHOP
├── RestGoal        → AIState.RESTING_IN_TOWN
├── CraftGoal       → AIState.VISIT_BLACKSMITH
├── SocialGoal      → AIState.VISIT_GUILD
└── GuardGoal       → AIState.GUARD_CAMP
```

### Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `GoalScorer` | `goals/base.py` | ABC: `name`, `target_state`, `score(ctx)` |
| `GoalScore` | `goals/base.py` | Dataclass: `(goal, score, target_state)` |
| `GoalEvaluator` | `goals/base.py` | `evaluate(ctx)` → sorted scores, `select(scores, rng)` → winner |
| `GOAL_REGISTRY` | `goals/base.py` | Module-level list of registered `GoalScorer` instances |
| `register_goal()` | `goals/base.py` | Append a scorer to the registry |

### How to Add a New Goal

1. Create a `GoalScorer` subclass:

```python
class QuestGoal(GoalScorer):
    @property
    def name(self) -> str:
        return "quest"

    @property
    def target_state(self) -> AIState:
        return AIState.QUEST  # add to enums.py first

    def score(self, ctx: AIContext) -> float:
        if not ctx.actor.active_quest:
            return 0.0
        return 0.6
```

2. Register in `goals/registry.py`:

```python
register_goal(QuestGoal())
```

3. Add a `StateHandler` in `ai/states.py` for the new state.

### Design Decisions

- **Classes over functions:** Allow properties (`name`, `target_state`), inheritance, and cached state across ticks.
- **Global registry:** Simple. For testing, clear and re-register. For mods, call `register_goal()`.

---

## 2. Damage Calculation — Strategy Pattern

**Location:** `src/actions/damage.py`

### Pattern

Each damage type is a `DamageCalculator` subclass that resolves ATK/DEF power, attribute multipliers, and training actions. Combat code calls `get_damage_calculator(damage_type)` and uses the returned `DamageContext` — no if/else branching.

```
DamageCalculator (ABC)
├── PhysicalDamageCalculator  (ATK vs DEF, STR/VIT scaling)
└── MagicalDamageCalculator   (MATK vs MDEF, SPI/WIS scaling)
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `DamageCalculator` | ABC: `damage_type`, `resolve(attacker, defender) -> DamageContext` |
| `DamageContext` | Dataclass: `atk_power`, `def_power`, `atk_mult`, `def_mult`, `train_action` |
| `DAMAGE_CALCULATORS` | Registry dict: `DamageType -> DamageCalculator` |
| `get_damage_calculator()` | Lookup with physical fallback |

### How to Add a New Damage Type

1. Add enum value in `src/core/enums.py`
2. Create a `DamageCalculator` subclass
3. Register: `DAMAGE_CALCULATORS[DamageType.TRUE] = TrueDamageCalculator()`

### Design Decisions

- **Classes over config dicts:** Classes can override complex logic (e.g., HYBRID damage splitting PHY/MAG).
- **`DamageContext` dataclass:** Decouples resolution from application. Combat code only sees the context.

---

## 3. Entity Construction — Builder Pattern

**Location:** `src/core/entity_builder.py`

### Pattern

The `EntityBuilder` provides a fluent API for constructing `Entity` instances. All spawn sites (hero, goblin, race-specific) use the same builder, eliminating code duplication.

### Usage

```python
hero = (
    EntityBuilder(rng, eid, tick=0)
    .kind("hero")
    .at(pos)
    .home(town_center)
    .faction(Faction.HERO_GUILD)
    .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3)
    .with_randomized_stats()
    .with_hero_class(HeroClass.WARRIOR)
    .with_race_skills("hero")
    .with_class_skills(HeroClass.WARRIOR, level=1)
    .with_inventory(max_slots=20, max_weight=100, weapon="iron_sword")
    .with_starting_items(["small_hp_potion"] * 3)
    .with_home_storage(max_slots=30)
    .with_traits(race_prefix="hero")
    .build()
)
```

### Key Methods

| Category | Methods |
|----------|---------|
| **Identity** | `kind()`, `at()`, `home()`, `ai_state()`, `faction()`, `tier()` |
| **Stats** | `with_base_stats()`, `with_randomized_stats()` |
| **Attributes** | `with_hero_class()`, `with_mob_attributes()`, `with_race_attributes()` |
| **Skills** | `with_race_skills()`, `with_class_skills()` |
| **Inventory** | `with_inventory()`, `with_existing_inventory()`, `with_equipment()`, `with_starting_items()` |
| **Storage** | `with_home_storage()` |
| **Traits** | `with_traits()` |
| **Build** | `build()` → `Entity` (calls `recalc_derived_stats`) |

### Design Decisions

- **Builder over Factory:** Handles combinatorial explosion of optional features without parameter explosion.
- **`with_existing_inventory()`:** Allows generator to build complex inventories externally while still using the builder for everything else.

---

## 4. Trait Aggregation — Typed Dataclasses

**Location:** `src/core/traits.py`

### Pattern

Trait aggregation uses **typed dataclasses** instead of `dict[str, float]` for type safety, autocomplete, and compile-time error detection.

| Dataclass | Purpose | Default Strategy |
|-----------|---------|-----------------|
| `UtilityBonus` | Additive modifiers for goal scoring | All fields start at `0.0` |
| `TraitStatModifiers` | Passive stat modifiers | Multipliers at `1.0`, additive at `0.0` |

### Usage

```python
bonus = aggregate_trait_utility(entity.traits)
score += bonus.combat  # typed access, IDE autocomplete

mods = aggregate_trait_stats(entity.traits)
effective_atk = base_atk * mods.atk_mult
```

### How to Add a New Trait Effect

1. Add the field to the appropriate dataclass
2. Update the aggregation function to sum the new field
3. Add the field to `TraitDef` and populate in trait definitions

---

## 5. AI State Machine — Strategy Pattern

**Location:** `src/ai/states.py`

### Pattern

Each AI state is a `StateHandler` subclass registered in `STATE_HANDLERS`. The `AIBrain` looks up the handler for the entity's current state and delegates execution.

```python
STATE_HANDLERS: dict[AIState, StateHandler] = {
    AIState.IDLE: IdleHandler(),
    AIState.WANDER: WanderHandler(),
    AIState.HUNT: HuntHandler(),
    AIState.COMBAT: CombatHandler(),
    # ... 18 total states
}
```

### How to Add a New AI State

1. Add the enum value in `src/core/enums.py`
2. Create a `StateHandler` subclass in `src/ai/states.py`
3. Register it in `STATE_HANDLERS`
4. (Optional) Create a `GoalScorer` that maps to the new state

---

## 6. Pattern Summary

| Pattern | Location | Open/Closed Principle |
|---------|----------|----------------------|
| **Plugin** (Goal Scorers) | `ai/goals/` | Add goal = add class + register. No existing code modified. |
| **Strategy** (Damage Calc) | `actions/damage.py` | Add damage type = add subclass + register. No if/else. |
| **Strategy** (State Handlers) | `ai/states.py` | Add AI state = add handler + register. |
| **Builder** (Entity) | `core/entity_builder.py` | Fluent API absorbs new features without parameter explosion. |
| **Typed Dataclass** (Traits) | `core/traits.py` | Type-safe aggregation. Add field = add to dataclass + aggregator. |

---

## 7. Metadata API — Shared Schemas

**Location:** `src/core/` (shared models), `src/api/routes/metadata.py` (endpoints), `frontend/src/types/metadata.ts`, `frontend/src/contexts/MetadataContext.tsx`

### Shared Pydantic Dataclasses (Single Source of Truth)

Core game definitions are **pydantic dataclasses** (`pydantic.dataclasses.dataclass`) used by both the engine and the API:

| Model | File | Used By |
|-------|------|---------|
| `ItemTemplate` | `core/items.py` | Game engine (IntEnum fields), API (serializes enums as strings) |
| `SkillDef` | `core/classes.py` | Game engine (skill execution), API (skill metadata) |
| `ClassDef` | `core/classes.py` | Game engine (class assignment), API (class views) |
| `BreakthroughDef` | `core/classes.py` | Game engine (promotion logic), API (breakthrough data) |
| `TraitDef` | `core/traits.py` | Game engine (trait effects), API (trait list) |

Enum fields use `Annotated[EnumType, PlainSerializer(...)]` so they remain IntEnums at runtime but serialize as lowercase strings (e.g., `ItemType.WEAPON` → `"weapon"`).

Mutable runtime types (`SkillInstance`, `TreasureChest`, `Building`, etc.) stay as stdlib `dataclass`.

### Endpoints

| Endpoint | Returns | Backend Source |
|----------|---------|---------------|
| `GET /metadata/enums` | Materials, AI states, tiers, rarities, item types, damage types, elements, entity roles, factions, entity kinds | `core/enums.py`, `core/faction.py` |
| `GET /metadata/items` | All item templates — serialized directly from core `ItemTemplate` | `core/items.py` → `ITEM_REGISTRY` |
| `GET /metadata/classes` | Class views, skills, breakthroughs, scaling grades, mastery tiers, race skills | `core/classes.py` |
| `GET /metadata/traits` | All trait defs — serialized directly from core `TraitDef` | `core/traits.py` → `TRAIT_DEFS` |
| `GET /metadata/attributes` | Attribute keys, labels, descriptions | Defined in route (9 core attributes) |
| `GET /metadata/buildings` | Building type names and descriptions | Defined in route |
| `GET /metadata/resources` | Resource node types per terrain | `core/resource_nodes.py` → `TERRAIN_RESOURCES` |
| `GET /metadata/recipes` | Crafting recipes with materials and output | `core/buildings.py` → `RECIPES` |

### Frontend Architecture

```
MetadataProvider (wraps App)
  └─ fetches all 8 endpoints in parallel on mount
  └─ builds derived lookup maps (itemMap, classMap, traitMap, etc.)
  └─ provides GameMetadata via React context

useMetadata() hook
  └─ used by InspectPanel, ClassHallPanel, BuildingPanel, LootPanel, etc.
  └─ returns typed GameMetadata with both raw data and lookup maps
```

### How to Add New Metadata

1. Define the pydantic dataclass in `src/core/` with `Annotated` serializers for any enum fields
2. Add a thin endpoint in `src/api/routes/metadata.py` that serializes via `TypeAdapter`
3. Add the TypeScript type in `frontend/src/types/metadata.ts`
4. Add the fetch call in `MetadataContext.tsx` and extend `GameMetadata`
5. Use `useMetadata()` in components that need the data

### Design Decisions

- **Shared schemas** — core pydantic dataclasses are the single source of truth for both engine and API
- **Annotated enum serializers** — `Annotated[ItemType, PlainSerializer(...)]` keeps IntEnum for game logic, strings for JSON
- **Colors stay in frontend** — visual presentation is a UI concern, not game data
- **Multiple small endpoints** — each endpoint is independently cacheable and focused
- **Derived lookup maps** — `itemMap`, `classMap`, `traitMap` etc. are built once on load for O(1) access

---

## 8. File Map (Refactored Modules)

```
src/
├── core/
│   ├── entity_builder.py     # Builder pattern — fluent Entity construction
│   ├── traits.py             # TraitDef, UtilityBonus, TraitStatModifiers
│   ├── classes.py            # ClassDef, SkillDef, BreakthroughDef, registries
│   ├── items.py              # ItemTemplate, ITEM_REGISTRY
│   ├── buildings.py          # Recipe, RECIPES, building logic
│   ├── resource_nodes.py     # TERRAIN_RESOURCES
│   ├── faction.py            # Faction enum, FactionRegistry
│   └── enums.py              # DamageType, Element, TraitType, AIState
├── api/
│   └── routes/
│       ├── metadata.py       # 8 metadata endpoints (Pydantic schemas + handlers)
│       └── __init__.py       # Router registration (includes metadata_router)
├── actions/
│   ├── combat.py             # CombatAction (uses DamageCalculator strategy)
│   └── damage.py             # DamageCalculator ABC + subclasses + registry
├── ai/
│   ├── brain.py              # AIBrain (hybrid: GoalEvaluator + StateHandler)
│   ├── goal_evaluator.py     # Backward-compat shim → ai/goals/
│   └── goals/
│       ├── __init__.py       # Package init, auto-registers all goals
│       ├── base.py           # GoalScorer ABC, GoalScore, GoalEvaluator, GOAL_REGISTRY
│       ├── scorers.py        # 9 built-in GoalScorer subclasses
│       └── registry.py       # register_all_goals() — idempotent registration
└── systems/
    └── generator.py          # EntityGenerator (uses EntityBuilder)

frontend/src/
├── types/
│   ├── api.ts                # Simulation state types (Entity, Building, etc.)
│   └── metadata.ts           # Metadata response types (GameMetadata, ClassEntry, etc.)
├── contexts/
│   └── MetadataContext.tsx    # MetadataProvider + useMetadata() hook
├── constants/
│   └── colors.ts             # Visual-only: tile/kind/state/rarity colors, CELL_SIZE
├── components/
│   ├── InspectPanel.tsx       # Entity inspector (uses useMetadata for items/classes/traits)
│   ├── ClassHallPanel.tsx     # Class browser (uses useMetadata for class/skill data)
│   ├── BuildingPanel.tsx      # Building details (uses useMetadata for items/recipes)
│   └── LootPanel.tsx          # Loot display (uses useMetadata for item info)
└── hooks/
    └── useCanvas.ts           # Canvas rendering (visual colors only)
```

---

# entities_and_factions

# Entities & Factions

Technical documentation for the entity model, faction system, races, tiers, territory intrusion, and status effects.

---

## Overview

Every agent in the simulation is an `Entity`. Each entity belongs to exactly one **Faction**. Factions define inter-group relationships (hostile, neutral, allied) and territory ownership. The system is **data-driven** — adding new factions or races requires only registry configuration, not code changes in AI, combat, or movement logic.

**Primary files:** `src/core/models.py`, `src/core/faction.py`, `src/core/effects.py`, `src/core/enums.py`, `src/systems/generator.py`

---

## Entity Model (`src/core/models.py`)

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique, monotonic, never reused |
| `kind` | str | Type name (e.g. "hero", "goblin", "wolf") |
| `pos` | Vector2 | Current grid position |
| `stats` | Stats | HP, ATK, DEF, SPD, level, gold, stamina, etc. |
| `ai_state` | AIState | Current FSM state |
| `next_act_at` | float | Absolute time this entity can act again |
| `alive` | bool | Gate for scheduling |
| `faction` | Faction | Which faction this entity belongs to |
| `tier` | int | Enemy difficulty tier (0–3) |
| `home_pos` | Vector2 \| None | Spawn/respawn position |

### Extended Fields

| Field | Type | Description |
|-------|------|-------------|
| `inventory` | Inventory \| None | Items carried + equipment slots |
| `home_storage` | HomeStorage \| None | Hero's persistent home storage |
| `attributes` | Attributes \| None | 9 primary attributes (STR, AGI, etc.) |
| `attribute_caps` | AttributeCaps \| None | Attribute growth limits |
| `hero_class` | int | HeroClass enum value (0=NONE) |
| `skills` | list[SkillInstance] | Learned skills with runtime state |
| `class_mastery` | float | 0.0–100.0 |
| `effects` | list[StatusEffect] | Active buffs/debuffs |
| `traits` | list[TraitType] | Personality traits (2–4 per entity) |
| `quests` | list[Quest] | Tracked quests (hero only) |
| `known_recipes` | list[str] | Recipe IDs learned from blacksmith |
| `craft_target` | str \| None | Current crafting goal |
| `terrain_memory` | set[tuple] | Explored tile positions |
| `entity_memory` | dict | Last-seen positions of other entities |
| `vision_range` | int | Perception radius (Manhattan distance) |
| `engaged_ticks` | int | Consecutive ticks adjacent to a hostile |

### Effective Stat Methods

Equipment bonuses and status effects flow through `effective_*()` methods:

```python
entity.effective_atk()       # base + equipment + effects
entity.effective_def()
entity.effective_spd()
entity.effective_max_hp()
entity.effective_crit_rate()
entity.effective_evasion()
entity.effective_matk()      # magical attack
entity.effective_mdef()      # magical defense
```

### EntityRole

| Role | Value | Description |
|------|-------|-------------|
| HERO | 0 | Can use town buildings, AI goal-driven |
| MOB | 1 | Wild creature/enemy, guards territory |
| NPC | 2 | Town resident (future) |

---

## Faction System (`src/core/faction.py`)

### Faction Identity

| Faction | Value | Territory Tile |
|---------|-------|---------------|
| HERO_GUILD | 0 | TOWN |
| GOBLIN_HORDE | 1 | CAMP |
| WOLF_PACK | 2 | FOREST |
| BANDIT_CLAN | 3 | DESERT |
| UNDEAD | 4 | SWAMP |
| ORC_TRIBE | 5 | MOUNTAIN |
| CENTAUR_HERD | 6 | GRASSLAND |
| FROST_KIN | 7 | SNOW |
| LIZARDFOLK | 8 | JUNGLE |
| DEMON_HORDE | 9 | VOLCANIC |

### Faction Relations

| Relation | Value | Behavior |
|----------|-------|----------|
| ALLIED | 0 | Will not attack; may cooperate |
| NEUTRAL | 1 | Ignore each other (unless provoked) |
| HOSTILE | 2 | Attack on sight |

**Default relations:** All factions are HOSTILE to every other faction. Same-faction entities are implicitly ALLIED.

### FactionRegistry

Data-driven registry that maps factions to territories and relations. Queried at runtime:

```python
reg = FactionRegistry.default()
reg.is_hostile(Faction.HERO_GUILD, Faction.GOBLIN_HORDE)  # True
reg.is_allied(Faction.HERO_GUILD, Faction.HERO_GUILD)     # True
reg.owns_tile(Faction.WOLF_PACK, Material.FOREST)         # True
reg.tile_owner(Material.CAMP)                              # Faction.GOBLIN_HORDE
reg.is_enemy_territory(Faction.HERO_GUILD, Material.CAMP)  # True
```

Entity `kind` strings are registered to factions:

| Kind | Faction |
|------|---------|
| `hero` | HERO_GUILD |
| `goblin`, `goblin_scout`, `goblin_warrior`, `goblin_chief` | GOBLIN_HORDE |
| `wolf`, `dire_wolf`, `alpha_wolf` | WOLF_PACK |
| `bandit`, `bandit_archer`, `bandit_chief` | BANDIT_CLAN |
| `skeleton`, `zombie`, `lich` | UNDEAD |
| `orc`, `orc_warrior`, `orc_warlord` | ORC_TRIBE |
| `centaur`, `centaur_warrior`, `centaur_chief` | CENTAUR_HERD |
| `frost_wolf`, `frost_giant`, `frost_shaman` | FROST_KIN |
| `lizard`, `lizard_warrior`, `lizard_chief` | LIZARDFOLK |
| `imp`, `hellhound`, `demon_lord` | DEMON_HORDE |

---

## Territory System

Each faction owns a tile type via `TerritoryInfo`:

| Field | Type | Description |
|-------|------|-------------|
| `tile` | Material | The territory tile type |
| `atk_debuff` | float | Multiplier on intruder ATK (e.g. 0.7 = 30% reduction) |
| `def_debuff` | float | Multiplier on intruder DEF |
| `spd_debuff` | float | Multiplier on intruder SPD |
| `alert_radius` | int | How far intrusion alerts propagate |

### Default Territory Debuffs

| Faction | Tile | ATK Debuff | DEF Debuff | SPD Debuff | Alert Radius |
|---------|------|-----------|-----------|-----------|-------------|
| HERO_GUILD | TOWN | 0.6× | 0.6× | 0.8× | 6 |
| GOBLIN_HORDE | CAMP | 0.7× | 0.7× | 0.85× | 6 |
| WOLF_PACK | FOREST | 0.7× | 0.7× | 0.85× | 6 |
| BANDIT_CLAN | DESERT | 0.7× | 0.7× | 0.85× | 6 |
| UNDEAD | SWAMP | 0.7× | 0.7× | 0.85× | 6 |
| ORC_TRIBE | MOUNTAIN | 0.7× | 0.7× | 0.85× | 6 |
| CENTAUR_HERD | GRASSLAND | 0.7× | 0.7× | 0.85× | 6 |
| FROST_KIN | SNOW | 0.7× | 0.7× | 0.85× | 6 |
| LIZARDFOLK | JUNGLE | 0.7× | 0.7× | 0.85× | 6 |
| DEMON_HORDE | VOLCANIC | 0.7× | 0.7× | 0.85× | 6 |

### Territory Intrusion

When an entity steps on hostile territory, `WorldLoop._process_territory_effects()` triggers:

1. **Stat Debuff** — `TERRITORY_DEBUFF` StatusEffect applied, refreshed each tick while on hostile tile, removed when entity leaves. Duration: `territory_debuff_duration` (3 ticks).

2. **Alert Propagation** — Same-faction defenders within `alert_radius` switch to `AIState.ALERT`, then seek and engage the intruder.

3. **Town Aura Damage** — Hostile entities on TOWN tiles lose `town_aura_damage` (2) HP/tick.

---

## Status Effect System (`src/core/effects.py`)

Generic system for temporary stat modifiers tracked on each entity.

### StatusEffect Fields

| Field | Type | Description |
|-------|------|-------------|
| `effect_type` | EffectType | Category |
| `remaining_ticks` | int | Duration; -1 = permanent, 0 = expired |
| `source` | str | Human-readable origin |
| `atk_mult` | float | ATK multiplier (1.0 = neutral) |
| `def_mult` | float | DEF multiplier |
| `spd_mult` | float | SPD multiplier |
| `crit_mult` | float | Crit rate multiplier |
| `evasion_mult` | float | Evasion multiplier |
| `hp_per_tick` | int | Flat HP change/tick (+regen, −DoT) |

### EffectType Enum

| Type | Value | Usage |
|------|-------|-------|
| TERRITORY_DEBUFF | 0 | Stat penalty for hostile territory |
| TERRITORY_BUFF | 1 | Stat bonus for home territory |
| POISON | 2 | DoT |
| BERSERK | 3 | ATK up, DEF down |
| SHIELD | 4 | Temporary DEF boost |
| HASTE | 5 | SPD boost |
| SLOW | 6 | SPD penalty |
| SKILL_BUFF | 7 | Buff from skill use |
| SKILL_DEBUFF | 8 | Debuff from enemy skill |

### Effect Lifecycle

1. **Applied:** Territory effects refreshed each tick; skill effects applied on use
2. **Ticked:** `remaining_ticks` decremented each tick, `hp_per_tick` applied
3. **Expired:** Effects with `remaining_ticks < 0` pruned automatically
4. **Queried:** `Entity.effective_*()` methods aggregate all active multipliers (multiplicative stacking)

---

## Races & Tiers

### Enemy Tiers

| Tier | Enum | Spawn Weight | Start Level |
|------|------|-------------|-------------|
| BASIC | 0 | 55% | 1 |
| SCOUT | 1 | 25% | 2 |
| WARRIOR | 2 | 15% | 3 |
| ELITE | 3 | 5% | 5 |

### Tier Stat Multipliers (Goblin Base)

| Tier | Kind | HP Mult | ATK Mult | Base DEF | SPD Mod |
|------|------|---------|----------|----------|---------|
| BASIC | `goblin` | 1.0× | 1.0× | 0 | +0 |
| SCOUT | `goblin_scout` | 0.8× | 0.9× | 0 | +3 |
| WARRIOR | `goblin_warrior` | 1.5× | 1.3× | 3 | -1 |
| ELITE | `goblin_chief` | 2.5× | 1.8× | 6 | +0 |

### Race Variants

Each race has three tier names:

| Race | Basic (T0) | Mid (T1–T2) | Elite (T3) |
|------|-----------|-------------|-----------|
| Goblin | `goblin` | `goblin_scout` / `goblin_warrior` | `goblin_chief` |
| Wolf | `wolf` | `dire_wolf` | `alpha_wolf` |
| Bandit | `bandit` | `bandit_archer` | `bandit_chief` |
| Undead | `skeleton` | `zombie` | `lich` |
| Orc | `orc` | `orc_warrior` | `orc_warlord` |

### Race Stat Modifiers (`RACE_STAT_MODS`)

Applied on top of tier multipliers:

| Race | HP Mult | ATK Mult | DEF Mod | SPD Mod | Crit | Evasion | Luck |
|------|---------|----------|---------|---------|------|---------|------|
| Wolf | 0.8× | 1.0× | +0 | +2 | 10% | 10% | 0 |
| Bandit | 1.0× | 0.9× | +1 | +1 | 8% | 5% | 2 |
| Undead | 1.3× | 0.8× | +3 | -2 | 3% | 0% | 0 |
| Orc | 1.2× | 1.2× | +2 | -1 | 5% | 2% | 1 |

### Spawning

**Goblins:** `EntityGenerator.spawn()` — tier-based stat multipliers, starting gear, loot tables.

**Race mobs:** `EntityGenerator.spawn_race(world, race, tier, near_pos)` — applies race stat mods on top of tier multipliers, picks kind name from `RACE_TIER_KINDS`, equips race-specific gear, sets faction from `RACE_FACTION`.

---

## Hero Spawn

Heroes spawn at town center with:

1. Random class assignment (Warrior/Ranger/Mage/Rogue)
2. Attributes: base 5 + class bonuses + small random variance (0–2)
3. Attribute caps: 15 + class cap bonuses
4. Stamina: 50 + END×2
5. Race skills (Rally, Second Wind) + first class skill
6. Starting gear: `iron_sword`, `leather_vest`, 3× `small_hp_potion`
7. Home storage (30 slots)

Uses the `EntityBuilder` fluent API (see `design_patterns.md`).

---

## Extending the System

### Adding a New Faction

```python
# 1. Add to Faction enum
class Faction(IntEnum):
    ...
    NEW_FACTION = 6

# 2. Register in FactionRegistry.default()
reg.set_relation(Faction.NEW_FACTION, Faction.HERO_GUILD, FactionRelation.HOSTILE)
reg.set_territory(Faction.NEW_FACTION, TerritoryInfo(
    tile=Material.NEW_TERRAIN,
    atk_debuff=0.7, def_debuff=0.7, spd_debuff=0.85, alert_radius=6,
))
reg.register_kind("new_mob", Faction.NEW_FACTION)
```

No changes to AI handlers, combat logic, or movement code.

### Adding a New Status Effect

```python
# 1. Add to EffectType enum
# 2. Create a factory function
# 3. Apply in combat or ability code
entity.effects.append(my_effect())
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `territory_debuff_duration` | 3 | Ticks debuff lasts after leaving |
| `territory_alert_radius` | 6 | Intrusion alert propagation range |
| `town_aura_damage` | 2 | HP lost/tick by hostiles in town |
| `town_passive_heal` | 1 | HP regained/tick by heroes in town |
| `hero_heal_per_tick` | 3 | HP regained/tick by resting heroes |

---

# frontend

# Frontend Visualization

Technical documentation for the browser-based simulation viewer.

---

## Overview

The frontend is a **React 19 + TypeScript** single-page application built with **Vite** and styled with **Tailwind CSS v4**. It polls the REST API every ~80ms and renders the simulation state onto layered HTML5 canvases with an interactive sidebar.

The production build is served at `/` by the FastAPI backend from `frontend/dist/`. During development, Vite's dev server proxies API requests to the backend.

**Primary files:** `frontend/src/`

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Build | Vite | Fast HMR, TypeScript, API proxy |
| Framework | React 19 + TypeScript | Component architecture, type safety |
| Styling | Tailwind CSS v4 | Utility-first CSS with custom theme |
| Icons | Lucide React | Lightweight icon set |
| Primitives | Radix UI | Accessible tabs, scroll areas, sliders |
| Canvas | HTML5 Canvas (imperative) | Tile grid + entity rendering via React refs |

---

## Component Tree

```
MetadataProvider              # Wraps App — fetches all 8 /metadata/* endpoints on mount
└── App
    ├── Header                # Status bar + page toggle (Simulation | API Docs)
    ├── [Simulation view]
    │   ├── GameCanvas        # Canvas wrapper + hover tooltip overlay
    │   │   ├── grid-canvas   # Layer 1 (z-index: 1) — static tiles
    │   │   ├── entity-canvas # Layer 2 (z-index: 2) — entities, items, buildings, HP bars
    │   │   ├── overlay-canvas# Layer 3 (z-index: 3) — fog of war, ghost markers
    │   │   ├── minimap-canvas# Top-left minimap with viewport rect + click-to-jump
    │   │   ├── Locations     # Collapsible panel under minimap
    │   │   └── HoverTooltip  # Fixed-position tooltip following cursor
    │   └── Sidebar
    │       ├── ControlPanel  # Always visible (start/pause/resume/step/reset + speed slider)
    │       └── Tabs (context-dependent)
    │           ├── [Default]     # Info (Legend + EntityList) + Events (EventLog)
    │           ├── [Spectating]  # Inspect (InspectPanel — 6 tabs, uses useMetadata)
    │           ├── [Building]    # BuildingPanel / ClassHallPanel (uses useMetadata)
    │           └── [Loot]        # LootPanel (uses useMetadata)
    └── [API Docs view]
        └── ApiDocsPage       # Interactive OpenAPI explorer (fetches /openapi.json)
            ├── Tag sidebar   # Grouped endpoint navigation + search
            └── Endpoint cards# Method badge, path, params, schema, Try It Out
```

---

## Canvas Layers

Three stacked `<canvas>` elements managed via React refs in `useCanvas`:

| Layer | Ref | Z-Index | Resolution | Purpose |
|-------|-----|---------|------------|----------|
| 1 | `gridRef` | 1 | 8192×8192 (full) | Static tile grid (drawn once on init) |
| 2 | `entityRef` | 2 | 8192×8192 (full) | Ground items, resources, entity sprites, HP bars, buildings, selection rings, vision border, weapon range ring, ghost markers (redrawn every poll) |
| 3 | `overlayRef` | 3 | 512×512 (tile-res) | Fog-of-war only — CSS-scaled via `scale(CELL_SIZE × zoom)` with `imageRendering: pixelated` (redrawn on entity move/memory change) |

The overlay uses `pointer-events: none` so clicks pass through.

### Performance Notes

- **Overlay canvas** is 512×512 (1 pixel per tile), **256× smaller** than full resolution. During dragging, the GPU composites a 262K-pixel texture instead of a 67M-pixel texture.
- **Vision border, weapon range ring, and ghost markers** are drawn on the entity canvas (full resolution) instead of the overlay, since they need sub-tile precision.
- **Minimap terrain** is cached to an offscreen `<canvas>` and blitted via `drawImage()` — avoids 262K `fillRect` calls per frame.

### Drag-Skip Optimization

When the user drags (pans) the canvas, all expensive canvas effects are **paused** via `isDraggingRef`. Only the CSS `transform: translate()` updates during drag, which is handled entirely by the GPU compositor at no CPU cost. All effects catch up automatically on the next poll (~80ms) after the mouse is released.

| Effect | Location | Skipped During Drag | Cost if Not Skipped |
|--------|----------|-------------------|---------------------|
| Entity canvas redraw | `useCanvas.ts` | ✅ | ~300 entities + vision border + ghosts on 8192×8192 |
| Fog overlay redraw | `useCanvas.ts` | ✅ | 262K tile iterations on 512×512 |
| Minimap terrain cache | `GameCanvas.tsx` | ✅ | 262K `fillRect` calls (rebuilds when `terrain_memory` grows) |
| Minimap dynamic layer | `GameCanvas.tsx` | ✅ | `drawImage` + entity dots + viewport rect |

**Why this matters:** Without the skip, polling (every 80ms) triggers `setState` → React re-renders → all effects fire. The minimap terrain cache is the worst offender: when spectating a running entity, `terrain_memory` grows each tick as the entity explores, causing a full 262K-tile cache rebuild every 80ms *during* drag.

**Trade-off:** The entity positions, fog overlay, and minimap freeze momentarily while dragging. This is imperceptible since drag typically lasts <1 second, and updates resume within 80ms of release.

---

## Sidebar Layout

Context-dependent tabbed interface. **ControlPanel** always visible above tab bar.

| Context | Tabs | Content |
|---------|------|---------|
| No selection | Info + Events | Legend + entity list; global event log with count + clear button |
| Spectating entity | Inspect (single tab) | 6-tab inspector panel |
| Clicked building | Inspect (building name) | BuildingPanel or ClassHallPanel |
| Clicked loot | Inspect ("Loot") | LootPanel with item details |

---

## Inspect Panel (6 Tabs)

When spectating an entity:

### Stats Tab
- **Header** — HP/stamina bars, ATK/DEF/MATK/MDEF/SPD/Gold in colored grid
- **Attributes** — 9-stat grid with caps/bars, hover tooltips showing full name, scaling, training progress
- **Detailed Stats** — base + equipment + buff breakdown
- **Equipment** — weapon, armor, accessory slots with item tooltips
- **Inventory** — bag items as small bordered tags with hover tooltips

### Class Tab
- Class info, skills with damage type (PHY/MAG) and element badges, mastery bars

### Quests Tab
- Title, type badge, progress bar, gold/XP reward, completion checkmark

### Events Tab
- Timestamped event history filtered to spectated entity, category color-coded

### Effects Tab
- Active buffs/debuffs with stat modifier badges, HP per tick, remaining duration

### AI Tab
- Current AI state with description
- Personality traits with colors/descriptions
- Utility AI goals explanation
- Craft target
- Memory & vision info

### Item Tooltips

Both equipment slots and inventory items use `ItemWithTooltip`. Hover shows:
- Item name (color-coded by rarity)
- Type and rarity
- Stat bonuses (ATK, DEF, SPD, CRIT, EVA, LUCK, max HP, MATK, MDEF)
- Consumable effects (heal amount, gold value)

Rarity colors: Common (`#9ca3af`), Uncommon (`#34d399`), Rare (`#a78bfa`).

---

## Vision Overlay (Fog of War)

When spectating, the overlay canvas (512×512, 1px/tile) draws three fog levels:

| State | Overlay Fill | Effective Brightness | Description |
|-------|-------------|---------------------|-------------|
| **In vision** | Clear (no fill) | 100% | Within current vision range |
| **Explored (fog)** | `rgba(0, 0, 0, 0.5)` | ~50% | Previously seen, in `terrain_memory` |
| **Unseen** | `rgba(0, 0, 0, 1.0)` | 0% (fully black) | Never explored — completely hidden |

The overlay is drawn at tile resolution and CSS-scaled with `imageRendering: pixelated` for crisp tile edges.

### Overlay Key Caching

The fog is only redrawn when the entity moves or memory changes. A memoized `overlayKey` string (`id_x_y_memSize_emSize`) is compared to avoid expensive 262K-tile iterations.

### Vision Range Border
Faint blue outline (`rgba(74, 158, 255, 0.3)`) around visible area edges. Drawn on the **entity canvas** (full resolution) for sub-tile precision.

### Weapon Range Ring
Colored outline around weapon range area. Orange for ranged (`weapon_range > 1`), red for melee. Drawn on the **entity canvas**.

### Ghost Entity Markers
Remembered entities from `entity_memory` drawn as ghosts on the **entity canvas**:
- Skip if currently visible or if remembered position is in vision cone
- Skip if position unexplored
- Render: semi-transparent circle, dashed border, `?` label

---

## Minimap

### Features
- **Size:** `MINIMAP_SCALE = 2` px/tile, default 180×180 px container
- **Resizable:** Drag bottom-right handle (80–400 px range)
- **Separate zoom:** Scroll over minimap zooms minimap (1×–5×); scroll over world zooms world (0.5×–3×)
- **Click to jump:** Click anywhere on minimap moves world camera
- **Spectate filtering:** When spectating, entities/resources outside vision hidden on minimap
- **Terrain caching:** Terrain tiles cached to an offscreen canvas (`mmTerrainCacheRef`) — only rebuilt when `terrain_memory` size changes. Dynamic elements (entity dots, viewport rect) blit the cache via `drawImage()` then overdraw.

### Minimap Fog of War

When spectating, minimap terrain uses three levels matching the main canvas:

| State | Color | Description |
|-------|-------|-------------|
| **Unseen** | `#000000` | Completely black |
| **Explored** | `TILE_COLORS_DIM[tile]` | Dimmed tile color |
| **In vision** | `TILE_COLORS[tile]` | Full brightness (bright overlay drawn per frame) |

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MINIMAP_SCALE` | 2 | Pixels per tile |
| `MM_DEFAULT_W/H` | 180 | Default container size (px) |
| `MM_MIN_SIZE` / `MM_MAX_SIZE` | 80 / 400 | Resize bounds |
| `MM_MIN_ZOOM` / `MM_MAX_ZOOM` | 1.0 / 5.0 | Minimap zoom range |
| `MIN_ZOOM` / `MAX_ZOOM` | 0.5 / 3.0 | World zoom range |

### Locations Panel

Collapsible panel under minimap showing:
- **Buildings:** Store, Blacksmith, Guild, Class Hall, Inn — with position and color
- **Tile clusters:** Camps, Sanctuaries, Ruins, Dungeons — detected via flood-fill with centroid coordinates
- Click any entry to jump camera

---

## Entity Rendering

### Hero
- **Shape:** Diamond (rotated square)
- **Glow:** Golden shadow blur (`#fbbf24`, 6px)
- **State border:** Colored outline matching AI state
- **ID label:** Bold white monospace

### Mobs
- **Shape:** Circle (`CELL_SIZE * 0.35` radius)
- **Color:** Kind-specific from `KIND_COLORS`
- **State border:** Colored ring matching AI state
- **ID label:** Semi-transparent white monospace

### Buildings
- **Shape:** Colored square markers with letter labels
- **Store:** S (blue), **Blacksmith:** B (amber), **Guild:** G (purple), **Class Hall:** C (violet), **Inn:** I (orange)
- Also appear as colored dots on minimap

### Ground Items
- **Shape:** Small diamond (rotated square, `CELL_SIZE * 0.28`)
- **Color:** Lime green (`#a3e635`) with glow
- **Badge:** White count badge if multiple items on tile

### Resource Nodes
- **Available:** 50% opacity fill + 1px border in resource-type color
- **Depleted:** Grey (`#4a5568`) at 30% opacity

### Selection Ring
- White dashed circle (`CELL_SIZE * 0.55` radius)

### HP Bars
- 2px tall bar above each entity
- Green (>50%) → Yellow (>25%) → Red (<25%)

---

## Tile Hover Tooltip (epic-09 F10)

Hovering any tile shows a multi-line tooltip with **all** information on that tile. No early-return — every layer is collected and displayed.

### Tooltip Lines

| Icon | Category | Content |
|------|----------|--------|
| 🗺 | **Terrain** | Tile type name + grid coordinates, always shown |
| ⚔ | **Entities** | All entities on tile: `#id kind Lv# (class) \| HP \| STA \| state` |
| 👻 | **Ghosts** | Remembered entities in fog: id, kind, level, ATK, HP, last-seen tick |
| 🏛 | **Buildings** | Building name |
| 💎 | **Loot** | Item name or bag count |
| 🌿 | **Resources** | Node name, remaining/max harvests, yields item |

### Implementation

- `TILE_NAMES` map in `src/constants/colors.ts` — maps `Material` enum values (0–22) to display names
- `handleCanvasHover` in `useCanvas.ts` collects all lines, joins with `\n`
- Tooltip rendered with `whitespace-pre-line max-w-xs` in `GameCanvas.tsx`
- Fog-of-war respected: entities/loot/resources hidden outside vision when spectating

---

## Color Palette

All colors in `src/constants/colors.ts` and Tailwind theme in `src/index.css`.

### Tile Colors

| Material | Hex |
|----------|-----|
| Floor | `#1a1d27` |
| Wall | `#555b73` |
| Water | `#1e3a5f` |
| Town | `#2d4a3e` |
| Camp | `#4a2d2d` |
| Sanctuary | `#2d3a4a` |
| Forest | `#1b3a1b` |
| Desert | `#3a3420` |
| Swamp | `#2a2a3a` |
| Mountain | `#3a3a3a` |
| Road | `#5a5040` |
| Bridge | `#4a6050` |
| Ruins | `#4a4035` |
| Dungeon | `#6a3040` |
| Lava | `#8a3000` |
| Grassland | `#4a6030` |
| Snow | `#c8d8e8` |
| Jungle | `#0a4a0a` |
| Shallow Water | `#2a5070` |
| Farmland | `#6a7a40` |
| Cave | `#3a3040` |
| Volcanic | `#5a2a1a` |
| Graveyard | `#4a4050` |

### Entity Colors (by kind)

| Kind | Hex |
|------|-----|
| Hero | `#4a9eff` |
| Goblin | `#f87171` |
| Goblin Scout | `#fb923c` |
| Goblin Warrior | `#dc2626` |
| Goblin Chief | `#fbbf24` |
| Wolf | `#a0a0a0` |
| Dire Wolf | `#808080` |
| Alpha Wolf | `#c0c0c0` |
| Bandit | `#e0a050` |
| Bandit Archer | `#d4943c` |
| Bandit Chief | `#f0c060` |
| Skeleton | `#b0b8c0` |
| Zombie | `#70a070` |
| Lich | `#c080ff` |
| Orc | `#60a060` |
| Orc Warrior | `#408040` |
| Orc Warlord | `#80c040` |
| Centaur | `#b0a060` |
| Centaur Lancer | `#c0b070` |
| Centaur Elder | `#d0c080` |
| Frost Wolf | `#90b0d0` |
| Frost Giant | `#7090b0` |
| Frost Shaman | `#a0c0e0` |
| Imp | `#e06040` |
| Hellhound | `#c04020` |
| Demon Lord | `#ff5030` |
| Lizard | `#40a080` |
| Lizard Warrior | `#308060` |
| Lizard Chief | `#50c0a0` |

### AI State Colors

| State | Hex |
|-------|-----|
| IDLE | `#8b8fa8` |
| WANDER | `#34d399` |
| HUNT | `#fbbf24` |
| COMBAT | `#f87171` |
| FLEE | `#a78bfa` |
| RETURN_TO_TOWN | `#60a5fa` |
| RESTING_IN_TOWN | `#22d3ee` |
| RETURN_TO_CAMP | `#f97316` |
| GUARD_CAMP | `#ef4444` |
| LOOTING | `#a3e635` |
| ALERT | `#ff6b6b` |
| VISIT_SHOP | `#38bdf8` |
| VISIT_BLACKSMITH | `#f59e0b` |
| VISIT_GUILD | `#818cf8` |
| HARVESTING | `#7dd3a0` |
| VISIT_CLASS_HALL | `#c084fc` |
| VISIT_INN | `#fb923c` |

---

## Key Hooks & Contexts

### `MetadataProvider` / `useMetadata()`

**File:** `src/contexts/MetadataContext.tsx`

Fetches all 8 `/api/v1/metadata/*` endpoints in parallel on mount. Builds derived lookup maps for O(1) access. Wraps the entire `App` in `main.tsx`.

**Provided data:**
- Raw data: `enums`, `items`, `classes`, `traits`, `attributes`, `buildings`, `resources`, `recipes`
- Lookup maps: `itemMap`, `traitMap`, `skillMap`, `classMap`, `aiStateMap`, `buildingTypeMap`
- Attribute helpers: `attrKeys`, `attrLabels`

**Used by:** `InspectPanel`, `ClassHallPanel`, `BuildingPanel`, `LootPanel`

### `useSimulation`

Central state management with payload-optimized data fetching:

**One-time loads (on mount):**
- `GET /map` — RLE-compressed grid decoded via `decodeRLE()` into `DecodedMapData` (`grid: number[][]`)
- `GET /static` — buildings, resource nodes, treasure chests, regions

**Polling (every 80ms via `setTimeout`):**
- `GET /state?since_tick=N&selected=ID` — slim entities + optional full selected entity
- `GET /stats` — simulation counters

**State exposed:**
- `mapData: DecodedMapData | null` — decoded 2D grid
- `entities: EntitySlim[]` — all alive entities (slim ~200 B each)
- `selectedEntity: Entity | null` — full entity for inspected entity (includes terrain_memory, entity_memory, skills, etc.)
- `buildings`, `resourceNodes`, `regions` — static data (fetched once)
- `events`, `groundItems`, `tick`, `status`, `aliveCount`, etc.

**Callbacks:** `sendControl(action)`, `setSpeed(tps)`, `selectEntity(id)`, `clearEvents()`

**Key implementation details:**
- `selectedIdRef` synced **immediately** in `selectEntity()` callback (not via `useEffect`) so the very next poll includes `?selected=`
- `selectedEntity` updates tracked via `lastSelKeyRef` (`responseEntityId_tick`) — skips redundant `setState` calls when data hasn't changed
- `entities` / `groundItems` only update when tick advances (`lastTickRef`) — eliminates re-renders when paused or polling within the same tick
- Simulation status (`running`/`paused`/`stopped`) always updates regardless of tick

### `useCanvas`

Canvas rendering — accepts `EntitySlim[]` for all entities and `Entity | null` for the full selected entity:
- **Grid canvas:** Draws tile grid once when `DecodedMapData` arrives (8192×8192)
- **Entity canvas:** Redraws entities/items/resources/buildings every poll cycle, plus vision border, weapon range ring, and ghost markers when spectating
- **Overlay canvas:** Tile-resolution (512×512) fog-of-war only — CSS-scaled to match grid. Redrawn only when `overlayKey` changes (entity position or memory size). Three levels: unseen=opaque black, explored=50% dim, visible=clear
- **Spectate vision filtering:** When `selectedEntityId` is set but `selectedEntity` is null (data pending), entity canvas uses empty `visibleSet` (hides everything) and overlay shows full fog
- Hover detection: resolves grid cell, collects ALL info (terrain + entities + buildings + loot + resources) into multi-line tooltip. Shows class/stamina from full entity for selected entity only.
- Zoom-corrected coordinates for click and hover

---

## API Documentation Page

**File:** `src/components/ApiDocsPage.tsx`

An interactive API explorer accessible via the "API Docs" button in the header. Fetches `/openapi.json` from FastAPI and renders a custom UI.

### Features

- **Tag-grouped sidebar** — endpoints grouped by tag (State, Map, Control, Config, Metadata) with search
- **Endpoint cards** — expandable cards with method badge (color-coded), path, description
- **Parameter table** — name, location (path/query), type, required flag
- **Schema viewer** — request body and response schema rendered as typed pseudocode with copy button
- **Try It Out** — interactive request builder: fill parameters, edit body JSON, send real requests, view formatted response with status and timing
- **External links** — links to Swagger UI (`/docs`) and ReDoc (`/redoc`) in the sidebar footer

### Navigation

The `Header` component provides a page toggle between `Simulation` and `API Docs` views. The active page is stored in `App` state as `PageView` (`'simulation' | 'api-docs'`).

---

## Data Flow

```
── ONE-TIME LOADS (on mount) ──────────────────────────────────────────

Backend → /map (RLE grid)   → decodeRLE() → DecodedMapData (grid[][])
Backend → /static           → buildings, resourceNodes, regions
Backend → /metadata/*       → MetadataProvider (itemMap, classMap, ...)
Backend → /openapi.json     → ApiDocsPage (endpoint cards + Try It Out)

── POLLING (every 80ms) ───────────────────────────────────────────────

Backend (WorldLoop) → Snapshot → /state?selected=ID → useSimulation()
                                                          ↓
                                        entities: EntitySlim[]     (~75 KB)
                                        selectedEntity: Entity     (~3 KB)
                                        events, groundItems
                                           ↓              ↓               ↓
                                    useCanvas()    InspectPanel       EventLog
                                  (3 canvas +      (full entity       (React
                                   hover tooltip)   with memory)       component)

── CONTEXT CONSUMERS ──────────────────────────────────────────────────

MetadataProvider → GameMetadata context
                     ↓              ↓                ↓
              InspectPanel   ClassHallPanel    BuildingPanel
```

---

## Type Safety

Two type definition files:

### `src/types/api.ts` — Simulation State

Matches Pydantic schemas for dynamic runtime data:
- `EntitySlim` — minimal entity for rendering (id, kind, x, y, hp, max_hp, state, level, tier, faction, weapon_range, combat_target_id, loot_progress, loot_duration)
- `Entity` — full entity with stats, equipment, memory, goals, skills, traits, quests (only for selected entity)
- `Building` — building_id, name, x, y, building_type
- `GameEvent` — tick + category + message
- `GroundItem` — x, y, items[]
- `ResourceNode` — node_id, resource_type, name, position, yields_item, remaining, is_available
- `WorldState` — tick, alive_count, entities: EntitySlim[], selected_entity: Entity | null, events[], ground_items[]
- `StaticData` — buildings[], resource_nodes[], treasure_chests[], regions[]
- `SimulationStats` — counters + running/paused flags
- `MapData` — width, height, grid: number[] (RLE-encoded flat array)

### `src/hooks/useSimulation.ts` — Decoded Types

- `DecodedMapData` — width, height, grid: number[][] (decoded from RLE on load)

### `src/types/metadata.ts` — Game Definitions

Mirrors core pydantic dataclass schemas (the single source of truth):
- `ItemEntry` — mirrors `ItemTemplate` (item_type/rarity/damage_type/element as strings)
- `SkillDefEntry` — mirrors `SkillDef` (skill_type/target/class_req as strings)
- `ClassEntry` — mirrors `ClassView` (grouped attr_bonuses, scaling, breakthrough)
- `TraitEntry` — mirrors `TraitDef` (trait_type as number, all utility/stat fields)
- `GameMetadata` — aggregated type with raw data + derived lookup maps

---

## Development

### Dev Server

```bash
cd frontend
npm install
npm run dev          # Starts Vite on http://localhost:5173
```

Vite proxies `/api/*`, `/openapi.json`, `/docs`, and `/redoc` to `http://127.0.0.1:8000`.

### Production Build

```bash
cd frontend
npm run build        # Outputs to frontend/dist/
```

FastAPI serves `frontend/dist/` at `/`.

---

# items_and_inventory

# Items & Inventory

Technical documentation for item templates, inventory management, equipment, loot tables, home storage, and auto-equip mechanics.

---

## Overview

Every entity can carry an `Inventory` containing items, with three dedicated equipment slots (weapon, armor, accessory). Items provide stat bonuses when equipped and consumable effects when used. Heroes also have persistent `HomeStorage` at their home position.

**Primary files:** `src/core/items.py`, `src/core/models.py`

---

## 1. Item Templates

All items are defined as `ItemTemplate` dataclass instances registered in the global `ITEM_REGISTRY` dictionary.

### ItemTemplate Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier (e.g. `iron_sword`) |
| `name` | str | Display name |
| `item_type` | ItemType | WEAPON, ARMOR, ACCESSORY, CONSUMABLE, MATERIAL |
| `rarity` | Rarity | COMMON, UNCOMMON, RARE |
| `weight` | float | Weight units consumed in inventory |
| `atk_bonus` | int | ATK bonus when equipped |
| `def_bonus` | int | DEF bonus when equipped |
| `spd_bonus` | int | SPD bonus when equipped |
| `max_hp_bonus` | int | Max HP bonus when equipped |
| `matk_bonus` | int | MATK bonus when equipped |
| `mdef_bonus` | int | MDEF bonus when equipped |
| `crit_rate_bonus` | float | Crit rate bonus when equipped |
| `evasion_bonus` | float | Evasion bonus when equipped |
| `heal_amount` | int | HP restored on use (consumables) |
| `sell_value` | int | Gold received when selling |
| `damage_type` | DamageType | PHYSICAL or MAGICAL (weapons) |
| `element` | Element | Elemental tag (weapons/skills) |

---

## 2. Registered Items

### Weapons

| ID | Name | ATK | SPD | Crit | MATK | Type | Rarity |
|----|------|-----|-----|------|------|------|--------|
| `rusty_dagger` | Rusty Dagger | +2 | +1 | +2% | — | PHY | Common |
| `wooden_club` | Wooden Club | +3 | 0 | — | — | PHY | Common |
| `iron_sword` | Iron Sword | +5 | 0 | +3% | — | PHY | Common |
| `goblin_blade` | Goblin Blade | +3 | +2 | +5% | — | PHY | Common |
| `chief_axe` | Chief's Axe | +8 | -1 | +5% | — | PHY | Uncommon |
| `bandit_dagger` | Bandit Dagger | +3 | +2 | — | — | PHY | Common |
| `bandit_bow` | Bandit Bow | +5 | 0 | +5% | — | PHY | Uncommon |
| `orc_axe` | Orc Axe | +7 | -1 | — | — | PHY | Uncommon |
| `steel_sword` | Steel Sword | +7 | 0 | +4% | — | PHY | Uncommon |
| `battle_axe` | Battle Axe | +9 | -1 | +3% | — | PHY | Rare |
| `enchanted_blade` | Enchanted Blade | +11 | 0 | +6% | — | PHY | Rare |
| `apprentice_staff` | Apprentice Staff | — | 0 | — | +4 | MAG | Common |
| `fire_staff` | Fire Staff | — | 0 | — | +7 | MAG/Fire | Uncommon |
| `spectral_blade` | Spectral Blade | +9 | 0 | +8% | — | PHY | Rare |
| `desert_bow` | Desert Composite Bow | +6 | +1 | +6% | — | PHY | Uncommon |

### Armor

| ID | Name | DEF | HP | Evasion | MDEF | Rarity |
|----|------|-----|----|---------|------|--------|
| `leather_vest` | Leather Vest | +3 | +5 | — | — | Common |
| `chainmail` | Chainmail | +6 | +10 | — | — | Uncommon |
| `goblin_shield` | Goblin Shield | +2 | — | +3% | — | Common |
| `chief_plate` | Chief's Plate | +10 | +20 | — | — | Uncommon |
| `orc_shield` | Orc Shield | +5 | — | — | — | Uncommon |
| `iron_plate` | Iron Plate | +8 | +15 | — | — | Uncommon |
| `enchanted_robe` | Enchanted Robe | +4 | +10 | — | +5 | Rare |
| `wolf_cloak` | Wolf Cloak | +3 | — | +4% | — | Uncommon |
| `bone_shield` | Bone Shield | +5 | +10 | — | — | Uncommon |
| `mountain_plate` | Mountain Plate | +7 | +15 | — | — | Rare |
| `cloth_robe` | Cloth Robe | +2 | +5 | — | +3 | Common |
| `silk_robe` | Silk Robe | +3 | +8 | — | +5 | Uncommon |

### Accessories

| ID | Name | Bonuses | Rarity |
|----|------|---------|--------|
| `speed_ring` | Speed Ring | +3 SPD, +2% evasion | Common |
| `lucky_charm` | Lucky Charm | +2 ATK, +5% crit | Common |
| `evasion_amulet` | Evasion Amulet | +5% evasion, +1 SPD | Uncommon |
| `ring_of_power` | Ring of Power | +4 ATK, +3% crit | Rare |
| `fang_necklace` | Fang Necklace | +2 ATK, +8% crit | Uncommon |
| `mana_crystal` | Mana Crystal | +3 MATK | Uncommon |
| `spirit_pendant` | Spirit Pendant | +2 MDEF, +2 MATK | Uncommon |

### Consumables

| ID | Name | Effect | Rarity |
|----|------|--------|--------|
| `small_hp_potion` | Small HP Potion | Heal 20 HP | Common |
| `medium_hp_potion` | Medium HP Potion | Heal 40 HP | Uncommon |
| `large_hp_potion` | Large HP Potion | Heal 80 HP | Rare |
| `herbal_remedy` | Herbal Remedy | Heal 25 HP | Common |
| `wild_berries` | Wild Berries | Heal 8 HP | Common |
| `gold_pouch_s` | Gold Pouch (S) | 10 gold | Common |
| `gold_pouch_m` | Gold Pouch (M) | 25 gold | Uncommon |
| `gold_pouch_l` | Gold Pouch (L) | 50 gold | Rare |

### Materials

| ID | Name | Rarity | Sell Value | Source |
|----|------|--------|------------|--------|
| `wood` | Wood | Common | 5g | Goblins, Timber nodes |
| `leather` | Leather | Common | 8g | Goblins, scouts, wolves |
| `iron_ore` | Iron Ore | Uncommon | 10g | Warriors, ore nodes |
| `steel_bar` | Steel Bar | Uncommon | 15g | Warriors (rare), orcs |
| `enchanted_dust` | Enchanted Dust | Rare | 20g | Elites, liches, crystal nodes |
| `wolf_pelt` | Wolf Pelt | Common | 10g | Wolves |
| `wolf_fang` | Wolf Fang | Uncommon | 14g | Dire wolves, alpha wolves |
| `fiber` | Fiber | Common | 4g | Bandits, cactus fiber |
| `raw_gem` | Raw Gem | Uncommon | 18g | Bandit archers, gem deposits |
| `bone_shard` | Bone Shard | Common | 6g | Skeletons, zombies |
| `ectoplasm` | Ectoplasm | Uncommon | 16g | Zombies, liches |
| `dark_moss` | Dark Moss | Common | 6g | Skeletons, dark moss patches |
| `glowing_mushroom` | Glowing Mushroom | Uncommon | 12g | Zombies, mushroom groves |
| `stone_block` | Stone Block | Common | 7g | Orcs, granite quarries |
| `herb` | Herb | Common | 4g | Herb patches |

---

## 3. Inventory System

### Inventory Class

```python
@dataclass
class Inventory:
    items: list[str]              # Item IDs in the bag
    max_slots: int = 8            # Maximum bag items
    max_weight: float = 20.0      # Maximum total weight
    weapon: str | None = None     # Equipped weapon
    armor: str | None = None      # Equipped armor
    accessory: str | None = None  # Equipped accessory
```

### Capacity Limits

| Entity Type | Max Slots | Max Weight |
|-------------|-----------|------------|
| Hero | 36 | 90.0 |
| Goblin (all tiers) | 12 | 30.0 |

Configured in `SimulationConfig` as `hero_inventory_slots`, `hero_inventory_weight`, `goblin_inventory_slots`, `goblin_inventory_weight`.

### Key Methods

| Method | Description |
|--------|-------------|
| `add_item(item_id)` | Add to bag if slots and weight allow. Returns bool. |
| `remove_item(item_id)` | Remove first occurrence. Returns bool. |
| `equip(item_id)` | Equip into matching slot. Swaps if occupied. |
| `equipment_bonus(attr)` | Sum a stat bonus across equipped items. |
| `get_all_item_ids()` | All items: bag + equipped (for loot drops). |
| `used_slots` | Property: current item count in bag. |
| `current_weight` | Property: total weight of bag + equipped items. |
| `weight_ratio` | Property: `current_weight / max_weight` (0.0–1.0+). |
| `is_effectively_full` | Property: `True` when slots full OR weight ≥ max. Used by LootGoal and LootingHandler to abort looting (bug-02). |
| `auto_equip_best(item_id)` | Equip if better than current gear in that slot. |
| `copy()` | Deep copy for snapshot generation. |

### Equipment Bonus Calculation

Effective stats computed via `Entity.effective_*()`:

```python
def effective_atk(self) -> int:
    base = self.stats.atk
    if self.inventory:
        base += int(self.inventory.equipment_bonus("atk_bonus"))
    # ... status effect multipliers ...
    return max(base, 1)
```

Pattern used for: `effective_atk`, `effective_def`, `effective_spd`, `effective_crit_rate`, `effective_evasion`, `effective_max_hp`, `effective_matk`, `effective_mdef`.

---

## 4. Item Power & Auto-Equip

### Item Power Heuristic

`_item_power(template)` sums all stat bonuses:

```
power = atk + def + spd + max_hp + matk + mdef + crit_rate*50 + evasion*50 + luck
```

### Auto-Equip Best

`Inventory.auto_equip_best(item_id)`:
- **Empty slot** → always equip
- **Occupied** → equip only if new item has higher power
- **Non-equipment items** → ignored

Used during: loot pickup, shop purchases.

---

## 5. Loot Tables

### Goblin Tier Loot (`TIER_LOOT_TABLES`)

| Tier | Possible Drops |
|------|---------------|
| BASIC | small_hp_potion (5), rusty_dagger (2), leather_vest (1) |
| SCOUT | small_hp_potion (4), goblin_blade (3), speed_ring (1) |
| WARRIOR | medium_hp_potion (3), goblin_blade (2), goblin_shield (2), chainmail (1) |
| ELITE | large_hp_potion (2), chief_axe (1), chief_plate (1), lucky_charm (1) |

Numbers in parentheses are weights for weighted random selection.

### Race-Specific Loot (`RACE_LOOT_TABLES`)

Each mob kind has drops with probabilities (see `entities_and_factions.md` for full race details):

| Kind | Key Drops |
|------|-----------|
| `wolf` | Wolf Pelt (40%), Small HP Potion (20%) |
| `alpha_wolf` | Wolf Pelt (60%), Wolf Fang (50%), Medium HP Potion (30%) |
| `bandit_chief` | Bandit Bow (60%), Gold Pouch M (50%), Speed Ring (20%) |
| `lich` | Ectoplasm (60%), Enchanted Dust (40%), Large HP Potion (30%) |
| `orc_warlord` | Orc Axe (60%), Orc Shield (50%), Iron Ore (40%) |

### Starting Gear by Tier (`TIER_STARTING_GEAR`)

| Tier | Weapon | Armor |
|------|--------|-------|
| BASIC | — | — |
| SCOUT | goblin_blade | — |
| WARRIOR | goblin_blade | goblin_shield |
| ELITE | chief_axe | chief_plate |

Hero starts with: `iron_sword`, `leather_vest`, 3× `small_hp_potion`.

---

## 6. Ground Loot

### Drop Mechanics

When an entity dies, all items (bag + equipped) are dropped at the death position:

```python
world.drop_items(entity.pos, entity.inventory.get_all_item_ids())
```

Hero death: drops bag items only, keeps equipment.

### Pickup Mechanics

The `LOOT` action in `WorldLoop._process_item_actions()`:
1. Items removed from ground
2. Each item added to inventory if space allows
3. Equipment auto-equipped if slot is empty
4. Items that can't be carried dropped back to ground

---

## 7. Home Storage System

Heroes have persistent storage at their home position (`HomeStorage` dataclass).

### Storage Tiers

| Level | Max Slots | Upgrade Cost |
|-------|-----------|-------------|
| 0 | 30 | Free (starting) |
| 1 | 50 | 200g |
| 2 | 80 | 500g |

### AI Behavior (`VISIT_HOME` state)

Heroes visit home when:
- Inventory nearly full (≥ max - 2) and storage has space
- Can afford an upgrade

At home, the `VisitHomeHandler`:
1. Upgrades storage if affordable
2. Stores low-priority items: materials not needed for crafting, weaker equipment, excess consumables (keep 2)

### Integration

- `EntityBuilder.with_home_storage()` creates storage on hero spawn
- `Entity.home_storage` field, deep-copied in `Entity.copy()`
- `hero_should_visit_home()` scorer in `states.py`
- Exposed via API: `home_storage_used`, `home_storage_max`, `home_storage_level`

---

## 8. Sell Prices

| Rarity | Base Sell Price |
|--------|----------------|
| Common | 5g |
| Uncommon | 15g |
| Rare | 40g |

Materials use their explicit `sell_value` field instead.

---

# performance-report-api-payload

# Performance Report — API Payload Optimization

## Problem

The frontend polls `GET /api/v1/state` every ~80ms. Pre-optimization, this endpoint returned **~1.6 MB per request**, causing visible lag and excessive bandwidth usage.

### Root Cause Breakdown (pre-optimization `/state` payload)

| Component | Size | % of Total | Issue |
|-----------|------|-----------|-------|
| `terrain_memory` (all entities) | ~761 KB | 47% | Every tile ever seen by every entity, sent every poll |
| `entity_memory` (all entities) | ~90 KB | 6% | Last-seen entity data for every entity |
| Full entity schemas (all fields) | ~200 KB | 12% | Skills, quests, attributes, equipment for every entity |
| Buildings / regions / resources | ~50 KB | 3% | Static data re-sent every poll |
| `/map` grid (2D array) | ~876 KB | one-time | Uncompressed 512×512 tile grid |

## Optimizations Applied

### 1. Slim Entity Schema (`EntitySlimSchema`)

**Before:** Full `EntitySchema` (~5 KB each) for all ~300 entities = ~1.5 MB
**After:** `EntitySlimSchema` (~200 B each) for all entities + full `EntitySchema` only for selected entity

Slim schema fields (14 total): `id`, `kind`, `x`, `y`, `hp`, `max_hp`, `state`, `level`, `tier`, `faction`, `weapon_range`, `combat_target_id`, `loot_progress`, `loot_duration`

Full schema sent only when `?selected=<id>` is passed — includes `terrain_memory`, `entity_memory`, `skills`, `quests`, `attributes`, `inventory_items`, etc.

### 2. Static Data Endpoint (`/static`)

**Before:** Buildings, resource nodes, treasure chests, and regions included in every `/state` poll
**After:** New `GET /api/v1/static` endpoint fetched once on mount

Contents: ~20 buildings, ~117 resource nodes, ~26 treasure chests, ~25 regions ≈ **47 KB** (one-time)

### 3. RLE-Compressed Map Grid

**Before:** `/map` returns `grid: number[][]` (2D array) = ~876 KB
**After:** `/map` returns `grid: number[]` (RLE flat array: `[value, count, ...]`) = ~270 KB

Frontend decodes via `decodeRLE()` in `useSimulation.ts`. Compression ratio: **~69% smaller**.

### 4. Frontend Data Flow Restructured

- `useSimulation` fetches `/map` + `/static` once on mount (parallel)
- `useSimulation` passes `?selected=<id>` to `/state` using a ref (no re-render on selection change)
- `useCanvas` accepts `EntitySlim[]` + `Entity | null` — uses slim for rendering, full for fog-of-war
- `GameCanvas`, `Sidebar`, `InspectPanel`, `EntityList` all updated for new types

## Results

### Measured Payload Sizes (10 ticks, ~360 entities)

| Endpoint | Frequency | Before | After | Reduction |
|----------|-----------|--------|-------|-----------|
| `/state` (no selection) | Every 80ms | ~800 KB | ~75 KB | **~91%** |
| `/state` (with selection) | Every 80ms | ~800 KB | ~78 KB | **~90%** |
| `/map` | Once | ~876 KB | ~270 KB | **~69%** |
| `/static` | Once | N/A (in /state) | ~47 KB | **100% removed from poll** |

### Bandwidth Impact

| Metric | Before | After |
|--------|--------|-------|
| Per-poll payload | ~800 KB – 1.6 MB | ~75 KB |
| Bandwidth at 80ms poll | ~10–20 MB/s | ~0.9 MB/s |
| One-time load | ~876 KB | ~317 KB (map + static) |

### Test Coverage

- **575 existing tests pass** (0 failures)
- **8 new payload tests** in `tests/test_api_payload.py`:
  - RLE encoding correctness and decode round-trip
  - Slim schema field validation (must have / must not have)
  - Per-entity JSON size < 300 B
  - Full `/state` response < 100 KB (no selection)
  - `WorldStateResponse` has no static fields
  - `StaticDataResponse` has all static fields
- **TypeScript compiles clean** (0 errors)

## Files Changed

### Backend
- `src/api/schemas.py` — `EntitySlimSchema`, `StaticDataResponse`, `MapResponse` (RLE grid), `WorldStateResponse` (slimmed)
- `src/api/routes/state.py` — `/state` (slim + selected), `/static` endpoint
- `src/api/routes/map.py` — RLE encoding

### Frontend
- `frontend/src/types/api.ts` — `EntitySlim`, `StaticData`, `MapData` (RLE)
- `frontend/src/hooks/useSimulation.ts` — `decodeRLE()`, `DecodedMapData`, fetch `/static` once, `selectedIdRef`
- `frontend/src/hooks/useCanvas.ts` — `EntitySlim[]` + `Entity | null` params
- `frontend/src/components/GameCanvas.tsx` — `selectedEntity` prop, minimap uses full entity
- `frontend/src/components/Sidebar.tsx` — `EntitySlim[]` + `selectedEntity` prop
- `frontend/src/components/InspectPanel.tsx` — `DecodedMapData` type
- `frontend/src/components/EntityList.tsx` — `EntitySlim` type
- `frontend/src/App.tsx` — pass `selectedEntity`

### Tests & Scripts
- `tests/test_api_payload.py` — 8 payload optimization tests
- `scripts/profile_api_payload.py` — API payload size profiler

## How to Profile

```bash
python scripts/profile_api_payload.py                # Default: 10 ticks, seed 42
python scripts/profile_api_payload.py --ticks 50     # More ticks = more memory accumulated
python scripts/profile_simulation.py --ticks 500     # Engine tick profiling (unchanged)
```

---

# performance-report-epic16

# Performance Audit Report — Epic 16

## Baseline (pre-optimization)

- **Map**: 192×192, 8 Voronoi regions, 156 entities at peak
- **Avg tick**: 49.8ms (20.0 ticks/sec)
- **P95**: 72.0ms, **Max**: 257.7ms
- **Function calls**: 159M over 500 ticks

## Hotspots Identified (cProfile, 500 ticks)

| Rank | Function | tottime | calls | Root Cause |
|------|----------|---------|-------|------------|
| 1 | `_update_entity_memory` | 19.0s | 500 | O(n × vr²) Vector2 alloc + O(n²) entity scan + linear memory search |
| 2 | `find_frontier_target` | 7.2s | 8,704 | Iterates ALL explored tiles (grows with map) |
| 3 | `manhattan` | 7.2s | 15M | Method call overhead at extreme volume |
| 4 | `visible_entities` | 4.2s | 70k | O(n) full entity scan per call |
| 5 | Worker pool threading | 22s | 43k futures | ThreadPoolExecutor overhead with 1 worker |
| 6 | `_tick_engagement` | 2.0s | 500 | O(n²) entity scan for adjacency |
| 7 | `Snapshot.from_world` | 2.7s | 501 | Unnecessary grid.copy() every tick |
| 8 | `alive` property | 3.2s | 12.7M | Property chain overhead |
| 9 | `enum.__get__` | 1.8s | 5.4M | Enum descriptor access in terrain scan |

## Optimizations Applied

### 1. `_update_entity_memory` — terrain scan (world_loop.py)
- **Before**: `Vector2(tx, ty)` allocated per tile → `grid.in_bounds()` → `grid.get()` → `.value`
- **After**: Direct `grid._tiles[row_base + tx].value` — no Vector2, no method calls
- Also: moved `from ... import Vector2` out of the loop
- **Impact**: 19.0s → 5.0s tottime

### 2. `_update_entity_memory` — entity scan (world_loop.py)
- **Before**: O(n²) — every entity scans every other entity, linear search through entity_memory list
- **After**: `spatial_hash.query_radius()` for nearby entities, `dict[id → entry]` for O(1) memory lookup
- **Impact**: Eliminated ~10s of O(n²) scanning

### 3. `find_frontier_target` (perception.py)
- **Before**: Iterates ALL explored tiles to find frontier (grows unbounded with map exploration)
- **After**: Bounded neighborhood scan (max 40-tile radius around actor), early exit at 32 candidates
- **Impact**: 7.2s → 4.9s (and won't degrade as entities explore more)

### 4. `visible_entities` (perception.py)
- **Before**: O(n) scan of all entities per call (70k calls)
- **After**: Snapshot spatial index (`_spatial` dict, cell_size=16) → only check nearby cells
- **Impact**: 4.2s → 0.7s tottime (**83% reduction**)

### 5. Worker pool inline mode (worker_pool.py)
- **Before**: `ThreadPoolExecutor.submit()` + `as_completed()` even with 1 worker = 22s threading overhead
- **After**: Inline execution when `num_workers <= 1` — no futures, no thread sync
- **Impact**: Eliminated 22s of cProfile overhead; real-world: ~3ms/tick saved

### 6. `_tick_engagement` (world_loop.py)
- **Before**: O(n²) — every entity scans all others for adjacency
- **After**: `spatial_hash.query_radius(pos, 1)` — only check immediate neighbors
- **Impact**: 2.0s → 0.3s

### 7. Snapshot creation (snapshot.py)
- **Before**: `grid.copy()` copies 36,864 tiles every tick (grid never changes during ticks)
- **After**: Share grid reference directly
- Also: Build lightweight spatial index during `from_world` for `visible_entities`
- **Impact**: Saved ~0.5s over 500 ticks

### 8. Grid raw-coordinate access (grid.py)
- Added `get_xy(x, y)` and `in_bounds_xy(x, y)` methods that skip Vector2 allocation

## Post-Optimization Results

- **Avg tick**: 28.4ms (34.9 ticks/sec) — **43% faster**
- **P50**: 27.0ms — **41% faster**
- **P95**: 40.1ms — **44% faster**
- **Max**: 59.8ms — **77% faster** (spikes nearly eliminated)
- **StdDev**: 6.1ms — **64% less variance**
- **Function calls**: 47M — **70% fewer**

## Memory Profile (500 ticks)

- **Current**: 374.7 KB
- **Peak**: 14.1 MB
- **Status**: Healthy, no unbounded growth detected
- Top allocations: profiler timing arrays, terrain_memory dicts, snapshot copies

## Remaining Hotspots (not worth optimizing without changing architecture)

| Function | tottime | Notes |
|----------|---------|-------|
| `_update_entity_memory` | 5.0s | Inherent cost of updating vision for ~80 entities |
| `find_frontier_target` | 3.9s | Bounded scan, scales with vision_range not map size |
| `Entity.copy` | 1.5s | Deep copy needed for thread safety |
| `enum.__get__` | 1.8s | Python enum overhead, would need C extension |
| `alive` property | 1.3s | Property chain, 3.4M calls — marginal |

## Files Changed

- `src/engine/world_loop.py` — `_update_entity_memory`, `_tick_engagement`
- `src/ai/perception.py` — `visible_entities`, `find_frontier_target`
- `src/engine/worker_pool.py` — inline dispatch for single-worker
- `src/core/snapshot.py` — skip grid copy, add spatial index
- `src/core/grid.py` — raw-coordinate accessors

---

# performance-report-rendering

# Performance Report — Frontend Rendering Optimization

## Problem

With the 512×512 map (expanded from 192×192), the frontend became extremely laggy during dragging and zooming, especially in spectate mode (fog-of-war active). UI operations felt unresponsive.

### Root Causes

| Bottleneck | Impact | Frequency |
|-----------|--------|-----------|
| Minimap terrain: 262K `fillRect` calls | ~50ms per frame | Every poll (80ms) + every drag event |
| Fog overlay: 8192×8192 canvas (67M pixels) | GPU compositing lag during CSS transform | Every drag frame |
| Overlay redraw: 262K tile iterations | ~30ms per redraw | Every poll (object ref changed) |
| `Object.keys(terrain_memory).length` | O(10K) per render | Every render during drag (~60fps) |
| `selectedEntity` setState every poll | Triggers re-renders + canvas effects | Every 80ms (even same data) |
| Minimap `canvas.width` reset every frame | GPU reallocation | Every poll |

## Optimizations Applied

### 1. Minimap Terrain Caching (`GameCanvas.tsx`)

**Before:** 262K `fillRect` calls on every poll and drag event (terrain + fog-of-war in single effect).
**After:** Split into two effects:
- **Cache effect** — draws 262K terrain tiles to offscreen `<canvas>` (`mmTerrainCacheRef`). Only re-runs when `mmTerrainKey` changes (selection or `terrain_memory` size change).
- **Dynamic effect** — blits cached terrain via `drawImage()`, then draws ~300 entity dots + viewport rect.

**Result:** During drag, only 1 `drawImage` + ~300 entity dots instead of 262K `fillRect`.

### 2. Overlay Canvas Shrunk 256× (`useCanvas.ts` + `GameCanvas.tsx`)

**Before:** Overlay canvas was 8192×8192 (67M pixels). GPU had to composite this massive texture on every CSS transform during drag.
**After:** Overlay is 512×512 (1 pixel per tile), CSS-scaled via `transform: scale(CELL_SIZE × zoom)` with `imageRendering: pixelated`.

- Fog drawn at 1px/tile: `fillRect(x, y, 1, 1)` instead of `fillRect(x*16, y*16, 16, 16)`
- Vision border, weapon range ring, ghost markers moved to entity canvas (need sub-tile precision)

**Result:** GPU composites 262K pixels instead of 67M pixels during drag — **256× reduction**.

### 3. Overlay Position-Based Skip (`useCanvas.ts`)

**Before:** Overlay effect depended on `selectedEntity` (new object ref every poll) → 262K tile iterations every 80ms.
**After:** Memoized `overlayKey` string (`id_x_y_memSize_emSize`). Effect early-returns if key unchanged.

**Result:** Fog only redraws when entity actually moves or memory grows.

### 4. Memoized Overlay Key (`useCanvas.ts`)

**Before:** `Object.keys(selectedEnt.terrain_memory).length` computed on every render (O(10K) during drag at 60fps).
**After:** `overlayKey` wrapped in `useMemo` with `[selectedEnt, selectedEntityId]` deps.

**Result:** O(10K) computation only runs when `selectedEntity` state changes (once per tick), not on every drag frame.

### 5. Smart State Updates (`useSimulation.ts`)

**Before:** `setEntities()`, `setSelectedEntity()`, etc. called every poll (80ms), even when paused or data unchanged.
**After:**
- `selectedEntity` tracked via `lastSelKeyRef` (`responseEntityId_tick`) — skips setState when unchanged
- `entities` / `groundItems` only update when tick advances
- `selectedIdRef` synced immediately in callback (not via `useEffect` delay)

**Result:** Zero re-renders from simulation state when paused. During same tick, only status updates.

### 6. Minimap GPU Reallocation Fix (`GameCanvas.tsx`)

**Before:** `canvas.width = mmW; canvas.height = mmH;` set every frame — triggers GPU memory reallocation even when size unchanged.
**After:** Only set if dimensions actually changed; use `clearRect()` otherwise.

## Fog-of-War Visual Levels

Three distinct brightness levels when spectating:

| State | Overlay | Main Canvas | Minimap |
|-------|---------|-------------|---------|
| **In vision** | Clear | 100% brightness | `TILE_COLORS[tile]` |
| **Explored (fog)** | `rgba(0,0,0,0.5)` | ~50% brightness | `TILE_COLORS_DIM[tile]` |
| **Unseen** | `rgba(0,0,0,1.0)` | Fully black (hidden) | `#000000` |

## Performance Impact

### During Drag (spectate mode)

| Metric | Before | After |
|--------|--------|-------|
| Minimap terrain draws | 262K fillRects | 1 drawImage |
| Fog overlay GPU pixels | 67M (8192²) | 262K (512²) |
| Canvas effects per drag frame | 3 (grid+entity+overlay) | 1 (minimap dynamic only) |
| Overlay redraws per drag | Every frame | 0 (cached by overlayKey) |

### During Polling (running)

| Metric | Before | After |
|--------|--------|-------|
| State updates per poll | 5+ setState calls | 1-2 (tick-gated) |
| Overlay redraws per poll | Every poll | Only on entity move |
| Object.keys per render | O(10K) | 0 (memoized) |

### During Polling (paused)

| Metric | Before | After |
|--------|--------|-------|
| React re-renders per poll | Full component tree | 0 (all state skipped) |

## Files Changed

- `frontend/src/hooks/useCanvas.ts` — tile-res overlay (512×512), memoized overlayKey, entity canvas draws vision border/range/ghosts, removed TILE_COLORS_DIM import
- `frontend/src/components/GameCanvas.tsx` — minimap terrain cache (offscreen canvas + split effects), overlay CSS `scale(CELL_SIZE*zoom)` + pixelated, GPU realloc fix
- `frontend/src/hooks/useSimulation.ts` — tick-based state skip, selKey for selectedEntity, immediate ref sync

---

# pitch

# RPG Simulation Engine — Project Pitch

## One-Liner

**An RPG world that plays itself** — a deterministic, concurrent simulation engine where hundreds of autonomous entities explore, fight, craft, and form factions across a living 2D world — while you watch the stories emerge.

---

## What Is This?

A **fully autonomous 2D RPG simulation engine** built on three pillars:

1. **A living world** — heroes explore, fight, loot, craft, and level up on their own. Monsters guard territory, form factions, and fight back. The economy runs itself. Every entity has personality traits that shape its decisions.
2. **Emergent storytelling** — nobody writes the plot. Stories emerge from the collision of AI, combat, economy, and faction systems interacting in ways that create *narrative as a side effect of mechanics*.
3. **Serious engineering** — deterministic concurrency, immutable snapshots, domain-separated RNG, shared pydantic schemas, 575+ tests, and performance-optimized rendering. The same seed produces the exact same story on any machine.

Think of it as an **ant farm meets Final Fantasy** — a living world you observe rather than control, built on an engine you can trust.

---

## Why Is It Interesting?

### 🌍 A Complete Living World

This isn't a toy simulation. The systems are deep enough to produce real RPG gameplay:

| System | What It Does |
|--------|-------------|
| **8 biomes** | Forest, desert, swamp, mountain, grassland, snow, jungle, volcanic — each with unique races, resources, and terrain features |
| **9+ factions** | Hero Guild, Goblin Horde, Wolf Pack, Bandit Clan, Undead, Orc Tribe, Centaur Herd, Frost Kin, Lizardfolk, Demon Horde — with territory, hostility, and faction-aware AI |
| **4 hero classes** | Warrior → Champion, Ranger → Sharpshooter, Mage → Archmage, Rogue → Assassin — each with unique skills, scaling, and playstyle |
| **30+ item types** | Weapons, armor, accessories, potions, crafting materials — with rarity tiers (Common → Epic) and stat bonuses |
| **AoE & ranged combat** | Whirlwind, Rain of Arrows, Fireball — with weapon range, line of sight, cover, threat/aggro, kiting AI |
| **A* pathfinding** | Terrain-cost-aware routing with road preference, path caching, and greedy fallback |
| **Full economy** | Shop, blacksmith, guild — heroes sell loot, buy potions, learn recipes, craft gear |
| **Personality traits** | Brave, Cautious, Greedy, Curious, Resilient — each modifies AI goal scoring differently |
| **Region difficulty** | Tier 1–4 scaling by distance from town — stat multipliers, loot quality, and mob composition increase |

### 📖 Emergent Stories, Not Scripted Ones

Nobody writes the plot. Instead, stories emerge from the collision of simple rules:

- A cautious hero avoids a goblin camp for 500 ticks, slowly grinding wolves in the forest. It levels up, crafts a sword at the blacksmith, and finally raids the camp — only to find the goblin chief has leveled too.
- A brave, greedy ranger charges deep into orc territory for rare loot. It kites enemies at range, narrowly survives with 3 HP, and flees back to town to sell everything at the shop.
- Two factions clash at a border. The undead push from the swamp, skeletons shambling slowly but tanking massive damage. The bandits in the desert scatter — they're fast but fragile.

These aren't handcrafted scenarios. They happen because the systems interact in ways that create *narrative* as a side effect of *mechanics*.

### ⚙️ Engineered for Correctness and Performance

The engine is built with the rigor of production systems software:

- **Absolute determinism** — all randomness via `Hash(Seed, Domain, EntityID, Tick)` using xxhash. Same seed = same world = same story, on any machine, every run.
- **Single-writer concurrency** — AI workers run in parallel on immutable `Snapshot` objects. Only the `WorldLoop` thread mutates `WorldState`. No locks on the hot path.
- **Shared schemas** — core data models (`ItemTemplate`, `SkillDef`, `ClassDef`, `TraitDef`) are `pydantic_dataclass(frozen=True)` — the single source of truth for both the game engine and the REST API. No duplicate schemas.
- **575+ automated tests** — combat, AI, pathfinding, inventory, economy, deterministic replay verification, API payload tests.
- **Performance-optimized** — backend: 28ms/tick for 200 entities on 512×512 (43% improvement after audit). Frontend: 256× smaller fog overlay, offscreen minimap caching, drag-skip rendering, 98% API payload reduction.

### 🔭 Built to Watch

The web-based viewer isn't an afterthought — it's designed for observation:

- **Spectate any entity** — see the world through its eyes with fog of war, vision range, and ghost markers for remembered enemies
- **Three fog levels** — visible (clear), explored (dimmed), and unseen (completely dark)
- **Rich tooltips** — hover any tile to see terrain, entities, buildings, loot, and resources — fog-gated when spectating
- **Minimap** with terrain caching, entity dots, and viewport indicator
- **Event log** tracking combat, deaths, level-ups, loot, and skill usage
- **6-tab inspector** showing stats, equipment, skills, AI goals, memory, and events for any entity

---

## Architecture

### Tick Cycle

```
Every tick (configurable speed):
  1. SCHEDULE  — find entities whose next_act_at ≤ current_tick
  2. COLLECT   — parallel AI workers decide actions (read immutable snapshots)
  3. RESOLVE   — single thread validates & applies all actions atomically
  4. CLEANUP   — respawn, decay, territory effects, threat decay
```

### Concurrency Model

| Thread | Role | Reads | Writes |
|--------|------|-------|--------|
| **Main** (uvicorn) | HTTP requests | `latest_snapshot` | Control signals |
| **Engine** (`WorldLoop`) | Tick cycle | `WorldState` | `WorldState`, `Snapshot` |
| **Workers** (ThreadPool) | AI computation | `Snapshot` (immutable) | `ActionQueue` (thread-safe) |

Workers never see partial updates. The `ActionQueue` is the only shared mutable structure.

### Data-Driven Design

Adding content means adding data, not code:

- **Items** → register in `ITEM_REGISTRY`
- **Skills** → add `SkillDef` to class definition
- **Factions** → extend `Faction` enum + register relationships
- **Terrain costs** → add entry to `TERRAIN_MOVE_COST`
- **Traits** → register `TraitDef` with utility bonuses
- **Races** → add to `RACE_TIER_KINDS` + `RACE_STAT_MODS`

All game definitions are pydantic dataclasses — `IntEnum` at runtime for fast logic, lowercase strings in JSON for the API.

---

## Current State

### What's Built (production-ready)

**Simulation:**
- 200+ autonomous entities on a 512×512 Voronoi-tessellated world with 8 biomes
- Hybrid AI: Utility AI for goal selection + State Machine for execution
- Full combat: AoE skills, ranged weapons, threat/aggro, opportunity attacks, kiting, cover
- A* pathfinding with terrain costs, path caching, greedy fallback
- Economy loop: loot → sell → buy potions → gather materials → craft gear
- 9+ factions with territory, hostility, alert states, town aura

**Engineering:**
- Deterministic replay: same seed = same world on any machine (verified by SHA-256 fingerprint test)
- 575+ automated tests (combat, AI, pathfinding, inventory, economy, API, replay)
- Backend: 28ms/tick (43% improvement after profiling audit)
- Frontend: 98% API payload reduction, 256× smaller fog overlay, drag-skip rendering
- Shared pydantic schemas — zero duplicate API models

**Frontend:**
- Triple-layer canvas (grid + entities + fog overlay) with CSS-scaled tile-resolution fog
- Spectate mode with 3-level fog of war, ghost markers, vision border
- Rich tile tooltips (fog-gated), minimap with terrain caching, 6-tab entity inspector
- Interactive API documentation page with Try It Out

---

## Roadmap

Epics are ordered by **impact across all three pillars** — emergent storytelling, world depth, and engineering challenge.

### Tier 1 — High-Impact Features

| Epic | Name | Impact |
|------|------|--------|
| **E12** | AI Personality & Emergent Behavior | Nemesis system, grudges, confidence, mood — entities become *individuals* with history. Highest storytelling ROI. |
| **E04** | Multi-Hero Party System | Multiple autonomous heroes cooperating and competing — multiplies narrative surface area and AI complexity. |
| **E06** | World Events & Invasions | Goblin raids, wandering bosses, plagues — external pressure creates dramatic stakes. New event scheduling subsystem. |
| **E07** | Reputation & Faction Diplomacy | Shifting alliances, cease-fires, faction wars — the political landscape evolves at runtime. |

### Tier 2 — World Richness

| Epic | Name | Impact |
|------|------|--------|
| **E03** | Day/Night & Weather | Natural rhythm drives behavior cycles. Weather effects + visibility modifiers add strategic depth. |
| **E02** | NPC & Social System | Living town with schedules, relationships, merchants — NPCs as autonomous agents. |
| **E01** | Dungeon System | Instanced multi-room challenges — heroes autonomously gauge readiness before entering. |
| **E13** | Ruins Exploration & Lore | Discovery loop, lore collection, hidden caches — rewards exploration with permanent bonuses. |

### Tier 3 — Depth & Polish

| Epic | Name | Impact |
|------|------|--------|
| **E05** | Advanced Combat (remaining) | Status ailments, combos, environmental combat, formations — tactical depth. |
| **E08** | Transcendence & Endgame Classes | Tier 3 class advancement, ultimate skills — late-game power fantasy. |
| **E10** | Enchantment & Item Progression | Gem socketing, +1–+10 enhancement, item sets — gear investment. |
| **E14** | Frontend UX Improvements | Smooth interpolation, damage numbers, keyboard shortcuts, camera follow. |
| **E11** | Replay & Observation Tools | Timeline scrubbing, heatmaps, stat graphs — tools for studying emergent behavior. |
| **E09** | Pathfinding (remaining) | Hazard avoidance, formations, speed modifiers, path visualization. |

---

## Try It

```bash
git clone <repo-url>
cd rpg-based-simulation
make install    # Python + Node dependencies
make serve      # Open http://localhost:8000
```

Click any entity to spectate. Press play. Watch the world unfold.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Engine** | Python 3.11+, xxhash, ThreadPoolExecutor |
| **API** | FastAPI, Pydantic 2, uvicorn |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, HTML5 Canvas |
| **Testing** | pytest (575+ tests), deterministic replay verification |

---

# world_generation

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

---

#   S i m u l a t i o n   E x e c u t i o n   F l o w   a n d   T e c h n o l o g y   S t a c k  
  
 T h i s   d o c u m e n t   p r o v i d e s   a   h i g h - l e v e l   o v e r v i e w   o f   t h e   e n t i r e   R P G   s i m u l a t i o n   s y s t e m ,   d e t a i l i n g   t h e   t e c h n o l o g y   s t a c k s   u s e d   a n d   t h e   p r i m a r y   f l o w s   o f   e x e c u t i o n   f r o m   b o o t   t o   o b s e r v a b i l i t y .  
  
 - - -  
  
 # #   1 .   T e c h n o l o g y   S t a c k  
  
 T h e   p r o j e c t   u s e s   a   m o d e r n ,   d i s t r i b u t e d   a r c h i t e c t u r e   t o   h a n d l e   c o n c u r r e n t   A I   s i m u l a t i o n   w i t h   d e t e r m i n i s t i c   r e s u l t s   a n d   h i g h   o b s e r v a b i l i t y .  
  
 |   L a y e r   |   T e c h n o l o g y   |   P u r p o s e   |  
 | - - - - - - - | - - - - - - - - - - - - | - - - - - - - - - |  
 |   * * F r o n t e n d * *   |   R e a c t ,   V i t e ,   T y p e S c r i p t   |   I n t e r a c t i v e   U I   f o r   v i s u a l i z a t i o n ,   e n t i t y   i n s p e c t i o n ,   a n d   s i m u l a t i o n   c o n t r o l .   |  
 |   * * A P I   G a t e w a y * *   |   N g i n x   |   S e r v e s   s t a t i c   f r o n t e n d   a s s e t s   a n d   r e v e r s e - p r o x i e s   A P I   r e q u e s t s   t o   t h e   b a c k e n d .   |  
 |   * * B a c k e n d * *   |   F a s t A P I   ( P y t h o n )   |   H i g h - p e r f o r m a n c e   a s y n c h r o n o u s   A P I ;   m a n a g e s   t h e   l i f e c y c l e   o f   t h e   s i m u l a t i o n   e n g i n e .   |  
 |   * * S i m u l a t i o n   C o r e * *   |   C u s t o m   E n g i n e   ( P y t h o n )   |   S i n g l e - t h r e a d e d ,   d e t e r m i n i s t i c   4 - p h a s e   t i c k   l o o p .   |  
 |   * * A I   S c h e d u l i n g * *   |   R a b b i t M Q   +   ` p i k a `   |   D i s t r i b u t e d   t a s k   q u e u e   f o r   o f f l o a d i n g   c o m p l e x   A I   " b r a i n "   d e c i s i o n s   t o   w o r k e r   d a e m o n s .   |  
 |   * * E v e n t   S o u r c i n g * *   |   A p a c h e   K a f k a   |   P e r s i s t e n t   a p p e n d - o n l y   l o g   f o r   f u l l   s i m u l a t i o n   s n a p s h o t s   a n d   g r a n u l a r   d e l t a   e v e n t s .   |  
 |   * * R e a l - t i m e   S t r e a m i n g * *   |   R e d i s   S t r e a m s   +   S S E   |   S t a t e   d e l t a s   p u b l i s h e d   t o   R e d i s   a n d   s t r e a m e d   t o   t h e   f r o n t e n d   v i a   S e r v e r - S e n t   E v e n t s .   |  
 |   * * O b s e r v a b i l i t y * *   |   P r o m e t h e u s   &   G r a f a n a   |   R e a l - t i m e   m e t r i c s   c o l l e c t i o n   ( P r o m e t h e u s )   a n d   v i s u a l i z a t i o n   d a s h b o a r d s   ( G r a f a n a ) .   |  
 |   * * I n f r a s t r u c t u r e * *   |   D o c k e r   &   D o c k e r   C o m p o s e   |   C o n t a i n e r i z a t i o n   a n d   o r c h e s t r a t i o n   o f   a l l   s e r v i c e s .   |  
  
 - - -  
  
 # #   2 .   M a i n   E x e c u t i o n   F l o w  
  
 # # #   P h a s e   A :   B o o t   &   I n i t i a l i z a t i o n  
 W h e n   t h e   b a c k e n d   c o n t a i n e r   s t a r t s ,   t h e   f o l l o w i n g   s e q u e n c e   o c c u r s :  
 1 .     * * F a s t A P I   S t a r t u p * * :   T h e   a p p l i c a t i o n   i n i t i a l i z e s   a n d   r u n s   t h e   ` l i f e s p a n `   e v e n t .  
 2 .     * * E n g i n e   B u i l d i n g * * :   ` E n g i n e M a n a g e r `   b u i l d s   t h e   i n i t i a l   w o r l d   ( G r i d   g e n e r a t i o n ,   e n t i t y   s p a w n i n g ,   m e t a d a t a   r e g i s t r y ) .  
 3 .     * * I n f r a s t r u c t u r e   C o n n e c t i v i t y * * :   C o n n e c t i o n   p o o l s   a r e   e s t a b l i s h e d   f o r   R e d i s ,   K a f k a ,   a n d   R a b b i t M Q .  
 4 .     * * R e c o v e r y   ( O p t i o n a l ) * * :   I f   e n a b l e d ,   t h e   e n g i n e   c o n s u m e s   t h e   l a t e s t   s n a p s h o t   a n d   e v e n t s   f r o m   K a f k a   t o   r e h y d r a t e   t h e   s t a t e .  
 5 .     * * T h r e a d   L a u n c h * * :   T h e   ` W o r l d L o o p `   i s   s t a r t e d   i n   a   d e d i c a t e d   b a c k r o u n d   t h r e a d   t o   r u n   t h e   s i m u l a t i o n   i n d e p e n d e n t l y   o f   H T T P   r e q u e s t s .  
  
 # # #   P h a s e   B :   T h e   T i c k   C y c l e   ( 4   S e q u e n t i a l   P h a s e s )  
 E a c h   s i m u l a t i o n   t i c k   e x e c u t e s   a   s t r i c t   4 - p h a s e   p i p e l i n e   i n   ` w o r l d _ l o o p . p y `   t o   e n s u r e   d e t e r m i n i s m :  
  
 1 .     * * S c h e d u l i n g   &   S n a p s h o t t i n g * * :  
         *       T h e   e n g i n e   i d e n t i f i e s   e n t i t i e s   d u e   t o   a c t   ( ` n e x t _ a c t _ a t   < =   c u r r e n t _ t i c k ` ) .  
         *       A n   i m m u t a b l e   ` S n a p s h o t `   o f   t h e   w o r l d   i s   c r e a t e d .  
         *       T a s k s   a r e   f a n n e d   o u t   t o   * * R a b b i t M Q * *   ( D i s t r i b u t e d )   o r   a   * * T h r e a d P o o l * *   ( L o c a l ) .  
 2 .     * * A I   D e c i s i o n   C o l l e c t i o n * * :  
         *       W o r k e r   d a e m o n s   r e c e i v e   t h e   s n a p s h o t   o n c e   p e r   t i c k   ( F a n o u t ) .  
         *       W o r k e r s   c o m p u t e   d e c i s i o n s   ( ` A I B r a i n . d e c i d e ` )   f o r   a s s i g n e d   e n t i t i e s   a n d   p u s h   ` A c t i o n P r o p o s a l s `   t o   a   r e s u l t s   q u e u e .  
         *       T h e   e n g i n e   b l o c k s   u n t i l   a l l   r e s u l t s   a r e   c o l l e c t e d   o r   a   h a r d   t i m e o u t   ( e . g . ,   2 s )   i s   r e a c h e d .  
 3 .     * * C o n f l i c t   R e s o l u t i o n   &   A p p l i c a t i o n * * :  
         *       P r o p o s a l s   a r e   s o r t e d   d e t e r m i n i s t i c a l l y   ( b y   ` n e x t _ a c t _ a t ` ,   t h e n   ` e n t i t y _ i d ` ) .  
         *       E a c h   a c t i o n   i s   v a l i d a t e d   a g a i n s t   t h e   c u r r e n t   s t a t e   ( e . g . ,   " i s   t h e   t a r g e t   s t i l l   r e a c h a b l e ? " ) .  
         *       V a l i d   a c t i o n s   a r e   a p p l i e d   s e q u e n t i a l l y   t o   t h e   ` W o r l d S t a t e ` .  
 4 .     * * P o s t - T i c k   &   E v e n t   E m i s s i o n * * :  
         *       S u b s y s t e m s   u p d a t e   ( X P   g a i n s ,   L e v e l - u p s ,   S t a m i n a   r e g e n ,   S t a t u s   e f f e c t   t i c k s ) .  
         *       E v e n t s   a r e   p u b l i s h e d   t o   t h e   i n t e r n a l   ` E v e n t L o g ` .  
         *       S t a t e   d e l t a s   a r e   p u b l i s h e d   t o   t h e   * * R e d i s   S t r e a m * *   f o r   i m m e d i a t e   S S E   d e l i v e r y   t o   t h e   f r o n t e n d .  
         *       P e r i o d i c   s n a p s h o t s   a r e   p u s h e d   t o   * * K a f k a * *   f o r   p e r s i s t e n c e .  
  
 # # #   P h a s e   C :   O b s e r v a b i l i t y   P i p e l i n e  
 T h e   s y s t e m   i s   i n s t r u m e n t e d   t o   p r o v i d e   d e e p   i n s i g h t s   i n t o   p e r f o r m a n c e   a n d   g a m e   b a l a n c e :  
 1 .     * * I n s t r u m e n t a t i o n * * :   T h e   e n g i n e   u p d a t e s   ` p r o m e t h e u s _ c l i e n t `   m e t r i c s   ( G a u g e s ,   C o u n t e r s ,   H i s t o g r a m s )   t r a c k i n g   t i c k   d u r a t i o n s ,   q u e u e   d e p t h s ,   a n d   e n t i t y   c o u n t s .  
 2 .     * * S c r a p i n g * * :   P r o m e t h e u s   p e r i o d i c a l l y   s c r a p e s   t h e   ` / m e t r i c s `   e n d p o i n t   o f   t h e   b a c k e n d .  
 3 .     * * V i s u a l i z a t i o n * * :  
         *       * * G r a f a n a * *   q u e r i e s   P r o m e t h e u s   t o   d i s p l a y   r e s o u r c e   m e t r i c s   ( C P U ,   R A M ) .  
         *       * * C u s t o m   D a s h b o a r d s * *   d i s p l a y   s i m u l a t i o n   m e t r i c s   ( T i c k s   p e r   s e c o n d ,   t o t a l   d e a t h s ,   s p a w n   r a t e s ) .  
  
 - - -  
  
 # #   3 .   D a t a   F l o w   D i a g r a m  
  
 ` ` ` m e r m a i d  
 g r a p h   T D  
         U s e r ( [ U s e r   B r o w s e r ] )   < - - >   N g i n x [ N g i n x   R e v e r s e   P r o x y ]  
         N g i n x   < - - >   R e a c t [ R e a c t   F r o n t e n d ]  
         R e a c t   - -   A P I   C a l l s   - - >   F a s t A P I [ F a s t A P I   B a c k e n d ]  
         F a s t A P I   - -   C o n t r o l   S i g n a l s   - - >   E n g i n e [ W o r l d L o o p   E n g i n e   T h r e a d ]  
  
         s u b g r a p h   " S i m u l a t i o n   C o r e "  
                 E n g i n e   - -   M u t a t e s   - - >   S t a t e [ W o r l d S t a t e ]  
                 E n g i n e   - -   C r e a t e s   - - >   S n a p s h o t [ I m m u t a b l e   S n a p s h o t ]  
         e n d  
  
         S n a p s h o t   - -   F a n o u t   - - >   R a b b i t [ R a b b i t M Q ]  
         R a b b i t   - -   T a s k s   - - >   W o r k e r s [ A I   W o r k e r   D a e m o n s ]  
         W o r k e r s   - -   R e s u l t s   - - >   E n g i n e  
  
         E n g i n e   - -   S n a p s h o t s / E v e n t s   - - >   K a f k a [ ( K a f k a   E v e n t   S t o r e ) ]  
         E n g i n e   - -   S t a t e   D e l t a s   - - >   R e d i s [ ( R e d i s   S t r e a m s ) ]  
         R e d i s   - -   S S E   - - >   F a s t A P I  
         F a s t A P I   - -   S S E   S t r e a m   - - >   R e a c t  
  
         E n g i n e   - -   M e t r i c s   - - >   P r o m [ P r o m e t h e u s ]  
         P r o m   - -   Q u e r i e d   b y   - - >   G r a f a n a [ G r a f a n a   D a s h b o a r d s ]  
 ` ` `  
  
 - - -  
  
 # #   4 .   P r i m a r y   F i l e   R e f e r e n c e s  
  
 *       * * E n t r y   P o i n t * * :   ` s r c / a p i / e n g i n e _ m a n a g e r . p y `   ( O r c h e s t r a t e s   s t a r t u p / s h u t d o w n )  
 *       * * T h e   L o o p * * :   ` s r c / e n g i n e / w o r l d _ l o o p . p y `   ( C o r e   4 - p h a s e   l o g i c )  
 *       * * T h e   S n a p s h o t s * * :   ` s r c / c o r e / s n a p s h o t . p y `   ( P e r s i s t e n c e   a n d   W o r k e r   c o n t e x t )  
 *       * * W o r k e r   L o g i c * * :   ` s r c / w o r k e r s / a i _ w o r k e r _ d a e m o n . p y `   ( D i s t r i b u t e d   A I   p r o c e s s i n g )  
 *       * * S t r e a m i n g * * :   ` s r c / a p i / r o u t e s / s t r e a m . p y `   ( F a s t A P I   S S E   e n d p o i n t s )  
 *       * * M e t r i c s * * :   ` s r c / u t i l s / m e t r i c s . p y `   ( P r o m e t h e u s   d e f i n i t i o n s )  
 