# Epic 10: Enchantment & Item Progression

## Summary

Add an item enchantment system that lets heroes enhance their equipment with stat bonuses, elemental effects, and special properties. Items gain upgrade levels (+1, +2, etc.) and can be socketed with gems for additional effects. This creates a deep item progression loop beyond simply finding better gear.

Inspired by: Diablo gem socketing, Dark Souls weapon reinforcement, Path of Exile crafting, Korean MMO enhancement systems.

---

## Motivation

- Current item progression is flat: find or craft a better item, equip it, done
- No way to improve existing gear — encourages constant replacement over investment
- Enchantment adds attachment to gear and meaningful gold sinks
- Gem socketing creates build diversity (same weapon, different gem = different playstyle)
- Aligns with "realistic RPG simulation" — RPG heroes improve their trusted weapons over time

---

## Features

### F1: Item Enhancement (+1 to +10)
- Any equipment item (weapon, armor, accessory) can be enhanced at the Blacksmith
- Each enhancement level increases the item's base stat bonuses by 10%
- Enhancement costs gold, scaling per level: `base_cost * (1 + level * 0.5)`
- Enhancement success rate decreases at higher levels:
  - +1 to +5: 100% success
  - +6 to +8: 80% / 60% / 40%
  - +9 to +10: 25% / 15%
- Failed enhancement: item loses 1 level (minimum +0) — or consumes a protection material to prevent loss
- Uses `Domain.ITEM` RNG for deterministic success rolls
- **Extensibility:** Enhancement table defined as data (`EnhancementTier` dataclass with cost, rate, bonus)

### F2: Gem Socket System
- Equipment items can have 0–3 sockets (based on rarity: Common=0, Uncommon=1, Rare=2, Epic=3)
- Gems are a new `ItemType.GEM` category
- Socketing is permanent (gems cannot be removed without destroying them)
- **Extensibility:** Gem effects defined in `GemDef` dataclass; new gems = new data entries

### F3: Gem Types

| Gem | Effect | Source |
|-----|--------|--------|
| Ruby | +ATK, +fire damage | Mountain ore veins, treasure chests |
| Sapphire | +MDEF, +ice resistance | Swamp mushroom groves |
| Emerald | +HP regen, +VIT | Forest herb patches |
| Topaz | +SPD, +lightning damage | Desert gem deposits |
| Onyx | +crit rate, +dark damage | Dungeon drops, lich loot |
| Diamond | +all stats (small) | Legendary chest drops only |

### F4: Item Rarity Upgrade
- New building service or Blacksmith upgrade: combine 3 items of the same rarity to create 1 item of the next rarity
- Common + Common + Common → Uncommon (random item of same type)
- Uncommon × 3 → Rare
- Adds a new `Rarity.EPIC` tier beyond Rare
- Epic items have: higher base stats, 3 gem sockets, unique visual glow
- **Extensibility:** Rarity upgrade recipes defined in a registry, not hard-coded

### F5: Item Set Bonuses
- Certain items form named sets (2–4 pieces)
- Equipping multiple pieces from a set grants bonus effects:
  - 2-piece: minor stat bonus
  - 3-piece: significant stat bonus + special passive
  - 4-piece: powerful set effect (e.g. "attacks have 10% chance to chain to nearby enemy")
- Example sets:
  - **Wolf Hunter Set** (wolf_cloak + fang_necklace): 2pc: +15% crit in FOREST terrain
  - **Mountain King Set** (mountain_plate + orc_axe + ring_of_power): 3pc: +20% ATK, +10% DEF
- **Extensibility:** `ItemSetDef` registry with piece IDs and tier bonuses

### F6: AI Enhancement Decisions
- Heroes evaluate enhancement value when visiting the Blacksmith
- Priority: enhance primary weapon first, then armor, then accessory
- Heroes socket gems that match their class (Warrior→Ruby, Mage→Sapphire, etc.)
- Enhancement goal integrated into `CraftGoal` scorer
- **Extensibility:** Enhancement AI priorities defined per class in config data

### F7: Frontend
- Enhanced items show "+N" suffix in tooltips and inventory (e.g. "Iron Sword +5")
- Socket display: gem icons below item name in tooltip
- Enhancement success/failure events in event log
- BuildingPanel Blacksmith section shows enhancement UI with success rates
- Epic rarity items have a purple glow in inventory/equipment display

---

## Design Principles

- Enhancement levels stored as a field on `Inventory` item entries (not on `ItemTemplate`)
- Gem sockets stored per-item as `list[str | None]` (gem IDs or empty slots)
- All enhancement mechanics flow through existing WorldLoop action processing
- Success rolls use `Domain.ITEM` RNG for determinism
- Item set detection runs when equipment changes, caches result on entity

---

## Dependencies

- Blacksmith building (already exists)
- Item template system (already exists)
- Crafting system (already exists)
- Status effect system for set bonuses (already exists)
- Element system for gem damage types (already exists)

---

## Estimated Scope

- Backend: ~8 files new/modified
- Frontend: ~4 files modified (tooltips, BuildingPanel, InspectPanel, colors)
- Data: Enhancement tables, gem definitions, item set definitions
