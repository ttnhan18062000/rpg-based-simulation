# Terrain Regions, Resource Nodes & New Mob Races

This document describes the terrain region system, harvestable resource nodes, new mob races, and the HARVESTING AI behaviour introduced alongside the map size increase.

---

## Overview

The world is now a **128×128** tile grid (up from 64×64) with four new terrain types generated as organic regions across the map. Each terrain hosts a unique mob race and harvestable resource nodes. Heroes can discover resources while exploring and harvest them for crafting materials.

### High-Level Flow

```
World Generation
  ├── Place town + sanctuary (center)
  ├── Generate terrain regions (FOREST, DESERT, SWAMP, MOUNTAIN)
  │     ├── Scatter resource nodes per region
  │     └── Spawn race-specific mobs per region
  ├── Place goblin camps (on any walkable tile)
  └── Spawn heroes + goblins

Runtime
  ├── Heroes explore → discover resource nodes
  ├── HARVESTING AI state → channel → receive item
  ├── Resource depletes → cooldown → respawn
  └── Race mobs guard their terrain, fight intruders
```

---

## Terrain Types

Four new `Material` enum values in `src/core/enums.py`:

| Value | Name | Color (hex) | Description |
|-------|------|-------------|-------------|
| 6 | `FOREST` | `#1b3a1b` | Dense woodland — wolves roam here |
| 7 | `DESERT` | `#3a3420` | Arid wasteland — bandits camp here |
| 8 | `SWAMP` | `#2a2a3a` | Dark bogland — undead lurk here |
| 9 | `MOUNTAIN` | `#3a3a3a` | Rocky highlands — orcs control here |

All four terrains are **walkable** (added to `Grid.is_walkable`). Helper methods `is_forest`, `is_desert`, `is_swamp`, `is_mountain` are available on the `Grid` class.

### Region Generation (`src/api/engine_manager.py`)

Regions are placed during `_build()` before goblin camps:

1. For each terrain type, attempt to place N regions (configurable)
2. Each region center must be at least `region_min_distance` tiles from all other region centers and `camp_min_distance_from_town` from the town
3. Region tiles are painted in a diamond (Manhattan distance) shape with edge noise for organic feel
4. Radius per region is randomized between `region_min_radius` and `region_max_radius`

| Config Parameter | Default | Description |
|-----------------|---------|-------------|
| `num_forest_regions` | 4 | Number of forest regions |
| `num_desert_regions` | 3 | Number of desert regions |
| `num_swamp_regions` | 3 | Number of swamp regions |
| `num_mountain_regions` | 3 | Number of mountain regions |
| `region_min_radius` | 6 | Minimum region radius (tiles) |
| `region_max_radius` | 12 | Maximum region radius (tiles) |
| `region_min_distance` | 8 | Minimum distance between region centers |

---

## New Mob Races

Each terrain type has an associated mob race with its own faction, stat modifiers, tier variants, loot tables, and starting gear.

### Terrain → Race → Faction Mapping

| Terrain | Race | Faction | Disposition |
|---------|------|---------|-------------|
| FOREST | `wolf` | `WOLF_PACK` | Hostile to all except own |
| DESERT | `bandit` | `BANDIT_CLAN` | Hostile to all except own |
| SWAMP | `undead` | `UNDEAD` | Hostile to all (including each other race) |
| MOUNTAIN | `orc` | `ORC_TRIBE` | Hostile to all except own |

Defined in `src/core/items.py` (`TERRAIN_RACE`, `RACE_FACTION`) and `src/core/faction.py`.

### Tier Variants

Each race has three tier names (`src/core/items.py: RACE_TIER_KINDS`):

| Race | Basic (T0) | Scout/Warrior (T1–T2) | Elite (T3) |
|------|-----------|----------------------|-----------|
| Wolf | `wolf` | `dire_wolf` | `alpha_wolf` |
| Bandit | `bandit` | `bandit_archer` | `bandit_chief` |
| Undead | `skeleton` | `zombie` | `lich` |
| Orc | `orc` | `orc_warrior` | `orc_warlord` |

### Stat Modifiers (`RACE_STAT_MODS`)

Race modifiers are applied on top of tier multipliers:

| Race | HP mult | ATK mult | DEF mod | SPD mod | Crit | Evasion | Luck |
|------|---------|----------|---------|---------|------|---------|------|
| Wolf | 0.8× | 1.0× | +0 | +2 | 10% | 10% | 0 |
| Bandit | 1.0× | 0.9× | +1 | +1 | 8% | 5% | 2 |
| Undead | 1.3× | 0.8× | +3 | -2 | 3% | 0% | 0 |
| Orc | 1.2× | 1.2× | +2 | -1 | 5% | 2% | 1 |

### Race-Specific Loot (`RACE_LOOT_TABLES`)

Each mob kind has a loot table defining drop items and probabilities:

| Kind | Drops |
|------|-------|
| `wolf` | Wolf Pelt (40%), Small HP Potion (20%) |
| `dire_wolf` | Wolf Pelt (50%), Wolf Fang (30%) |
| `alpha_wolf` | Wolf Pelt (60%), Wolf Fang (50%), Medium HP Potion (30%) |
| `bandit` | Bandit Dagger (30%), Gold Pouch S (40%) |
| `bandit_archer` | Bandit Bow (40%), Gold Pouch S (50%) |
| `bandit_chief` | Bandit Bow (60%), Gold Pouch M (50%), Speed Ring (20%) |
| `skeleton` | Bone Shard (50%), Small HP Potion (15%) |
| `zombie` | Bone Shard (40%), Ectoplasm (30%) |
| `lich` | Ectoplasm (60%), Enchanted Dust (40%), Large HP Potion (30%) |
| `orc` | Orc Axe (25%), Leather (40%) |
| `orc_warrior` | Orc Axe (40%), Orc Shield (30%) |
| `orc_warlord` | Orc Axe (60%), Orc Shield (50%), Iron Ore (40%) |

### Spawning (`src/systems/generator.py: spawn_race`)

The `EntityGenerator.spawn_race(world, race, tier, near_pos)` method:

1. Allocates an entity ID and rolls a tier (if not specified)
2. Applies race stat modifiers on top of tier multipliers
3. Picks the appropriate kind name from `RACE_TIER_KINDS`
4. Equips race-specific starting gear from `RACE_STARTING_GEAR`
5. Rolls loot drops from `RACE_LOOT_TABLES`
6. Sets faction from `RACE_FACTION`
7. Places the entity near the given position (within ±3 tiles)

During world generation, each terrain region spawns 2–4 basic mobs plus 1 elite.

---

## Faction System Extensions

### New Factions (`src/core/faction.py`)

| Faction | Territory Tile |
|---------|---------------|
| `WOLF_PACK` | `Material.FOREST` |
| `BANDIT_CLAN` | `Material.DESERT` |
| `UNDEAD` | `Material.SWAMP` |
| `ORC_TRIBE` | `Material.MOUNTAIN` |

### Relations

All new factions are **hostile** to every other faction (including HERO_GUILD and GOBLIN_HORDE). Heroes entering a terrain region will trigger territory debuffs and alert nearby defenders, just like goblin camps.

---

## Resource Nodes

### Data Model (`src/core/resource_nodes.py`)

```python
@dataclass(slots=True)
class ResourceNode:
    node_id: int                # Unique ID
    resource_type: str          # e.g. "herb_patch", "ore_vein"
    name: str                   # Display name
    pos: Vector2                # Grid position
    terrain: Material           # Which terrain type this belongs to
    yields_item: str            # Item ID produced on harvest
    remaining: int              # Harvests left before depletion
    max_harvests: int           # Total harvests when fully grown
    respawn_cooldown: int       # Ticks to regenerate after depletion
    harvest_ticks: int          # Ticks to channel a single harvest
    cooldown_remaining: int     # Current cooldown counter (0 = available)
```

**Key properties:**

- `is_available` → `True` when `remaining > 0` and `cooldown_remaining == 0`
- `harvest()` → Decrements `remaining`, starts cooldown when depleted, returns `yields_item`
- `tick_cooldown()` → Called each tick; decrements cooldown, resets `remaining` when cooldown expires
- `copy()` → Creates a snapshot-safe copy for `Snapshot.resource_nodes`

### Terrain Resource Definitions (`TERRAIN_RESOURCES`)

| Terrain | Resource Type | Display Name | Yields | Max Harvests | Respawn | Channel |
|---------|--------------|--------------|--------|-------------|---------|---------|
| **FOREST** | `herb_patch` | Herb Patch | `herb` | 3 | 20 ticks | 2 |
| | `timber` | Timber | `wood` | 4 | 25 ticks | 3 |
| | `berry_bush` | Berry Bush | `wild_berries` | 2 | 15 ticks | 1 |
| **DESERT** | `gem_deposit` | Gem Deposit | `raw_gem` | 2 | 30 ticks | 3 |
| | `cactus_fiber` | Cactus Fiber | `fiber` | 3 | 20 ticks | 2 |
| | `sand_iron` | Sand Iron Deposit | `iron_ore` | 2 | 25 ticks | 3 |
| **SWAMP** | `mushroom_grove` | Glowing Mushroom Grove | `glowing_mushroom` | 3 | 20 ticks | 2 |
| | `bog_iron` | Bog Iron Deposit | `iron_ore` | 2 | 25 ticks | 3 |
| | `dark_moss` | Dark Moss Patch | `dark_moss` | 4 | 15 ticks | 1 |
| **MOUNTAIN** | `ore_vein` | Ore Vein | `iron_ore` | 3 | 25 ticks | 3 |
| | `crystal_node` | Crystal Node | `enchanted_dust` | 1 | 35 ticks | 4 |
| | `granite_quarry` | Granite Quarry | `stone_block` | 5 | 20 ticks | 2 |

Additionally, **Wild Berry Bushes** are placed on FLOOR tiles (8 total), yielding `wild_berries`.

### Node Placement

During world generation, `resources_per_region` nodes (default: 4) are placed per region. Nodes are positioned randomly within the region, constrained to matching terrain tiles.

### Lifecycle

```
Available (remaining > 0, cooldown = 0)
    │
    ▼ hero harvests
remaining -= 1, hero receives yields_item
    │
    ├── remaining > 0 → still available
    └── remaining == 0 → depleted
            │
            ▼ cooldown_remaining = respawn_cooldown
        Depleted (unavailable, grey on map)
            │ each tick: cooldown_remaining -= 1
            ▼ cooldown_remaining == 0
        Respawned (remaining = max_harvests)
```

---

## New Items

### Harvestable Materials (`src/core/items.py`)

| Item ID | Name | Type | Rarity | Sell Value |
|---------|------|------|--------|------------|
| `herb` | Herb | Material | Common | 4g |
| `wild_berries` | Wild Berries | Consumable | Common | 2g (heals 8 HP) |
| `raw_gem` | Raw Gem | Material | Uncommon | 15g |
| `fiber` | Fiber | Material | Common | 3g |
| `glowing_mushroom` | Glowing Mushroom | Material | Uncommon | 12g |
| `dark_moss` | Dark Moss | Material | Common | 3g |
| `stone_block` | Stone Block | Material | Common | 5g |

### Mob-Specific Loot

| Item ID | Name | Type | Rarity | Stats |
|---------|------|------|--------|-------|
| `wolf_pelt` | Wolf Pelt | Material | Common | — |
| `wolf_fang` | Wolf Fang | Material | Uncommon | — |
| `bandit_dagger` | Bandit Dagger | Weapon | Common | ATK +3, SPD +2 |
| `bandit_bow` | Bandit Bow | Weapon | Uncommon | ATK +5, CRIT +5% |
| `bone_shard` | Bone Shard | Material | Common | — |
| `ectoplasm` | Ectoplasm | Material | Uncommon | — |
| `orc_axe` | Orc Axe | Weapon | Uncommon | ATK +7, SPD -1 |
| `orc_shield` | Orc Shield | Armor | Uncommon | DEF +5, SPD -1 |

---

## Craftable Items from Race-Specific Materials

Seven new recipes at the blacksmith use race-specific materials, encouraging heroes to explore all terrain regions:

| Recipe | Output | Gold | Materials | Source Terrain |
|--------|--------|------|-----------|---------------|
| Wolf Cloak | `wolf_cloak` (DEF+3, SPD+2, EVA+4%) | 50g | 2× Wolf Pelt, 1× Leather | Forest |
| Fang Necklace | `fang_necklace` (ATK+2, CRIT+8%) | 45g | 2× Wolf Fang, 1× Fiber | Forest + Desert |
| Desert Composite Bow | `desert_bow` (ATK+6, SPD+1, CRIT+6%) | 75g | 1× Raw Gem, 2× Fiber | Desert |
| Bone Shield | `bone_shield` (DEF+5, HP+10) | 65g | 3× Bone Shard, 1× Dark Moss | Swamp |
| Spectral Blade | `spectral_blade` (ATK+9, CRIT+8%) | 180g | 2× Ectoplasm, 1× Enchanted Dust | Swamp + any |
| Mountain Plate | `mountain_plate` (DEF+7, SPD-2, HP+15) | 160g | 3× Stone Block, 2× Iron Ore | Mountain |
| Herbal Remedy | `herbal_remedy` (heal 25 HP) | 15g | 3× Herb, 1× Glowing Mushroom | Forest + Swamp |

New item templates are registered in `src/core/items.py` and recipes in `src/core/buildings.py`.

---

## HARVEST Action & HARVESTING AI State

### Enums (`src/core/enums.py`)

- **`ActionType.HARVEST`** (value 5) — New action verb for harvesting
- **`AIState.HARVESTING`** (value 14) — New AI state for channeling a harvest
- **`Domain.HARVEST`** (value 8) — New RNG domain for harvest-related rolls

### AI Behaviour (`src/ai/states.py: HarvestingHandler`)

The `HarvestingHandler` manages the full harvest lifecycle:

1. **Interrupt checks**: Flee if low HP; engage if enemy within 3 tiles
2. **Not on node**: Find nearest available resource within 8 tiles and move toward it
3. **On node**: Channel harvest (`loot_progress` increments each tick)
4. **Channel complete**: Propose `HARVEST` action with target position

Heroes discover resources while wandering via `WanderHandler`:
- After checking for loot, heroes with inventory space look for resources within 5 tiles
- If found, transition to `HARVESTING` state and move toward the node

### Action Processing (`src/engine/world_loop.py`)

`HARVEST` actions are processed alongside `USE_ITEM` and `LOOT` in `_process_item_actions`:

1. Look up the `ResourceNode` at the target position via `world.resource_at(pos)`
2. If node is available and entity has inventory space, call `node.harvest()`
3. Add the yielded item to entity's inventory
4. If inventory full, drop item on ground instead

### World Loop Integration

- `_tick_resource_nodes()` is called each tick in Phase 4 (Cleanup & Advancement)
- Each node's `tick_cooldown()` is invoked to count down depleted nodes toward respawn

---

## WorldState & Snapshot Changes

### WorldState (`src/core/world_state.py`)

New fields and methods:

| Field/Method | Description |
|-------------|-------------|
| `resource_nodes: dict[int, ResourceNode]` | All resource nodes by ID |
| `_next_node_id: int` | ID allocator for nodes |
| `add_resource_node(node)` | Register a node |
| `allocate_node_id()` | Get next unique node ID |
| `resource_at(pos)` | Find node at a given position |

### Snapshot (`src/core/snapshot.py`)

New field:

- `resource_nodes: tuple[ResourceNode, ...]` — Immutable copy of all resource nodes

---

## API Changes

### New Schema: `ResourceNodeSchema` (`src/api/schemas.py`)

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

### Updated: `WorldStateResponse`

New field added:

| Field | Type | Description |
|-------|------|-------------|
| `resource_nodes` | ResourceNodeSchema[] | All resource nodes with availability state |

### Updated: Material Values (GET /api/v1/map)

| Value | Name |
|-------|------|
| 0 | Floor |
| 1 | Wall |
| 2 | Water |
| 3 | Town |
| 4 | Camp |
| 5 | Sanctuary |
| 6 | **Forest** (new) |
| 7 | **Desert** (new) |
| 8 | **Swamp** (new) |
| 9 | **Mountain** (new) |

---

## Configuration Changes (`src/config.py`)

### Updated Defaults

| Parameter | Old | New | Reason |
|-----------|-----|-----|--------|
| `grid_width` | 64 | 128 | Larger map for terrain regions |
| `grid_height` | 64 | 128 | Larger map for terrain regions |
| `initial_entity_count` | 15 | 25 | More entities for larger map |
| `generator_spawn_interval` | 12 | 10 | Faster spawning |
| `generator_max_entities` | 50 | 80 | Higher cap for larger map |
| `town_center_x` | 5 | 12 | Centered for larger map |
| `town_center_y` | 5 | 12 | Centered for larger map |
| `town_radius` | 3 | 4 | Slightly larger town |
| `num_camps` | 5 | 8 | More camps for larger map |
| `camp_min_distance_from_town` | 15 | 25 | Proportional to map size |
| `sanctuary_radius` | 5 | 7 | Wider buffer zone |

### New Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_forest_regions` | 4 | Forest terrain region count |
| `num_desert_regions` | 3 | Desert terrain region count |
| `num_swamp_regions` | 3 | Swamp terrain region count |
| `num_mountain_regions` | 3 | Mountain terrain region count |
| `region_min_radius` | 6 | Minimum region radius |
| `region_max_radius` | 12 | Maximum region radius |
| `region_min_distance` | 8 | Minimum spacing between region centers |
| `resources_per_region` | 4 | Resource nodes spawned per region |
| `resource_respawn_ticks` | 30 | Default respawn cooldown |
| `harvest_duration` | 2 | Default harvest channel ticks |

---

## Frontend Changes

### Types (`frontend/src/types/api.ts`)

New interface:

```typescript
interface ResourceNode {
  node_id: number;
  resource_type: string;
  name: string;
  x: number;
  y: number;
  terrain: number;
  yields_item: string;
  remaining: number;
  max_harvests: number;
  is_available: boolean;
  harvest_ticks: number;
}
```

`WorldState` now includes `resource_nodes: ResourceNode[]`.

### Colors (`frontend/src/constants/colors.ts`)

**New terrain tile colors** (values 6–9) added to `TILE_COLORS` and `TILE_COLORS_DIM`.

**New mob kind colors:**

| Kind | Color |
|------|-------|
| `wolf` | `#a0a0a0` |
| `dire_wolf` | `#808080` |
| `alpha_wolf` | `#c0c0c0` |
| `bandit` | `#e0a050` |
| `bandit_archer` | `#d4943c` |
| `bandit_chief` | `#f0c060` |
| `skeleton` | `#b0b8c0` |
| `zombie` | `#70a070` |
| `lich` | `#c080ff` |
| `orc` | `#60a060` |
| `orc_warrior` | `#408040` |
| `orc_warlord` | `#80c040` |

**New state color:** `HARVESTING: #7dd3a0`

**Resource node colors** (`RESOURCE_COLORS`) — unique color per resource type for canvas rendering.

**Updated legend** includes all new mob categories, terrain types, and resource markers.

### Canvas Rendering (`frontend/src/hooks/useCanvas.ts`)

- **Resource nodes** are drawn on the entity layer as colored squares (filled at 50% opacity with 1px border)
- Depleted nodes render as grey at 30% opacity
- **Hover tooltips** show resource name, remaining harvests, and yielded item
- Fog-of-war correctly dims new terrain types using `TILE_COLORS_DIM[6–9]`

### Minimap (`frontend/src/components/GameCanvas.tsx`)

- Resource nodes appear on the minimap as small colored dots (green if available, grey if depleted)
- New mob races appear with their kind-specific colors

### Data Flow (`frontend/src/hooks/useSimulation.ts`)

- `resourceNodes` state added to the `SimulationState` interface
- Parsed from `state.resource_nodes` in the poll response
- Passed through `App.tsx → GameCanvas → useCanvas`

---

## File Map (New & Modified)

### New Files

| File | Description |
|------|-------------|
| `src/core/resource_nodes.py` | `ResourceNode` dataclass, `TERRAIN_RESOURCES` definitions |

### Modified Files

| File | Changes |
|------|---------|
| `src/core/enums.py` | Added `Material.FOREST/DESERT/SWAMP/MOUNTAIN`, `ActionType.HARVEST`, `AIState.HARVESTING`, `Domain.HARVEST` |
| `src/core/grid.py` | New terrains walkable, helper methods `is_forest`, `is_desert`, `is_swamp`, `is_mountain` |
| `src/core/faction.py` | Added `WOLF_PACK`, `BANDIT_CLAN`, `UNDEAD`, `ORC_TRIBE` factions with territory and relations |
| `src/core/items.py` | New harvestable materials, mob-specific weapons/armor, `RACE_*` tables, `TERRAIN_RACE` mapping |
| `src/core/world_state.py` | `resource_nodes` dict, `add_resource_node`, `allocate_node_id`, `resource_at` methods |
| `src/core/snapshot.py` | `resource_nodes` tuple field, deep-copied in `from_world` |
| `src/config.py` | Larger map (128×128), region params, resource params, adjusted town/camp settings |
| `src/systems/generator.py` | `spawn_race()` method for race-specific entity creation |
| `src/api/engine_manager.py` | Region generation, resource node placement, race mob spawning |
| `src/api/schemas.py` | `ResourceNodeSchema`, `resource_nodes` field in `WorldStateResponse` |
| `src/api/routes/state.py` | Serialize `resource_nodes` in state response |
| `src/engine/world_loop.py` | `_tick_resource_nodes()`, HARVEST action processing, HARVESTING goal text |
| `src/engine/conflict_resolver.py` | HARVEST action passthrough (validated in WorldLoop) |
| `src/ai/states.py` | `HarvestingHandler`, `find_nearby_resource` helper, resource-seeking in `WanderHandler` |
| `frontend/src/types/api.ts` | `ResourceNode` interface, `resource_nodes` in `WorldState` |
| `frontend/src/constants/colors.ts` | Terrain colors 6–9, mob colors, `HARVESTING` state, `RESOURCE_COLORS`, item display/stats |
| `frontend/src/hooks/useSimulation.ts` | `resourceNodes` state, parsing, exposure |
| `frontend/src/hooks/useCanvas.ts` | Resource node rendering, hover tooltips, dependency arrays |
| `frontend/src/components/GameCanvas.tsx` | `resourceNodes` prop, minimap rendering |
| `frontend/src/App.tsx` | Pass `resourceNodes` to `GameCanvas` |
