---
status: archive
authority: P2
audience: historical
layer: testing
original_date: 2026-04-24
---

# Test Taxonomy and Marker Enforcement Design

## 1. Goal
To ensure every test in the V2 parity suite has a clear verification purpose and follows strict proof standards. This prevents "shallow testing" and ensures that divergences are explicitly captured rather than accidentally implemented.

## 2. Taxonomy Definitions

| Marker | Proof Standard |
| :--- | :--- |
| `legacy_characterization` | Must run against legacy `src` or use frozen legacy state to define "as-is" behavior. |
| `v2_contract` | Defines the expected behavior of a V2 component where legacy parity is not the primary goal. |
| `differential` | Must compare outputs from both `src` and `src` for identical inputs (Seeds/Configs). |
| `intentional_divergence` | Must assert that V2 behavior differs from legacy in a specific, documented way. Requires a `divergence_id`. |
| `regression` | Must reproduce a known bug or drift item before the fix is applied. |
| `certification` | Must pass for a release/milestone to be considered stable. |

## 3. Enforcement Logic

### 3.1 Marker Registration
Markers are registered in `pyproject.toml` to avoid `PytestUnknownMarkWarning`.

### 3.2 Collection Hook
The `tests/conftest.py` will implement `pytest_collection_modifyitems`:

```python
def pytest_collection_modifyitems(config, items):
    taxonomy_markers = {
        "legacy_characterization", "v2_contract", "differential",
        "intentional_divergence", "regression", "certification"
    }
    
    for item in items:
        # Only enforce for the parity subdirectory
        if "tests/parity" in str(item.fspath):
            item_markers = {m.name for m in item.iter_markers()}
            if not (item_markers & taxonomy_markers):
                pytest.fail(f"Test {item.nodeid} is missing a taxonomy marker.")
```

### 3.3 Divergence Metadata
Tests marked as `intentional_divergence` MUST include a `divergence_id` parameter:
```python
@pytest.mark.intentional_divergence(id="COMB-001")
def test_divergent_behavior():
    ...
```

## 4. Documentation
A new doc `docs/testing/v2_test_taxonomy.md` will be created to guide the team on how to choose and implement these markers.
