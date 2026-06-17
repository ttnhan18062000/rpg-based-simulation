---
status: active
layer: engine
authority: P1
audience: developer
---

# Minimal Kernel Verification Surface

Pins the minimal kernel execution laws and proves bit-identical determinism. Every test in this surface guards the tick-loop contract: correct phase sequencing, readiness gating, authoritative apply correctness, and reproducible hashing.

## 1. Tick Execution Path

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_tick_advancement` | Call `tick_once()` | `state.tick` increments by 1 | Broken tick loop or double-advancement |
| `test_phase_sequence` | Call `tick_once()` | Phases executed in enum order | Phase drifting or out-of-order execution |
| `test_world_time_passive` | Quiet tick (0 entities) | `world_time` increments | Passive systems depending on actions |

## 2. Readiness Gating

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_readiness_threshold` | Entity readiness 99 vs 100 | Action only collected for 100 | Illegal early action |
| `test_readiness_consumption` | Successful action | Readiness reset/decremented | Infinite action loops |

## 3. Authoritative Apply Path

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_generation_isolation` | `apply(state, upd)` | Prior state remains unchanged | Hidden mutation (frozen breach) |
| `test_deterministic_sort` | Unordered `entity_id` updates | Applied in ascending ID order | Intermittent non-determinism |
| `test_invalid_mutation` | Update outside contract | Rejection/error raised | Out-of-contract state contamination |

## 4. Determinism Proof

| Test Name | Input | Expected Rule | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_reproducibility` | Seed 123, Input X, 100 runs | 100 identical hashes | Flaky determinism (non-canonical keys) |
| `test_seed_divergence` | Seed 1 vs Seed 2 | Different hashes | Seed ignored/leaking global state |
| `test_quiet_tick_determinism` | 10 quiet ticks | Precise deterministic final state | Timing-based drift |

## Regression Intent

- **Mutation Leakage**: Catching any attempt to bypass the `apply()` function.
- **Serialization Drift**: Catching non-canonical hashing material.
- **Action/Time Coupling**: Catching instances where time stops if no entity is acting.
