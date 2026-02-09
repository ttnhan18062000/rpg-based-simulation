# Inventory & Equipment System

Technical documentation for the item, inventory, and equipment mechanics.

---

## Overview

Every entity can carry an `Inventory` containing items, with three dedicated equipment slots (weapon, armor, accessory). Items provide stat bonuses when equipped and consumable effects when used.

**Primary file**: `src/core/items.py`

---

## Item Templates

All items are defined as `ItemTemplate` dataclass instances and registered in the global `ITEM_REGISTRY` dictionary.

### ItemTemplate Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier (e.g. `iron_sword`) |
| `name` | str | Display name |
| `item_type` | ItemType | WEAPON (0), ARMOR (1), ACCESSORY (2), CONSUMABLE (3) |
| `rarity` | Rarity | COMMON, UNCOMMON, RARE, EPIC |
| `weight` | float | Weight units consumed in inventory |
| `atk_bonus` | int | ATK stat bonus when equipped |
| `def_bonus` | int | DEF stat bonus when equipped |
| `spd_bonus` | int | SPD stat bonus when equipped |
| `max_hp_bonus` | int | Max HP bonus when equipped |
| `crit_rate_bonus` | float | Crit rate bonus when equipped |
| `evasion_bonus` | float | Evasion bonus when equipped |
| `heal_amount` | int | HP restored on use (consumables only) |

### Registered Items

#### Weapons
| ID | Name | ATK | SPD | Crit | Weight |
|----|------|-----|-----|------|--------|
| `rusty_dagger` | Rusty Dagger | +2 | +1 | +0.02 | 1.0 |
| `iron_sword` | Iron Sword | +5 | 0 | +0.03 | 2.0 |
| `goblin_blade` | Goblin Blade | +3 | +2 | +0.05 | 1.5 |
| `chief_axe` | Chief's Axe | +8 | -1 | +0.05 | 3.0 |

#### Armor
| ID | Name | DEF | HP | Evasion | Weight |
|----|------|-----|----|---------|--------|
| `leather_vest` | Leather Vest | +3 | +5 | 0 | 2.0 |
| `chainmail` | Chainmail | +6 | +10 | 0 | 4.0 |
| `goblin_shield` | Goblin Shield | +2 | 0 | +0.03 | 1.5 |
| `chief_plate` | Chief's Plate | +10 | +20 | 0 | 5.0 |

#### Accessories
| ID | Name | Bonus | Weight |
|----|------|-------|--------|
| `speed_ring` | Speed Ring | +3 SPD, +0.02 evasion | 0.5 |
| `lucky_charm` | Lucky Charm | +2 ATK, +0.05 crit | 0.5 |

#### Consumables
| ID | Name | Heal | Weight |
|----|------|------|--------|
| `small_hp_potion` | Small HP Potion | 20 HP | 0.5 |
| `medium_hp_potion` | Medium HP Potion | 40 HP | 0.5 |
| `large_hp_potion` | Large HP Potion | 80 HP | 0.5 |

---

## Inventory Class

```python
@dataclass
class Inventory:
    items: list[str]          # Item IDs in the bag
    max_slots: int = 8        # Maximum number of items
    max_weight: float = 20.0  # Maximum total weight
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None
```

### Capacity Limits

| Entity Type | Max Slots | Max Weight |
|-------------|-----------|------------|
| Hero | 12 | 50.0 |
| Goblin (all tiers) | 4 | 15.0 |

Configured in `SimulationConfig` as `hero_inventory_slots`, `hero_inventory_weight`, `goblin_inventory_slots`, `goblin_inventory_weight`.

### Key Methods

| Method | Description |
|--------|-------------|
| `add_item(item_id)` | Add item to bag if slots and weight allow. Returns bool. |
| `remove_item(item_id)` | Remove first occurrence of item from bag. Returns bool. |
| `equip(item_id)` | Equip item into matching slot (weapon/armor/accessory). Swaps if slot occupied. |
| `equipment_bonus(attr)` | Sum a stat bonus attribute across all equipped items. |
| `get_all_item_ids()` | Returns all items: bag + equipped items (for loot drops). |
| `used_slots` | Property returning current item count in bag. |
| `current_weight` | Property returning total weight of bag items. |
| `copy()` | Deep copy for snapshot generation. |

### Equipment Bonus Calculation

Effective stats are computed via `Entity.effective_*()` methods:

```python
def effective_atk(self) -> int:
    base = self.stats.atk
    if self.inventory:
        base += int(self.inventory.equipment_bonus("atk_bonus"))
    return max(base, 1)
```

This pattern is used for: `effective_atk()`, `effective_def()`, `effective_spd()`, `effective_crit_rate()`, `effective_evasion()`, `effective_max_hp()`.

---

## Loot Tables

Each enemy tier has a loot table defining possible item drops with weights:

```python
TIER_LOOT_TABLES = {
    EnemyTier.BASIC: [
        ("small_hp_potion", 5),
        ("rusty_dagger", 2),
        ("leather_vest", 1),
    ],
    EnemyTier.SCOUT: [
        ("small_hp_potion", 4),
        ("goblin_blade", 3),
        ("speed_ring", 1),
    ],
    # ...
}
```

The `roll_loot(tier, rng, eid, tick)` function selects a random item from the table using weighted selection via the deterministic RNG.

---

## Starting Gear

Each enemy tier spawns with predefined equipment:

```python
TIER_STARTING_GEAR = {
    EnemyTier.BASIC: {},
    EnemyTier.SCOUT: {"weapon": "goblin_blade"},
    EnemyTier.WARRIOR: {"weapon": "goblin_blade", "armor": "goblin_shield"},
    EnemyTier.ELITE: {"weapon": "chief_axe", "armor": "chief_plate"},
}
```

The hero starts with: `iron_sword` (weapon), `leather_vest` (armor), 3x `small_hp_potion`.

---

## Ground Loot

### Drop Mechanics
When an entity dies, all inventory items + equipped items are dropped at the death position:

```python
# In WorldLoop._phase_cleanup()
if entity.inventory:
    dropped = entity.inventory.get_all_item_ids()
    if dropped:
        world.drop_items(entity.pos, dropped)
```

Ground items are stored in `WorldState.ground_items: dict[tuple[int,int], list[str]]`.

### Pickup Mechanics
The hero AI enters `LOOTING` state when ground loot is detected nearby. The `LOOT` action is processed in `WorldLoop._process_item_actions()`:

1. Items are removed from ground
2. Each item is added to entity inventory if space allows
3. Equipment items are auto-equipped if the slot is empty
4. Items that can't be carried are dropped back to the ground

### Hero Death
On death, the hero drops carried bag items but keeps equipment slots. The hero respawns at town with cleared bag.

---

## Potion System

### Auto-Use in Combat
During the `COMBAT` AI state, if an entity's HP drops below 50%, it will propose a `USE_ITEM` action instead of attacking:

```python
# Priority: large > medium > small
for potion_id in ["large_hp_potion", "medium_hp_potion", "small_hp_potion"]:
    if potion_id in entity.inventory.items:
        return ActionProposal(verb=ActionType.USE_ITEM, target=potion_id, ...)
```

### Processing
In `WorldLoop._process_item_actions()`:
1. Remove potion from inventory
2. Heal entity by `template.heal_amount`, capped at `effective_max_hp()`
3. Add 0.5 action time delay (half a normal action)
