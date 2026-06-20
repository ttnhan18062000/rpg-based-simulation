---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13C-RECIPES
artifact_type: test_plan
tags: [content, crafting-recipes, economy]
---

# Test Plan: TCK-20260619-E13C-RECIPES — Crafting Recipe Expansion

## Test Scope

Pure content data change — recipes.yaml expanded from 8 to 25+ entries.
No engine code changes. Tests verify:
1. Catalog loads cleanly
2. Recipe count ≥ 25
3. All ingredient/output item IDs exist in item catalog
4. gather→craft chain is complete (iron_ore → steel → ember_axe)
5. All service IDs in recipes exist in services.yaml

## Test Strategy

### 1. Smoke: CatalogRepository.load_all() passes
```bash
python3 -c "from src.content.repository import CatalogRepository; r = CatalogRepository('data/content'); r.load_all(); print('OK')"
```
Expected: prints "OK" with no errors.

### 2. Count check
```bash
grep "^- id:" data/content/world/recipes.yaml | wc -l
```
Expected: ≥ 25

### 3. Unit tests — new file: tests/unit/content/test_recipe_catalog_expansion.py
Tests to write:
- `test_recipe_count_at_least_25`: loads recipes.yaml, asserts len ≥ 25
- `test_gather_craft_chain_iron_to_steel`: verifies smelt_iron_to_steel recipe exists, iron_ore in ingredients, outputs steel
- `test_gather_craft_chain_steel_to_ember_axe`: verifies craft_ember_axe recipe, steel + ember_core → ember_axe
- `test_all_recipe_ingredients_are_valid_items`: every ingredient ID across all recipes exists in items.yaml
- `test_all_recipe_outputs_are_valid_items`: every output ID across all recipes exists in items.yaml
- `test_all_recipe_services_exist`: every required_service ID in recipes exists in services.yaml
- `test_service_coverage_all_types`: at least one recipe each for blacksmith_service, healer_service, arcane_service, general_store_service
- `test_catalog_load_includes_new_recipes`: CatalogRepository.load_all() report shows recipes count ≥ 25

### 4. Catalog integration check (existing AC)
Run: `pytest tests/unit/content/test_recipe_catalog_expansion.py -v`

## Test Data Dependencies
- `data/content/world/recipes.yaml` (expanded)
- `data/content/world/items.yaml` (reference — unchanged)
- `data/content/world/services.yaml` (reference — unchanged)

## Out of Scope
- Engine crafting execution tests (would require blacksmith system)
- Recipe discovery tests
- Multi-actor crafting race conditions
