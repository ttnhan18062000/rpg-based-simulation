# Performance Audit Report — Epic 16

## Baseline (pre-optimization)

- **Map**: 192×192, 8 Voronoi regions, 156 entities at peak
- **Avg tick**: 49.8ms (20.0 ticks/sec)
- **P95**: 72.0ms, **Max**: 257.7ms
- **Function calls**: 159M over 500 ticks

## Hotspots Identified (cProfile, 500 ticks)

| Rank | Function | tottime | calls | Root Cause |
|------|----------|---------|-------|------------|
| 1 | `_update_entity_memory` | 19.0s | 500 | O(n × vr²) Vector2 alloc + O(n²) entity scan + linear memory search |
| 2 | `find_frontier_target` | 7.2s | 8,704 | Iterates ALL explored tiles (grows with map) |
| 3 | `manhattan` | 7.2s | 15M | Method call overhead at extreme volume |
| 4 | `visible_entities` | 4.2s | 70k | O(n) full entity scan per call |
| 5 | Worker pool threading | 22s | 43k futures | ThreadPoolExecutor overhead with 1 worker |
| 6 | `_tick_engagement` | 2.0s | 500 | O(n²) entity scan for adjacency |
| 7 | `Snapshot.from_world` | 2.7s | 501 | Unnecessary grid.copy() every tick |
| 8 | `alive` property | 3.2s | 12.7M | Property chain overhead |
| 9 | `enum.__get__` | 1.8s | 5.4M | Enum descriptor access in terrain scan |

## Optimizations Applied

### 1. `_update_entity_memory` — terrain scan (world_loop.py)
- **Before**: `Vector2(tx, ty)` allocated per tile → `grid.in_bounds()` → `grid.get()` → `.value`
- **After**: Direct `grid._tiles[row_base + tx].value` — no Vector2, no method calls
- Also: moved `from ... import Vector2` out of the loop
- **Impact**: 19.0s → 5.0s tottime

### 2. `_update_entity_memory` — entity scan (world_loop.py)
- **Before**: O(n²) — every entity scans every other entity, linear search through entity_memory list
- **After**: `spatial_hash.query_radius()` for nearby entities, `dict[id → entry]` for O(1) memory lookup
- **Impact**: Eliminated ~10s of O(n²) scanning

### 3. `find_frontier_target` (perception.py)
- **Before**: Iterates ALL explored tiles to find frontier (grows unbounded with map exploration)
- **After**: Bounded neighborhood scan (max 40-tile radius around actor), early exit at 32 candidates
- **Impact**: 7.2s → 4.9s (and won't degrade as entities explore more)

### 4. `visible_entities` (perception.py)
- **Before**: O(n) scan of all entities per call (70k calls)
- **After**: Snapshot spatial index (`_spatial` dict, cell_size=16) → only check nearby cells
- **Impact**: 4.2s → 0.7s tottime (**83% reduction**)

### 5. Worker pool inline mode (worker_pool.py)
- **Before**: `ThreadPoolExecutor.submit()` + `as_completed()` even with 1 worker = 22s threading overhead
- **After**: Inline execution when `num_workers <= 1` — no futures, no thread sync
- **Impact**: Eliminated 22s of cProfile overhead; real-world: ~3ms/tick saved

### 6. `_tick_engagement` (world_loop.py)
- **Before**: O(n²) — every entity scans all others for adjacency
- **After**: `spatial_hash.query_radius(pos, 1)` — only check immediate neighbors
- **Impact**: 2.0s → 0.3s

### 7. Snapshot creation (snapshot.py)
- **Before**: `grid.copy()` copies 36,864 tiles every tick (grid never changes during ticks)
- **After**: Share grid reference directly
- Also: Build lightweight spatial index during `from_world` for `visible_entities`
- **Impact**: Saved ~0.5s over 500 ticks

### 8. Grid raw-coordinate access (grid.py)
- Added `get_xy(x, y)` and `in_bounds_xy(x, y)` methods that skip Vector2 allocation

## Post-Optimization Results

- **Avg tick**: 28.4ms (34.9 ticks/sec) — **43% faster**
- **P50**: 27.0ms — **41% faster**
- **P95**: 40.1ms — **44% faster**
- **Max**: 59.8ms — **77% faster** (spikes nearly eliminated)
- **StdDev**: 6.1ms — **64% less variance**
- **Function calls**: 47M — **70% fewer**

## Memory Profile (500 ticks)

- **Current**: 374.7 KB
- **Peak**: 14.1 MB
- **Status**: Healthy, no unbounded growth detected
- Top allocations: profiler timing arrays, terrain_memory dicts, snapshot copies

## Remaining Hotspots (not worth optimizing without changing architecture)

| Function | tottime | Notes |
|----------|---------|-------|
| `_update_entity_memory` | 5.0s | Inherent cost of updating vision for ~80 entities |
| `find_frontier_target` | 3.9s | Bounded scan, scales with vision_range not map size |
| `Entity.copy` | 1.5s | Deep copy needed for thread safety |
| `enum.__get__` | 1.8s | Python enum overhead, would need C extension |
| `alive` property | 1.3s | Property chain, 3.4M calls — marginal |

## Files Changed

- `src/engine/world_loop.py` — `_update_entity_memory`, `_tick_engagement`
- `src/ai/perception.py` — `visible_entities`, `find_frontier_target`
- `src/engine/worker_pool.py` — inline dispatch for single-worker
- `src/core/snapshot.py` — skip grid copy, add spatial index
- `src/core/grid.py` — raw-coordinate accessors
