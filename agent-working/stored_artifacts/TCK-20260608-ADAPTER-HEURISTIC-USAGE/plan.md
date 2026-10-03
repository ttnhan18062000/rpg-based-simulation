---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-ADAPTER-HEURISTIC-USAGE
artifact_type: plan
tags: [adapter, heuristic, usage]
---

# Plan — TCK-20260608-ADAPTER-HEURISTIC-USAGE

## Steps

1. **Update AdapterProjectionResult** (src/core/registries.py)
   - Replace `heuristic_count: int` field with `heuristic_usages: tuple`
   - Add `heuristic_count` property returning `len(self.heuristic_usages)`
   - Update `seed_phase1_content` to aggregate tuples instead of ints

2. **Update CatalogToItemRegistryAdapter.adapt()**
   - Replace `heuristic_count = 0` with `heuristic_usages: list[AdapterHeuristicUsage] = []`
   - Emit `AdapterHeuristicUsage(record_id=item_id, family="item", adapter="CatalogToItemRegistryAdapter", heuristic_type="use_kind", reason="...", mode=self.mode)` for use_kind heuristic
   - Emit `AdapterHeuristicUsage(..., heuristic_type="class_fit", ...)` for class_fit heuristic
   - Return `(items, tuple(heuristic_usages))`

3. **Update CatalogToServiceRegistryAdapter.adapt()**
   - Same pattern; emit heuristic for affordances inference
   - Return `(services, tuple(heuristic_usages))`

4. **Update CatalogToResourceRegistryAdapter.adapt()**
   - Same pattern for legacy_id and source_region_tags (existing heuristics)
   - Additionally track required_tool and base_difficulty inferences
   - Return `(resources, tuple(heuristic_usages))`

5. **Update seed_phase1_content()**
   - Aggregate: `all_heuristic_usages = items_heuristic + services_heuristic + resources_heuristic`
   - Pass `heuristic_usages=all_heuristic_usages` to AdapterProjectionResult
   - Add CATALOG_STRICT guard after aggregation: if mode == CATALOG_STRICT and all_heuristic_usages: raise AdapterError

6. **Fix test_registry_bridge.py** — update the 4 failing tests:
   - Replace MIGRATION/V2 references with CATALOG_WITH_COMPATIBILITY/CATALOG_STRICT
   - Update enum count assertion (was 2, now 4)
   - Update AdapterProjectionResult constructor call to use heuristic_usages kwarg

7. **Create tests/unit/content/test_adapter_heuristic_reporting.py**

## Scope Guards
- Do not touch ArchetypeToEnemyRegistryAdapter (no heuristics to track)
- Do not touch CatalogToRecipeRegistryAdapter (no heuristic counting)
- Do not change heuristic inference logic (only tracking)
- Do not change CATALOG_STRICT per-heuristic raise behavior in adapters

## Deviations
None.
