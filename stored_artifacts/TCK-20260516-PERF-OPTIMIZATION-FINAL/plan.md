# Implementation Plan: TCK-20260516-PERF-OPTIMIZATION-FINAL

## 1. Goal
Eliminate p95 tick latency bottlenecks to pass all performance benchmarks under 100.0ms limit and resolve monkeypatch regressions in `GoalRegistry`.

## 2. Proposed Changes
### A. `src/ai/goals/base.py`
- Modify `GoalRegistry.get_all_scores` to validate `cls._sorted_keys` against `cls._scorers`:
```python
        if cls._sorted_keys is None or len(cls._sorted_keys) != len(cls._scorers) or any(k not in cls._scorers for k in cls._sorted_keys):
            cls._sorted_keys = sorted(cls._scorers.keys())
```

### B. `src/engine/pipeline_phases/movement.py`
- Modify `route_movement_intent` line 280 to cache `live_occ_map` rather than clearing it:
```python
            object.__setattr__(state, "_occupancy_map_cache", live_occ_map)
```

### C. `src/core/dirty.py`
- In `DirtySetBuilder.__init__`, initialize `self._processed_upd_ids = set()`.
- In `mark_from_update`, skip already processed `EntityUpdate` object IDs:
```python
        for e_id, e_upd in update.entity_updates.items():
            upd_id = id(e_upd)
            if upd_id in self._processed_upd_ids:
                continue
            self._processed_upd_ids.add(upd_id)
```

### D. `src/engine/spatial.py`
- In `SpatialGrid.get_neighbor_tuples`, add fast bounding coordinate checks before multiplication:
```python
                            dx = ent.navigation.position[0] - px
                            if -radius <= dx <= radius:
                                dy = ent.navigation.position[1] - py
                                if -radius <= dy <= radius:
                                    if dx*dx + dy*dy <= r2:
                                        results.append((eid, ent))
```

## 3. Verification
- Run `pytest tests/unit/strategic/test_routine_biasing.py` to confirm the unit test fix.
- Run `pytest tests/unit` to ensure 100% pass rate.
- Run `pytest tests/perf` to ensure all 47 perf tests pass with latency under 100.0ms.
