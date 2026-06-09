# Investigation — TCK-20260609-ARCHETYPE-ENTITY-FACTORY

## Findings
- V2EntityBuilder in src/core/builder.py:78 is the existing entity construction path
- EntityState fields: id, kind, plus components (identity, combat, inventory, navigation, lifecycle, etc.)
- CombatComponent.range maps to contract.attack_range (builder accepts attack_range kwarg)
- InventoryComponent.gold: int (contract.starting_gold is float, truncate to int)
- IdentityComponent.properties: Dict[str, Any] — used to store archetype/race/faction/role string IDs and profile IDs
- V2EntityBuilder._component() helper filters only valid dataclass fields
- LifecycleComponent.active controls entity active state

## Architecture constraints
- Factory must not import CatalogRepository
- Profile IDs stored in properties, not dropped
