# Plan — TCK-20260609-ARCHETYPE-ENTITY-FACTORY

## Steps
1. Create EntitySpawnContext frozen dataclass in src/entities/archetype_factory.py
2. Create ArchetypeEntityFactory.build_entity() using V2EntityBuilder internally
3. Map contract fields: combat (hp/max_hp/atk/def_stat/attack_range/readiness/alive), identity (role/faction/traits/properties), inventory (items/gold), navigation (position)
4. Store archetype/race/faction/role/profile IDs in IdentityComponent.properties
5. Helper functions _replace_inventory() and _replace_lifecycle() for frozen dataclass replacement
6. Write 12 tests covering all 5 named test cases + additional coverage

## Deviations
None.
