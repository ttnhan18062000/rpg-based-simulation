# Plan - Phase 26

We will extract the registry adapters into `src/core/registries.py` (or a dedicated adapter module if appropriate, but keeping it in `registries.py` keeps it close to the registry definitions and `seed_phase1_content()`).
Let's see what each adapter needs to map:

1. `CatalogToItemRegistryAdapter`:
   - Inputs: `CatalogRepository` or iterable of `ItemDefinition`. Let's take `CatalogRepository` or specifically items map to be flexible. Let's make them accept `CatalogRepository` or specific items. Taking the definition/catalog is good. Let's take `ItemDefinition` or `CatalogRepository`. Let's design them to accept the relevant definitions, e.g. mapping `ItemDefinition` to `ItemDef`.
   - `ItemDef` fields:
     - `id: str`
     - `tags: Tuple[str, ...]` (from `item.categories`)
     - `rarity: str`
     - `base_value: int`
     - `use_kind: str` (derived via categories rule)
     - `class_fit: Tuple[str, ...]` (derived via metadata/fallback)

2. `CatalogToRecipeRegistryAdapter`:
   - Maps `RecipeDefinition` to `RecipeDef`.
   - `RecipeDef` fields:
     - `id: str` (derived with `craft_` stripped)
     - `requires_items: Dict[str, int]` (ingredients)
     - `service_req: str` (service name mapping blacksmith/healer etc)
     - `gold_cost: int`
     - `output_item_id: str` (first output item ID)

3. `CatalogToServiceRegistryAdapter`:
   - Maps `ServiceDefinition` to `ServiceDef`.
   - `ServiceDef` fields:
     - `id: str`
     - `region_id: str` (defaulting to "hometown" or extracted from definition/metadata)
     - `supported_affordances: Tuple[str, ...]` (derived from id/provided_items)
     - `knowledge_scope: Tuple[str, ...]` (default/empty or metadata)

4. `CatalogToRegionRegistryAdapter`:
   - Maps `RegionDefinition` to `RegionDef`.
   - `RegionDef` fields:
     - `id: str`
     - `name: str` (display_name or formatted id)
     - `tags: Tuple[str, ...]`
     - `danger_level: int`

5. `CatalogToResourceRegistryAdapter`:
   - Maps `ResourceDefinition` to `ResourceDef`.
   - `ResourceDef` fields:
     - `id: str` (maps wood_node -> node_wood, etc. and keeps both if needed, or maps to legacy ID)
     - `yield_item: str`
     - `source_region_tags: Tuple[str, ...]` (derived from Preferred region / biomes tags)
     - `required_tool: Optional[str]`
     - `base_difficulty: int`

6. `ArchetypeToEnemyRegistryAdapter`:
   - Maps `LegacyEnemyProjectionDefinition` (and archetypes/stats profiles) to `EnemyDef`.
   - `EnemyDef` fields:
     - `id: str`
     - `danger_hint: str`
     - `max_hp: int` (from stats profile of archetype)
     - `atk: int`
     - `def_stat: int`
     - `loot_table: Dict[str, float]`
     - `spawn_regions: Tuple[str, ...]`

We will define these adapters, write unit tests for each, rewrite `seed_phase1_content()` to use them, and write registry parity tests.
