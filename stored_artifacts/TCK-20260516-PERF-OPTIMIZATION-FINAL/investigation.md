---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260516-PERF-OPTIMIZATION-FINAL
artifact_type: investigation
tags: [perf, optimization, final]
---

# Investigation: Performance Bottlenecks & Monkeypatch Regressions

## 1. Discovery & Empirical Observations
- Executed `pytest tests/unit`: Exactly 2 failures in `test_routine_biasing.py` (`KeyError: 'fatigue'`).
- Executed `pytest tests/perf`: Exactly 7 failures across combat, movement, resource, and strategic benchmarks due to p95 tick latencies exceeding 100.0ms (e.g. `assert 204.1 < 100.0`).

## 2. Root Cause Analysis
### A. Unit Test Monkeypatch Regression (`KeyError: 'fatigue'`)
- In `src/ai/goals/base.py`, `GoalRegistry.get_all_scores` caches `_sorted_keys` at the class level upon first invocation.
- When unit tests use `monkeypatch.setattr(GoalRegistry, "_scorers", mock_scorers)`, `cls._sorted_keys` is not cleared. Stale keys from production (like `'fatigue'`) remain in the list, causing `get_all_scores` to look up non-existent keys in the mock dictionary.

### B. Benchmark Latency Overhead
1. **Redundant Occupancy Map Rebuilds**:
   - In `src/engine/pipeline_phases/movement.py`, `route_movement_intent` ends with `object.__setattr__(state, "_occupancy_map_cache", None)`.
   - This explicitly invalidates the transient O(1) occupancy map, forcing all subsequent phases (combat, legality, occupancy conflict resolution) to reconstruct the 500-entity occupancy map dictionary from scratch multiple times per tick.
2. **Unbounded Dirty Set Entity Loops**:
   - In `src/core/dirty.py`, `DirtySetBuilder.mark_from_update` iterates over the entire `update.entity_updates` dictionary from scratch every time it is called.
   - In Phase 17 (`final_integrity`), `mark_from_update` is called multiple times, resulting in thousands of redundant entity property checks per tick.
3. **Dense Grid Distance Checks**:
   - In `src/engine/spatial.py`, `SpatialGrid.get_neighbor_tuples` checks all entity tuples in adjacent cells, computing `dx*dx + dy*dy <= r2`. On a dense 100x5 grid of 500 entities, this evaluates hundreds of multiplications per entity for ~167 entities per tick.
