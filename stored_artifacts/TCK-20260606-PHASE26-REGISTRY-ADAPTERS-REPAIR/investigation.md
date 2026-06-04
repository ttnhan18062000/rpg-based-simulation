# Phase 26 Investigation

## Current Code Analysis
1. **`ItemDef` and `ItemRegistry`**:
   - `ItemDef` is a frozen dataclass in `src/core/registries.py` containing `id`, `tags`, `rarity`, `base_value`, `use_kind`, `class_fit`.
   - `CatalogToItemRegistryAdapter` translates catalog `ItemDefinition` records into `ItemDef` objects.
   - It checks `item.categories` to infer `use_kind`, and falls back to a hardcoded list of IDs for `class_fit`. We should add `use_kind` and `class_fit` to `ItemDefinition` in `src/content/schema.py` and have the adapter check them first.

2. **`ResourceDef` and `ResourceRegistry`**:
   - `ResourceDef` has `id`, `yield_item`, `source_region_tags`, `required_tool`, `base_difficulty`.
   - `CatalogToResourceRegistryAdapter` maps `wood_node` to `node_wood`, etc. It checks metadata for `source_region_tags`, `required_tool`, and `base_difficulty`.
   - We should add `legacy_id` and `required_tool` to `ResourceDefinition` in `src/content/schema.py` and check them first.

3. **`ServiceDef` and `ServiceRegistry`**:
   - `ServiceDef` has `id`, `region_id`, `supported_affordances`, `knowledge_scope`.
   - `CatalogToServiceRegistryAdapter` prepopulates `shop_hometown`, `blacksmith_hometown`, `guide_hometown`, `guild_hometown`, `inn_hometown`.
   - In catalog-backed mode, these should not be injected; they should be catalog records or compatibility records.
   - We should add `affordances` to `ServiceProfileDefinition` and check them first.

4. **`EnemyDef` and `EnemyRegistry`**:
   - `ArchetypeToEnemyRegistryAdapter` prepopulates `rat` if not present. In catalog mode, this fallback should not be seeded.

## Migration/Legacy Mode Flag
We can identify catalog-backed mode versus legacy mode by `runtime_content_source == "catalog"`.
The registries' bootstrap function is called in `seed_phase1_content`.
We can make sure that if `catalog_repo` is loaded, we run the adapters without injecting legacy fallback data (hometown services, fallback `rat` enemy), whereas in legacy backup mode we seed the hardcoded dicts.
Wait, let's verify if `CatalogToServiceRegistryAdapter` is always run with a `repo`. Yes, `seed_phase1_content` runs it with `catalog_repo`.
If `catalog_repo` is present:
- Do not inject hometown services in `CatalogToServiceRegistryAdapter` (unless they are loaded from catalog / metadata, or compatibility records).
- Do not inject `rat` in `ArchetypeToEnemyRegistryAdapter`.
- Fallbacks/heuristics should only be run if explicit values are missing.
