# Implementation Plan - Phase 15 Registry Bridge

This plan integrates the content catalog database with the legacy simulation registries by implementing an authoritative bootstrapping bridge.

## Proposed Changes

### Component 1: src/core/items.py
* Add `bootstrap(cls, data: Dict[str, ItemDefinition] | List[Any] | Dict[str, Any])` to `ItemRegistry`.
* Implement a parser that maps Pydantic `ItemDefinition` objects from the catalog into runtime `ItemDefinition` dataclasses:
  - Convert categories to `ItemKind`.
  - Resolve slots, attack/defense bonuses, healing amounts, and recovery values into the `properties` dictionary.
  - Set default stack size and weight values based on item type.

### Component 2: src/core/registries.py
* Update `seed_phase1_content()` to accept `catalog_repo: Optional[CatalogRepository] = None`.
* If `catalog_repo` is supplied:
  - Parse and bootstrap `ItemRegistry` with legacy `ItemDef` objects.
  - Parse and bootstrap `ResourceRegistry` with legacy `ResourceDef` objects (mapping `preferred_biomes` to region tags).
  - Parse and bootstrap `EnemyRegistry` with legacy `EnemyDef` objects by joining `LegacyEnemyProjectionDefinition` with `EntityArchetypeDefinition` and `StatsProfileDefinition`.
  - Parse and bootstrap `RecipeRegistry` with legacy `RecipeDef` objects.
  - Parse and bootstrap `ServiceRegistry` with legacy `ServiceDef` objects.
  - Parse and bootstrap `RegionRegistry` with legacy `RegionDef` objects.
  - Log `runtime_content_source = "catalog"` along with the catalog fingerprint.
* If `catalog_repo` is omitted:
  - Fall back to the legacy hardcoded seeding.
  - Log `runtime_content_source = "legacy_hardcoded"`.

## Verification Plan

### Automated Tests
* Create `tests/unit/core/test_registry_bridge.py` to:
  - Bootstrap registries using a mock `CatalogRepository` with custom YAML structures.
  - Assert that all mappers resolve values, slots, and properties correctly.
  - Run the full existing unit test suite to verify zero regressions.
