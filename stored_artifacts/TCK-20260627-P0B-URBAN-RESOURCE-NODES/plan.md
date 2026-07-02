---
status: active
layer: world
authority: P0
audience: agent
ticket_id: TCK-20260627-P0B-URBAN-RESOURCE-NODES
artifact_type: plan
tags: [p0, resource-nodes, urban-political, hotfix]
---

# Plan — TCK-20260627-P0B-URBAN-RESOURCE-NODES

## Ordered Steps

### Step 1 — Add resource_recipes to `frontier_village_core` module

**File**: `data/content/world_modules/frontier_village_core.yaml`

Add two resource_recipes using regions that the module itself defines (`hometown`):
- `wood_node` (count 8) — suitable for frontier village (wood for building/crafting)
- `herb_patch` (count 5) — healer's herb supply

Both use catalog IDs validated against `data/content/world/resources.yaml`.
Region `hometown` is defined by this module → module validation passes.

**AC covered**: AC1 (nodes added), AC2 (region_id `hometown` is valid)

### Step 2 — Add resource_recipes to `trading_company_hub` module

**File**: `data/content/world_modules/trading_company_hub.yaml`

Add one resource_recipe using the module's own `hometown` region (which gets
namespace-prefixed to `trading_hometown` during assembly when used in urban_political):
- `iron_vein` (count 6) — materials for trade/blacksmith activity

Region `hometown` is defined by this module → module validation passes.
Assembly prefix `trading_` → final region `trading_hometown` in resolved WorldSpec.

**AC covered**: AC1 (third node), AC2 (assembled region_id `trading_hometown` is valid)

### Step 3 — Re-run world-resolve to regenerate resolved files

**Command**: `make world-resolve WORLD=urban_political`  
This updates `data/worlds/urban_political/resolved/world.resolved.yaml` and
`compile_context.json` with the new resource entries.

### Step 4 — Verify CLI compilation

**Command**: `make world-compile WORLD=urban_political`  
Assert `resource_node_count >= 3` in report output and JSON.

**AC covered**: AC3

### Step 5 — Add resource node count assertion to integration test

**File**: `tests/integration/worldassembly/test_e2e_smoke.py`  
Add to `test_smoke_urban_political_compiles_to_authoritative_state`:
```python
assert report["resource_node_count"] >= 3, (
    f"urban_political must have >= 3 resource nodes, got {report['resource_node_count']}"
)
assert len(state.resource_nodes) >= 3
```

**AC covered**: AC3 (test gate), AC4 (tests pass)

### Step 6 — Run scoped tests

```
pytest tests/integration/worldassembly/ -k "urban_political or frontier" -m "not slow" -v
```

## Scope Guards

- Do NOT modify `data/content/world_compositions/urban_political.yaml` (content composition
  used by tests — `len(spec.module_refs) == 3` assertion must remain valid)
- Do NOT modify `data/worlds/urban_political/world.yaml` module_refs (not needed — modules
  already referenced provide the new resources)
- Do NOT modify `ResourceOpportunityProvider` (out of scope per ticket)
- Do NOT add resources to `bandit_road_trade_pressure` (not needed for ≥3 count)

## AC-to-Step Mapping

| AC | Step |
|---|---|
| ≥3 nodes in world definition | 1, 2 |
| Valid region_id for each | 1, 2 |
| make world-compile ≥3 nodes | 3, 4 |
| Existing tests pass | 5, 6 |

## Deviations (fill after implementation)

_None yet._
