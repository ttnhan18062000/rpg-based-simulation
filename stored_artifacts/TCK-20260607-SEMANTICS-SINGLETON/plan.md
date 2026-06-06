# Plan — TCK-20260607-SEMANTICS-SINGLETON

## Changes

1. `src/content_semantics/faction.py`
   - Add a doc comment above `_semantics_service_cache` explaining the singleton contract.
   - In `get_faction_semantics_service()`, replace `"data/content"` with `ContentPathConfig().content_root` (lazy import to avoid circular imports).
   - Add `configure_faction_semantics_service(repo: CatalogRepository) -> None`.
   - Add `reset_faction_semantics_service() -> None`.

2. `tests/integration/combat/test_relation_combat_integration.py`
   - Import `reset_faction_semantics_service`.
   - Add `@pytest.fixture(autouse=True) def reset_semantics_cache()` that yields then calls reset.

## No changes needed

- `legality.py`, `tactical.py` — call sites unchanged.
- `FactionSemanticsService` class — unchanged.
