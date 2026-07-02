# Test Plan — TCK-20260627-P2N-DEGRADED-FALLBACK

## Regression Surface (existing tests that must still pass)

| Test file | What it guards |
|---|---|
| `tests/unit/core/test_catalog_fallback.py::test_optional_fallback_mode` | `runtime_content_source == "legacy_hardcoded"` after LEGACY_FALLBACK with no catalog — value unchanged, only default changes |
| `tests/unit/core/test_catalog_fallback.py::test_strict_required_mode_missing` | raises ValueError in required=True mode |
| `tests/unit/runtime/test_fallback_restrict_modes.py` (all) | FallbackRestrictedError guards for CATALOG_STRICT / CATALOG_WITH_COMPATIBILITY |
| `tests/integration/perf/test_phase10_graceful_degradation.py` | Existing GracefulDegradationManager pressure/phase-skip behavior |

## New Tests Required (per AC)

### File: `tests/unit/core/test_degraded_fallback.py`

**Test 1 — module-level default is not `"legacy_hardcoded"`**
```python
def test_runtime_content_source_module_default_is_not_legacy_hardcoded():
    """The literal module-level default must not be the legacy_hardcoded string.
    Check the annotation/default in the module __annotations__ or by importing
    after a reload with no catalog available on the path.
    Uses importlib to re-inspect the source default, not the post-seeding value.
    """
```
Strategy: grep/AST check the source file for the declaration line, or import a fresh
isolated module (monkeypatching `os.path.exists` to False so seed_phase1_content
runs but produces catalog=None and confirm the module's declared default is `None`).

**Test 2 — `GracefulDegradationManager.resolve_content_source` uses catalog in degraded mode**
```python
def test_resolve_content_source_degraded_uses_catalog():
    manager = GracefulDegradationManager()
    manager.update_pressure(0.96, 1.0)  # → DEGRADED
    catalog = MagicMock()
    catalog.get_lowest_cost_for_type.return_value = {"item_a": object()}
    result = manager.resolve_content_source(catalog, "items")
    catalog.get_lowest_cost_for_type.assert_called_once_with("items")
    assert "item_a" in result
```

**Test 3 — `resolve_content_source` strict mode raises on missing catalog**
```python
def test_resolve_content_source_strict_raises_on_missing_catalog():
    manager = GracefulDegradationManager()
    with pytest.raises(CatalogMissError):
        manager.resolve_content_source(None, "items", strict=True)
```

**Test 4 — `resolve_content_source` non-strict mode returns empty on missing catalog**
```python
def test_resolve_content_source_non_strict_returns_empty_on_missing_catalog():
    manager = GracefulDegradationManager()
    result = manager.resolve_content_source(None, "items", strict=False)
    assert result == {}
```

**Test 5 — `CatalogRepository.get_lowest_cost_for_type` returns sorted dict**
```python
def test_get_lowest_cost_items_sorted_by_base_value():
    """Items should be returned cheapest-first by base_value."""
    # Build a minimal in-memory CatalogRepository with a few ItemDefinition entries
    # and assert the returned order is ascending by base_value.
```

## Scoped Pytest Commands

```bash
# New tests only
pytest tests/unit/core/test_degraded_fallback.py -v

# Regression surface
pytest tests/unit/core/test_catalog_fallback.py tests/unit/runtime/test_fallback_restrict_modes.py -v

# Full scoped suite
pytest tests/unit/core/test_degraded_fallback.py tests/unit/core/test_catalog_fallback.py tests/unit/runtime/test_fallback_restrict_modes.py tests/integration/perf/test_phase10_graceful_degradation.py -v
```

## Anti-Drift Test Guards

- Do not change the VALUE `"legacy_hardcoded"` that `seed_phase1_content` sets in LEGACY_FALLBACK
  with no catalog — only the module-level declared default changes. If the regression tests for
  existing fallback behavior break, the default-change has been applied incorrectly.
- The integration degradation test (`test_phase10_graceful_degradation.py`) must remain green —
  `update_pressure()`, `get_provider_cap()`, and `should_skip_phase()` behavior is unchanged.
