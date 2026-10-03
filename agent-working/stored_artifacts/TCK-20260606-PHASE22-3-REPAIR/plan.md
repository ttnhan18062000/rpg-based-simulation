---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE22-3-REPAIR
artifact_type: plan
tags: [phase22, repair]
---

# Staging Plan - TCK-20260606-PHASE22-3-REPAIR

## 1. Goal
Modify the normalization and resolution logic of RPG world modules so that counts/quantities of resources, buildings, and services are correctly preserved instead of being lost during list conversions.

## 2. Proposed Changes
- **`src/worldmodules/schema.py`**:
  - Update `services` type hint in `WorldModuleSpec` to `Union[Dict[str, int], List[Any]]` (same pattern as resources/buildings).
- **`src/worldmodules/normalizer.py`**:
  - Implement `normalize_count_map(value: Any, field_name: str) -> dict[str, int]` helper.
  - Implement checks in `normalize_count_map`:
    - Only positive integers (> 0) allowed as counts.
    - Zero or negative counts fail.
    - Keys must be strings.
    - Reject duplicate values in list shorthands.
  - Change `NormalizedWorldModule` fields:
    - `resources`: dict[str, int]
    - `buildings`: dict[str, int]
    - `services`: dict[str, int]
    - Change other lists (`biomes`, `ecologies`, `populations`, `relationships`) to `tuple[str, ...]` if appropriate or list.
- **`src/worldassembly/schema.py`**:
  - Update `ResolvedModuleContribution`:
    - `resource_refs`: Dict[str, int]
    - `building_refs`: Dict[str, int]
    - `service_refs`: Dict[str, int]
- **`src/worldassembly/resolver.py`**:
  - Update `resolve_module_contribution` to return the new dict structures.
  - Update `assemble` where it processes resource nodes/buildings/services to use the counts from these dictionaries correctly.
