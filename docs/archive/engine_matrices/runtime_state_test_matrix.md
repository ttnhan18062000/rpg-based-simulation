---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 3 Test Matrix — Retention & Separation

## 1. Purpose
This matrix defines the tests required to pin the Milestone 3 boundedness laws and model categories.

## 2. Test Groups

### Group A: Model Separation
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_hotpath_purity` | `AuthoritativeState` | Zero dependency on `export.py` / `diagnostic.py` | Non-authoritative payload leakage |
| `test_export_factory` | Call `to_export(state)`| Valid DTO, source state unchanged | Mutation during serialization |

### Group B: Bounded Collections
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_list_eviction_oldest`| Add 11 to List[10] | Index 0 is dropped | Off-by-one in circular buffer |
| `test_registry_reject` | Add 11 to Registry[10]| Raises `OverflowError` | Silent registry growth |

### Group C: Determinism in Overflow
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_eviction_determinism`| Same seed, N evictions | Identical final state (and hash) | Nondeterministic eviction order |
| `test_compaction_stability`| Metric window summarization | Identical summary hash | Floating point drift in summaries |

### Group D: Structural Resource Stability
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_sustained_memory_flat`| 100,000 additions to BoundedList[100] | RAM flat (no heap growth for list) | Hidden reference leakage in eviction |

## 3. Determinism Regression Intent
- **Iteration Order**: Ensure eviction logic does not depend on dict insertion order or set iteration.
- **Reference Leakage**: Ensure that evicted items are definitely eligible for GC (no hidden references in the buffer).
