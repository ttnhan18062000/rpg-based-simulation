---
status: active
layer: engine
authority: P1
audience: developer
---

# Runtime State Verification Surface

Tests that pin the runtime state boundedness laws and model category separation. Guards collection bounds, eviction determinism, and the isolation of hot-path authoritative structures from export/diagnostic paths.

## 1. Model Separation

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_hotpath_purity` | `AuthoritativeState` | Zero dependency on `export.py` / `diagnostic.py` | Non-authoritative payload leakage |
| `test_export_factory` | Call `to_export(state)` | Valid DTO, source state unchanged | Mutation during serialization |

## 2. Bounded Collections

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_list_eviction_oldest` | Add 11 to `List[10]` | Index 0 is dropped | Off-by-one in circular buffer |
| `test_registry_reject` | Add 11 to `Registry[10]` | Raises `OverflowError` | Silent registry growth |

## 3. Determinism in Overflow

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_eviction_determinism` | Same seed, N evictions | Identical final state (and hash) | Nondeterministic eviction order |
| `test_compaction_stability` | Metric window summarization | Identical summary hash | Floating-point drift in summaries |

## 4. Structural Resource Stability

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_sustained_memory_flat` | 100,000 additions to `BoundedList[100]` | RAM flat (no heap growth for list) | Hidden reference leakage in eviction |

## Regression Intent

- **Iteration Order**: Ensure eviction logic does not depend on dict insertion order or set iteration.
- **Reference Leakage**: Ensure that evicted items are eligible for GC (no hidden references in the buffer).
