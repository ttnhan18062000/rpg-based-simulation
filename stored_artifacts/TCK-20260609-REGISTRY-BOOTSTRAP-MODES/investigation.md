---
ticket: TCK-20260609-REGISTRY-BOOTSTRAP-MODES
phase: investigation
---

# Investigation

## Existing state

`src/core/registries.py::seed_phase1_content()` handles both catalog and hardcoded fallback paths but:
- Falls back to hardcoded silently whenever catalog_repo=None (no mode-based guard)
- Strict mode only raises on heuristic usages, not on the fallback itself
- No `ContentSourceReport` — only returns `AdapterProjectionResult` (catalog path) or None (fallback)
- No TEST_MANUAL branch — callers must pass catalog_repo=None manually

`RuntimeContentMode` enum in `src/core/modes.py` has 4 values:
  CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK, TEST_MANUAL

No `src/runtime/` package exists yet.

## Key adapter behaviors (verified)

- `ArchetypeToEnemyRegistryAdapter`: reads `repo.legacy_enemy_projections`, calls `get_entity_archetype()` (None-safe)
- `CatalogToRegionRegistryAdapter`: always injects hometown if not present
- `CatalogToServiceRegistryAdapter(catalog_mode=True)`: skips hardcoded prepopulation block
- All catalog adapters tolerate empty collections (return empty dicts)
