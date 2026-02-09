# Town Buildings & Economy System

This document describes the town building system, hero economy AI, crafting, and guild intel features.

## Overview

Three buildings are placed in the town during world generation:

| Building | Type | Position | Purpose |
|----------|------|----------|---------|
| **General Store** | `store` | Top-left of town | Buy/sell items |
| **Blacksmith** | `blacksmith` | Top-right of town | Learn recipes, craft items |
| **Adventurer's Guild** | `guild` | Bottom-center of town | Get camp intel, material hints |

Buildings are static locations (not entities). They are stored in `WorldState.buildings` and exposed in the API as part of `WorldStateResponse`.

## Data Model

### Building (`src/core/buildings.py`)

```python
@dataclass(slots=True)
class Building:
    building_id: str       # "store", "blacksmith", "guild"
    name: str
    pos: Vector2
    building_type: str     # "store" | "blacksmith" | "guild"
```

### Entity Extensions (`src/core/models.py`)

Two new fields on `Entity`:

- **`known_recipes: list[str]`** — Recipe IDs the hero has learned from the blacksmith
- **`craft_target: str | None`** — Recipe ID the hero is currently working toward

## Crafting Materials

Materials drop from enemies via the loot table system and from harvestable resource nodes across terrain regions.

### Goblin Drops

| Material | Rarity | Drop Source | Sell Value |
|----------|--------|-------------|------------|
| Wood | Common | Basic goblins, Timber nodes (forest) | 5g |
| Leather | Common | Goblins, scouts, wolves | 8g |
| Iron Ore | Uncommon | Warriors, orcs, camp raids, ore nodes | 10g |
| Steel Bar | Uncommon | Warriors (rare), orc warriors | 15g |
| Enchanted Dust | Rare | Elite goblins, liches, orc warlords, Crystal Nodes | 20g |

### Race-Specific Drops

| Material | Rarity | Source (Terrain) | Sell Value |
|----------|--------|-----------------|------------|
| Wolf Pelt | Common | Wolves (Forest) | 10g |
| Wolf Fang | Uncommon | Dire wolves, alpha wolves (Forest) | 14g |
| Fiber | Common | Bandits (Desert), Cactus Fiber nodes | 4g |
| Raw Gem | Uncommon | Bandit archers/chiefs (Desert), Gem Deposits | 18g |
| Bone Shard | Common | Skeletons, zombies (Swamp) | 6g |
| Ectoplasm | Uncommon | Zombies, liches (Swamp) | 16g |
| Dark Moss | Common | Skeletons (Swamp), Dark Moss Patches | 6g |
| Glowing Mushroom | Uncommon | Zombies (Swamp), Mushroom Groves | 12g |
| Stone Block | Common | Orcs (Mountain), Granite Quarries | 7g |
| Herb | Common | Herb Patch nodes (Forest) | 4g |

## General Store

### Selling

Heroes sell items they don't need:
- **Gold pouches/treasure** — always sold (converted to gold)
- **Materials** — sold unless needed for current craft target
- **Inferior equipment** — sold if hero has better gear equipped

Sell prices are based on rarity: Common 5g, Uncommon 15g, Rare 40g. Materials use their explicit `sell_value`.

### Buying

The store stocks consumables, basic equipment, and race-specific gear:

| Item | Buy Price |
|------|-----------|
| Small Health Potion | 15g |
| Medium Health Potion | 40g |
| Large Health Potion | 80g |
| Herbal Remedy | 20g |
| Wooden Club | 20g |
| Iron Sword | 50g |
| Bandit Dagger | 35g |
| Leather Vest | 25g |
| Chainmail | 60g |
| Orc Axe | 65g |
| Orc Shield | 70g |
| Lucky Charm | 30g |
| Speed Ring | 55g |

Heroes buy potions when low on stock (<2) and upgrade equipment when they can afford better gear.

## Blacksmith

### Recipe Learning

When a hero first visits the blacksmith, they learn all available recipes. The blacksmith also helps the hero choose a **craft target** — the most powerful item that would be an upgrade over current equipment.

### Recipes

#### Goblin-Material Recipes

| Recipe | Output | Gold Cost | Materials |
|--------|--------|-----------|-----------|
| Steel Sword | steel_sword | 60g | 2× Iron Ore, 1× Wood |
| Battle Axe | battle_axe | 90g | 3× Iron Ore, 1× Steel Bar |
| Enchanted Blade | enchanted_blade | 200g | 2× Steel Bar, 2× Enchanted Dust |
| Iron Plate | iron_plate | 70g | 3× Iron Ore, 1× Leather |
| Enchanted Robe | enchanted_robe | 150g | 2× Leather, 1× Enchanted Dust |
| Ring of Power | ring_of_power | 120g | 1× Iron Ore, 1× Enchanted Dust |
| Evasion Amulet | evasion_amulet | 80g | 2× Leather, 1× Wood |

#### Race-Specific Recipes

| Recipe | Output | Gold Cost | Materials | Source Terrain |
|--------|--------|-----------|-----------|---------------|
| Wolf Cloak | wolf_cloak | 50g | 2× Wolf Pelt, 1× Leather | Forest |
| Fang Necklace | fang_necklace | 45g | 2× Wolf Fang, 1× Fiber | Forest + Desert |
| Desert Composite Bow | desert_bow | 75g | 1× Raw Gem, 2× Fiber | Desert |
| Bone Shield | bone_shield | 65g | 3× Bone Shard, 1× Dark Moss | Swamp |
| Spectral Blade | spectral_blade | 180g | 2× Ectoplasm, 1× Enchanted Dust | Swamp + any |
| Mountain Plate | mountain_plate | 160g | 3× Stone Block, 2× Iron Ore | Mountain |
| Herbal Remedy | herbal_remedy | 15g | 3× Herb, 1× Glowing Mushroom | Forest + Swamp |

### Crafting Flow

1. Hero visits blacksmith → learns recipes → picks best upgrade as craft target
2. Hero goes adventuring to gather materials and gold
3. When hero has all required materials + gold, returns to blacksmith
4. Blacksmith consumes materials + gold, produces the item
5. Item is auto-equipped if it's better than current gear
6. `craft_target` is cleared after successful crafting

## Adventurer's Guild

### Camp Intel

The guild reveals all enemy camp locations (goblin, wolf, bandit, undead, orc) by adding them to the hero's `terrain_memory`. This gives the hero knowledge of where to find enemies for farming.

### Resource Node Intel

The guild also reveals the locations of all harvestable resource nodes across terrain regions, helping the hero discover crafting material sources without exploring every corner of the map.

### Material Hints

If the hero has a craft target, the guild provides tips about where to find each required material (covering all races and terrains). These are added to the hero's `goals` list for display.

### Terrain Tips

The guild provides general tips about which terrains host which races and materials:
- **Forests** → wolves → wolf pelts, wolf fangs
- **Deserts** → bandits → fiber, raw gems
- **Swamps** → undead → bone shards, ectoplasm
- **Mountains** → orcs → stone blocks, iron ore

## AI States

Three new AI states added to `AIState` enum:

| State | Value | Description |
|-------|-------|-------------|
| `VISIT_SHOP` | 11 | Hero is walking to or interacting with the store |
| `VISIT_BLACKSMITH` | 12 | Hero is walking to or interacting with the blacksmith |
| `VISIT_GUILD` | 13 | Hero is walking to or interacting with the guild |

### Economy Decision Flow

The hero's economy thinking is integrated into `RestingInTownHandler` (after fully healing):

1. **Sell items** — if hero has sellable items → `VISIT_SHOP`
2. **Buy upgrades** — if hero has enough gold for an upgrade → `VISIT_SHOP`
3. **Visit blacksmith** — if hero needs to learn recipes or can craft → `VISIT_BLACKSMITH`
4. **Visit guild** — if hero lacks camp intel → `VISIT_GUILD`
5. **Leave town** — if nothing to do → `WANDER`

Each handler moves the hero to the building, then performs the interaction when adjacent.

## API Schema

### BuildingSchema

```json
{
  "building_id": "store",
  "name": "General Store",
  "x": 3,
  "y": 3,
  "building_type": "store"
}
```

### WorldStateResponse additions

- `buildings: list[BuildingSchema]` — all buildings in the world

### EntitySchema additions

- `known_recipes: list[str]` — recipe IDs the entity knows
- `craft_target: str | null` — current crafting goal

## Frontend

### Tab Structure

The sidebar tabs are context-dependent:

| Context | Tabs Shown |
|---------|------------|
| No selection | **Info** (legend + entity list), **Events** (global log) |
| Spectating entity | **Inspect** (entity details with events sub-section) |
| Clicked building | **Inspect** → BuildingPanel (rich building info) |
| Clicked loot bag | **Inspect** → LootPanel (item details) |

### Building Panel

Clicking a building on the map opens its info panel:

- **Store**: shows buy inventory with prices, sell price tiers
- **Blacksmith**: shows all crafting recipes with materials and stats
- **Guild**: shows services (camp intel, material hints) and material source guide

### Canvas Rendering

Buildings are drawn on the entity canvas as colored square markers with letter labels:
- **S** (blue) — Store
- **B** (amber) — Blacksmith
- **G** (purple) — Guild

Buildings also appear as colored dots on the minimap.

### InspectPanel Changes

- **Craft Target** collapsible section (hero only) shows current crafting goal
- **Entity Events** collapsible sub-section shows filtered events for the spectated entity
- Sections are collapsible with chevron toggles

## File Map

| File | Changes |
|------|---------|
| `src/core/enums.py` | Added `MATERIAL` to `ItemType`, `VISIT_SHOP`/`VISIT_BLACKSMITH`/`VISIT_GUILD` to `AIState` |
| `src/core/items.py` | Added `sell_value` to `ItemTemplate`, 5 material items, updated loot tables |
| `src/core/buildings.py` | **New** — `Building` dataclass, `Recipe`, shop/guild config, economy helpers |
| `src/core/models.py` | Added `known_recipes`, `craft_target` fields to `Entity` |
| `src/core/world_state.py` | Added `buildings: list[Building]` |
| `src/core/snapshot.py` | Added `buildings` to `Snapshot` |
| `src/api/engine_manager.py` | Places 3 buildings in town during world generation |
| `src/api/schemas.py` | Added `BuildingSchema`, `RecipeSchema`, `ShopItemSchema`; updated `EntitySchema` and `WorldStateResponse` |
| `src/api/routes/state.py` | Serializes buildings + new entity fields |
| `src/ai/states.py` | Economy helpers, `VisitShopHandler`, `VisitBlacksmithHandler`, `VisitGuildHandler`, economy thinking in `RestingInTownHandler` |
| `frontend/src/types/api.ts` | Added `Building` interface, `known_recipes`/`craft_target` on `Entity`, `buildings` on `WorldState` |
| `frontend/src/constants/colors.ts` | New AI state colors, material item displays/stats, building legend entries |
| `frontend/src/hooks/useSimulation.ts` | Exposes `buildings` state |
| `frontend/src/hooks/useCanvas.ts` | Renders building markers on entity canvas |
| `frontend/src/components/GameCanvas.tsx` | Passes buildings to canvas, renders on minimap |
| `frontend/src/components/Sidebar.tsx` | Context-dependent tab restructure |
| `frontend/src/components/BuildingPanel.tsx` | **New** — Store/Blacksmith/Guild info panels |
| `frontend/src/components/InspectPanel.tsx` | Added Craft Target section, Entity Events sub-section |
| `frontend/src/App.tsx` | Building selection state, click-to-inspect buildings |
