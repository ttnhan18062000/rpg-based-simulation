---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 2 Test Matrix — Determinism & Execution

## 1. Purpose
This matrix defines the tests required to pin the Milestone 2 minimal kernel execution and prove bit-identical determinism.

## 2. Test Groups

### Group A: Tick Execution Path
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_tick_advancement` | Call `tick_once()` | `state.tick` increments by 1 | Broken tick loop or double-advancement |
| `test_phase_sequence` | Call `tick_once()` | Phases executed in Enum order | Phase drifting or out-of-order execution |
| `test_world_time_passive` | Quiet tick (0 entities) | `world_time` increments | Passive systems depending on actions |

### Group B: Readiness Gating
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_readiness_threshold` | Entity readiness 99 vs 100| Action only collected for 100 | Illegal early action |
| `test_readiness_consumption`| Successful Action | Readiness reset/decremented | Infinite action loops |

### Group C: Authoritative Apply Path
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_generation_isolation`| `apply(state, upd)` | Prior state remains unchanged | Hidden mutation (frozen breach) |
| `test_deterministic_sort` | Unordered `entity_id` updates | Applied in ascending ID order | Intermittent non-determinism |
| `test_invalid_mutation` | Update outside contract | Rejection/Error | Out-of-contract state contamination |

### Group D: Determinism Proof
| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_reproducibility` | Seed 123, Input X, 100 runs | 100 identical hashes | Flaky determinism (non-canonical keys) |
| `test_seed_divergence` | Seed 1 vs Seed 2 | Different hashes | Seed ignored/leaking global state |
| `test_quiet_tick_determinism`| 10 quiet ticks | Precise deterministic final state | Timing-based drift |

## 3. Regression Intent
- **Mutation Leakage**: Catching any attempt to bypass the `apply()` function.
- **Serialization Drift**: Catching non-canonical hashing material.
- **Action/Time Coupling**: Catching instances where time stops if no one is acting.
