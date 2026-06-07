# Investigation — TCK-20260608-RUNTIME-MODE-EXPLICIT

## Current State

- `src/core/modes.py` has only `MIGRATION = "migration"` and `V2 = "v2"`.
- `src/core/registries.py` uses these in four adapter constructors and in `seed_phase1_content`.
  - Default param is `RuntimeContentMode.MIGRATION` throughout.
  - V2 branch raises `AdapterError` immediately on heuristic use.
  - MIGRATION branch silently counts heuristics.
- `tests/integration/content/test_registry_projection_parity.py` seeds with `RuntimeContentMode.MIGRATION`.
- No `tests/unit/content/test_runtime_content_mode.py` file exists yet.

## Mapping

| Old value | New value |
|---|---|
| `V2` | `CATALOG_STRICT` |
| `MIGRATION` | `CATALOG_WITH_COMPATIBILITY` |

New values added: `LEGACY_FALLBACK`, `TEST_MANUAL`.

## Call Sites

- `CatalogToItemRegistryAdapter.__init__` default param
- `CatalogToServiceRegistryAdapter.__init__` default param
- `CatalogToResourceRegistryAdapter.__init__` default param
- All `if self.mode == RuntimeContentMode.V2` branches → `CATALOG_STRICT`
- `seed_phase1_content` default param and bottom call
- `test_registry_projection_parity.py` fixture call
