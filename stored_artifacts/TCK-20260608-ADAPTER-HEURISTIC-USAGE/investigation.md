# Investigation — TCK-20260608-ADAPTER-HEURISTIC-USAGE

## Current Behavior

### modes.py (src/core/modes.py)
- `RuntimeContentMode` already has four values: CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK, TEST_MANUAL (done in RUNTIME-MODE-EXPLICIT)
- `AdapterHeuristicUsage` frozen dataclass already defined here with all six required fields: record_id, family, adapter, heuristic_type, reason, mode

### registries.py (src/core/registries.py)
- `AdapterProjectionResult` still uses `heuristic_count: int` (line 511) — must change to `heuristic_usages: tuple`
- `seed_phase1_content` aggregates counts: `heuristic_count=items_heuristic + services_heuristic + resources_heuristic` (line 579)
- Three adapter `adapt()` methods return `(dict, int)` — must change to `(dict, tuple[AdapterHeuristicUsage, ...])`

#### CatalogToItemRegistryAdapter.adapt() heuristics:
- line 220: use_kind heuristic (when item has no explicit use_kind)
- line 245: class_fit heuristic (when item has no explicit class_fit)

#### CatalogToServiceRegistryAdapter.adapt() heuristics:
- line 331: affordances heuristic (when service has no explicit affordances)

#### CatalogToResourceRegistryAdapter.adapt() heuristics:
- line 388: legacy_id heuristic
- line 407: source_region_tags heuristic
- required_tool: currently inferred in non-CATALOG_STRICT mode (lines 426-427) — no heuristic_count increment; ticket requires tracking
- base_difficulty: currently inferred in else branch (lines 433-438) — no heuristic_count increment; ticket requires tracking

#### ArchetypeToEnemyRegistryAdapter:
- No heuristic projection; uses hardcoded `rat` fallback (line 492-493) but not counted as heuristic in the int model

### Failing tests pre-existing (from incomplete RUNTIME-MODE-EXPLICIT work):
- test_registry_bridge.py::test_runtime_content_mode_enum_has_migration_and_v2 — references removed MIGRATION/V2
- test_registry_bridge.py::test_seed_with_migration_mode_returns_projection_result — uses MIGRATION mode
- test_registry_bridge.py::test_seed_with_v2_mode_raises_if_unresolved_entities_exist — uses V2 mode
- test_registry_bridge.py::test_adapter_projection_result_is_frozen_dataclass — uses heuristic_count=1 kwarg

## Mechanics/Engine Constraints
- No Mechanics Bible chapters directly relevant to adapter heuristics
- Engine contract: authoritative_pipeline.md — data must flow through typed records

## Parity Ledger Overlap
- infrastructure.yaml — runtime content seeding path; likely entries for catalog projection

## Prior Work
- TCK-20260608-RUNTIME-MODE-EXPLICIT (done): established 4-mode enum, CATALOG_STRICT rejection per-heuristic in item/service adapters, AdapterHeuristicUsage dataclass in modes.py

## Risks and Open Questions
- None: plan is unambiguous

## Anti-Drift Hazards
- `heuristic_count` property must be retained as a compatibility shim so existing tests pass with minimal change
