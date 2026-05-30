# Investigation Notes - Phase 15 Registry Bridge

## Registries Analysis
We have two central registries for items:
1. `src/core/registries.py`: Contains `ItemRegistry` storing `ItemDef`. Used for recipes, loot tables, and legacy definitions.
2. `src/core/items.py`: Contains `ItemRegistry` storing `ItemDefinition`. Used for gameplay components, inventories, and equipment slots.

We also have:
- `ResourceRegistry` (`ResourceDef`): Yield item, source region tags, required tool, and base difficulty.
- `EnemyRegistry` (`EnemyDef`): Danger hint, hp, atk, def, loot table, spawn regions.
- `RecipeRegistry` (`RecipeDef`): Gold cost, required service, ingredients, output item.
- `ServiceRegistry` (`ServiceDef`): Region ID, supported affordances.
- `RegionRegistry` (`RegionDef`): Region name, tags, danger level.

## Mapping Challenges & Strategies
- **Categories to ItemKind**: Categories in `items.yaml` are lists like `["weapon", "melee"]`. We will check for keywords to map to the `ItemKind` enum:
  - `"weapon"` -> `ItemKind.WEAPON`
  - `"armor"` -> `ItemKind.ARMOR`
  - `"consumable"` -> `ItemKind.CONSUMABLE`
  - `"currency"` -> `ItemKind.CURRENCY`
  - Default -> `ItemKind.MATERIAL`
- **EquipSlot mapping**: For weapons and armor, map slots to `EquipSlot.MAIN_HAND` and `EquipSlot.TORSO` respectively.
- **Service mapping**: Map catalog `service_type` (e.g. `"trade"`, `"crafting"`, `"rest"`) to legacy supported affordances. Register legacy expected services like `guide_hometown` and `guild_hometown` directly to prevent failures in systems that depend on them.
- **Resource tags**: Map `preferred_biomes` to region tags. Support both legacy and catalog resource IDs.
