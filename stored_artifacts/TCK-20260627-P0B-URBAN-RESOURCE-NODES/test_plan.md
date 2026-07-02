---
status: active
layer: world
authority: P0
audience: agent
ticket_id: TCK-20260627-P0B-URBAN-RESOURCE-NODES
artifact_type: test_plan
tags: [p0, resource-nodes, urban-political, hotfix]
---

# Test Plan — TCK-20260627-P0B-URBAN-RESOURCE-NODES

## Scope

Verify that `urban_political` compiles with ≥3 resource nodes.

## Test Cases

### TC-01: CLI compilation has ≥3 resource nodes

**Command**: `make world-compile WORLD=urban_political`  
**Expected**: `resource_node_count >= 3` in compile report JSON  
**File verified**: `data/worlds/urban_political/world_compile_report.json`

### TC-02: Assembled urban_political has ≥3 resource nodes (integration)

**Test**: Add assertion to `test_smoke_urban_political_compiles_to_authoritative_state`  
**File**: `tests/integration/worldassembly/test_e2e_smoke.py`  
**Assertion**: `report["resource_node_count"] >= 3`

### TC-03: Resource nodes placed in valid regions

**Check**: All `ResourceNodeState` objects have `region_id` in  
{`hometown`, `bandit_road`, `trading_hometown`}  
Verified by WorldValidator "resource node region doesn't exist" rule (ERROR-level) — if
regions are invalid, assembly raises `InvalidWorldSpecError`.

### TC-04: Existing tests still pass

**Command**: `pytest tests/integration/worldassembly/ -m "not slow" -x`  
**Expected**: All tests GREEN

### TC-05: frontier_village_core module still assembles cleanly

**Test**: Existing `test_frontier_village_core_module_loads` or equivalent in
`tests/integration/worldassembly/test_real_content_world_compositions.py`  
**Expected**: No new ERROR-level validation issues from added resource_recipes

## Regression Guard

- `test_urban_political_composition` (test_real_content_world_compositions.py): asserts
  `len(spec.module_refs) == 3` on the content composition — this file is NOT changed,
  so assertion stays valid.
- `test_smoke_urban_political_compiles_to_authoritative_state`: add `resource_node_count >= 3`.

## Pytest Command

```
pytest tests/integration/worldassembly/ -k "urban_political or frontier" -m "not slow" -v
```
