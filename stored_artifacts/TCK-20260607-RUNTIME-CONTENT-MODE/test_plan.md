---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260607-RUNTIME-CONTENT-MODE
artifact_type: test_plan
tags: [runtime, content, mode]
---

# Test Plan — TCK-20260607-RUNTIME-CONTENT-MODE

## Test Command

```
pytest tests/unit/core/ tests/integration/content/ -q
```

Do NOT run `tests/unit/worldassembly/test_resolver.py` — the ticket's stated test file is
incorrect. `seed_phase1_content` is in `src/core/registries.py`, not `src/worldassembly/resolver.py`.
The correct test files are under `tests/unit/core/`.

## New Tests to Add

Target file: `tests/unit/core/test_registry_bridge.py` (existing file with seed_phase1_content tests)
OR a new file `tests/unit/core/test_runtime_content_mode.py` if it keeps things cleaner.

### 1. test_runtime_content_mode_enum_has_migration_and_v2
```python
def test_runtime_content_mode_enum_has_migration_and_v2():
    from src.core.modes import RuntimeContentMode
    assert RuntimeContentMode.MIGRATION.value == "migration"
    assert RuntimeContentMode.V2.value == "v2"
    assert len(RuntimeContentMode) == 2
```

### 2. test_seed_with_migration_mode_returns_projection_result
```python
def test_seed_with_migration_mode_returns_projection_result(mock_catalog_repo):
    from src.core.registries import seed_phase1_content
    from src.core.modes import RuntimeContentMode
    from src.core.registries import AdapterProjectionResult
    result = seed_phase1_content(mock_catalog_repo, mode=RuntimeContentMode.MIGRATION)
    assert isinstance(result, AdapterProjectionResult)
    assert result.total_entities >= 0
    assert result.native_resolved + result.legacy_projected + result.unresolved == result.total_entities
    assert isinstance(result.heuristic_details, dict)
```

### 3. test_seed_with_v2_mode_raises_if_unresolved_entities_exist
```python
def test_seed_with_v2_mode_raises_if_unresolved_entities_exist(mock_incomplete_catalog_repo):
    """In V2 mode, adapter raises AdapterError when a field is missing."""
    from src.core.registries import seed_phase1_content, AdapterError
    from src.core.modes import RuntimeContentMode
    with pytest.raises(AdapterError):
        seed_phase1_content(mock_incomplete_catalog_repo, mode=RuntimeContentMode.V2)
```

### 4. test_seed_legacy_fallback_returns_none
```python
def test_seed_legacy_fallback_returns_none():
    """Legacy hardcoded path (catalog_repo=None) returns None — no projection result."""
    from src.core.registries import seed_phase1_content
    result = seed_phase1_content(None)
    assert result is None
```

### 5. test_adapter_projection_result_is_frozen_dataclass
```python
def test_adapter_projection_result_is_frozen_dataclass():
    from src.core.registries import AdapterProjectionResult
    r = AdapterProjectionResult(total_entities=5, native_resolved=3,
                                legacy_projected=2, unresolved=0, heuristic_details={})
    assert r.total_entities == 5
    with pytest.raises((AttributeError, TypeError)):
        r.total_entities = 99  # frozen
```

## Existing Tests to Update

### tests/integration/content/test_registry_projection_parity.py:19
Change: `seed_phase1_content(repo, migration_mode=True)`
To:     `seed_phase1_content(repo, mode=RuntimeContentMode.MIGRATION)`
Add import: `from src.core.modes import RuntimeContentMode`

### tests/unit/core/test_registry_adapters.py:227-264
Change: `CatalogToItemRegistryAdapter(repo, migration_mode=False)`
To:     `CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.V2)`
(and similarly for ResourceAdapter, ServiceAdapter)
Add import: `from src.core.modes import RuntimeContentMode`

## Regression Coverage (existing tests must still pass)

- `tests/unit/core/test_registry_bridge.py` — all existing tests
- `tests/unit/core/test_catalog_smoke_simulation.py`
- `tests/unit/core/test_hardcoded_regression_guard.py`
- `tests/unit/core/test_registry_parity.py`
- `tests/unit/core/test_registry_cross_reference.py`
- `tests/unit/core/test_catalog_fallback.py`
- `tests/unit/core/test_registry_adapters.py`
- `tests/integration/content/test_registry_projection_parity.py`

## Test Classification

| Test | Type | Priority |
|---|---|---|
| enum values | unit | P1 |
| migration mode returns result | unit | P0 |
| v2 mode raises on incomplete data | unit | P0 |
| legacy fallback returns None | unit | P1 |
| frozen dataclass mutation guard | unit | P1 |
| existing adapter tests with enum | regression | P0 |
