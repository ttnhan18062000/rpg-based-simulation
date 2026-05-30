# Investigation Notes - Phase 13 Schema Expansion

## Current Schema State
- Current catalog classes define Factions, Roles, Stats, Combat, Inventory, Cognition, Resources, Buildings, Services, Terrains, and Spawns.
- They lack definition models for Items, Enemies, Recipes, and Progression Regions.
- `CatalogValidator` exists and checks some basic bounds, but does not validate loot drop item_ids or region references.
