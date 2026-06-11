---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE26-REGISTRY-ADAPTERS-REPAIR
artifact_type: test_plan
tags: [phase26, registry, adapters, repair]
---

# Phase 26 Test Plan

## Unit/Integration Tests
We will add a new test file: `tests/integration/content/test_registry_projection_parity.py`.
It will contain data-driven tests:
1. `test_item_registry_parity`: For each active item definition in `CatalogRepository`, check that it exists in `ItemRegistry` with correct attributes, prioritizing explicit `use_kind` and `class_fit`.
2. `test_recipe_registry_parity`: Check recipe definitions.
3. `test_service_registry_parity`: Check service definitions. Verify hometown services are not injected when booting from catalog.
4. `test_region_registry_parity`: Check region definitions.
5. `test_enemy_projection_registry_parity`: Check that enemy projections from `legacy_enemy_projections` are present, and `rat` is not injected in catalog mode if not in catalog.

We will also add unit tests verifying that:
- `test_item_adapter_uses_explicit_use_kind`
- `test_item_adapter_uses_explicit_class_fit`
- `test_resource_adapter_uses_explicit_legacy_id`
- `test_service_adapter_does_not_inject_default_service_in_catalog_mode`
- `test_fallback_enemy_not_seeded_in_catalog_mode`
- `test_fallback_usage_reported_in_legacy_mode`

## Execution Command
```bash
pytest tests/unit/content/ -k "adapter" -v
pytest tests/integration/content/ -v
```
