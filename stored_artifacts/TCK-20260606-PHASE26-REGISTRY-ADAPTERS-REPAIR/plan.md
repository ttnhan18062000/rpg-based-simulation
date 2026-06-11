---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE26-REGISTRY-ADAPTERS-REPAIR
artifact_type: plan
tags: [phase26, registry, adapters, repair]
---

# Phase 26 Implementation Plan

## Goal Description
Make registry projection explicit and testable, not hidden inside heuristic/fallback code.

## Proposed Changes

### Content Schema (`src/content/schema.py`)
- Add fields to `ItemDefinition`:
  - `use_kind: Optional[str] = Field(None, description="Explicit runtime usage kind")`
  - `class_fit: List[str] = Field(default_factory=list, description="Explicit class fit tags")`
  - `equipment_slot: Optional[str] = Field(None, description="Explicit equipment slot")`
- Add fields to `ResourceDefinition`:
  - `runtime_kind: Optional[str] = Field(None, description="Explicit runtime resource type")`
  - `legacy_id: Optional[str] = Field(None, description="Explicit legacy ID mapping")`
  - `required_tool: Optional[str] = Field(None, description="Explicit required tool")`
- Add fields to `ServiceProfileDefinition`:
  - `affordances: List[str] = Field(default_factory=list, description="Explicit service affordances")`

### Registry Adapters (`src/core/registries.py`)
- Update `CatalogToItemRegistryAdapter.adapt()`:
  - Check `item.use_kind` first. If present, use it. If not, use the fallback heuristic logic based on categories.
  - Check `item.class_fit` first. If present, convert to tuple and use it. If not, use the fallback heuristic logic.
  - Set `equipment_slot` if needed (if `ItemDef` class accepts it - wait, does `ItemDef` have `equipment_slot`? Let's check `ItemDef` definition in `src/core/registries.py`. It has `id`, `tags`, `rarity`, `base_value`, `use_kind`, `class_fit`. No `equipment_slot` field. We can keep it or add it if needed, but let's check `ItemDef` class).
- Update `CatalogToResourceRegistryAdapter.adapt()`:
  - Check `res.legacy_id` first. If present, use it. If not, use legacy ID mapping heuristic.
  - Check `res.required_tool` first. If present, use it. If not, check metadata, then heuristic.
- Update `CatalogToServiceRegistryAdapter.adapt()`:
  - In catalog mode, do not inject prepopulated Hometown services (`shop_hometown`, `blacksmith_hometown`, etc.). Only return adapted definitions from the repository.
  - Check `s_prof.affordances` (from `affordances` or `metadata.get("affordances")`) first. If present, use it. If not, use the category/name heuristics.
- Update `ArchetypeToEnemyRegistryAdapter.adapt()`:
  - Do not seed fallback `rat` enemy record if adapting in catalog mode. Only adapt the projections defined in the catalog (`legacy_enemy_projections`).

## Verification Plan

### Automated Tests
- Implement new unit/integration tests to verify explicit fields are preferred, heuristics are fallback, and catalog mode doesn't inject hardcoded fallbacks like `rat` or hometown services.
- Run tests in `tests/integration/content/test_registry_projection_parity.py`.
