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
