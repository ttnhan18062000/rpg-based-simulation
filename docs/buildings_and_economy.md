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
