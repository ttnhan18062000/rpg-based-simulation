# Milestone 4 — Spatial Index Consistency

## Objective

Avoid full-world scans for proximity queries.

---

## Current problem

Any logic that does this is dangerous:

```python
for entity in state.entities.values():
    distance(...)
```

This becomes expensive at large entity counts.

---

## Target design

Use spatial index for:

```text
nearby entities
nearby resource nodes
nearby buildings
nearby corpses/items
region lookup
occupancy lookup
```

---

## Technical tasks

### 4.1 Audit full scans

Search:

```bash
grep -R "for .* in state.entities.values" -n src
grep -R "for .* in state.resource_nodes.values" -n src
grep -R "for .* in state.buildings.values" -n src
```

Classify each scan:

```text
acceptable small global scan
should use spatial index
should use dirty set
should run by cadence
```

---

### 4.2 Add shared spatial query service

Create or centralize:

```text
src/engine/spatial_query.py
```

API:

```python
class SpatialQueryService:
    def entities_near(state, position, radius) -> list[int]: ...
    def resource_nodes_near(state, position, radius) -> list[int]: ...
    def buildings_near(state, position, radius) -> list[int]: ...
    def occupied_tiles(state) -> dict[tuple[float, float], int]: ...
```

Internally use:

```text
SpatialHashV2
SpatialGrid
cached per tick
```

---

### 4.3 Cache spatial index per state/tick

Avoid rebuilding repeatedly.

Simple cache key:

```text
state.tick
state.movement_count
entity_count
```

Better:

```text
state.spatial_version
```

If not available, start with per-tick cache.

---

### 4.4 Replace high-cost scans

Prioritize:

```text
movement/occupancy
tactical target selection
resource searching
goal scorers
group coordination
town/service lookup
```

---

### 4.5 Tests

Tests:

```text
spatial query returns same result as brute-force
spatial query deterministic ordering
spatial index invalidates after movement_count changes
spatial query excludes inactive/dead entities where needed
```

Performance tests:

```text
1000 entity nearby query must be faster than brute-force baseline
```

---

## Exit criteria

Large movement/combat/resource scenarios improve.

You should see lower phase cost for:

```text
movement
tactical
resource
strategic goal scoring
```

---
