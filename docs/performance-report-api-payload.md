# Performance Report — API Payload Optimization

## Problem

The frontend polls `GET /api/v1/state` every ~80ms. Pre-optimization, this endpoint returned **~1.6 MB per request**, causing visible lag and excessive bandwidth usage.

### Root Cause Breakdown (pre-optimization `/state` payload)

| Component | Size | % of Total | Issue |
|-----------|------|-----------|-------|
| `terrain_memory` (all entities) | ~761 KB | 47% | Every tile ever seen by every entity, sent every poll |
| `entity_memory` (all entities) | ~90 KB | 6% | Last-seen entity data for every entity |
| Full entity schemas (all fields) | ~200 KB | 12% | Skills, quests, attributes, equipment for every entity |
| Buildings / regions / resources | ~50 KB | 3% | Static data re-sent every poll |
| `/map` grid (2D array) | ~876 KB | one-time | Uncompressed 512×512 tile grid |

## Optimizations Applied

### 1. Slim Entity Schema (`EntitySlimSchema`)

**Before:** Full `EntitySchema` (~5 KB each) for all ~300 entities = ~1.5 MB
**After:** `EntitySlimSchema` (~200 B each) for all entities + full `EntitySchema` only for selected entity

Slim schema fields (14 total): `id`, `kind`, `x`, `y`, `hp`, `max_hp`, `state`, `level`, `tier`, `faction`, `weapon_range`, `combat_target_id`, `loot_progress`, `loot_duration`

Full schema sent only when `?selected=<id>` is passed — includes `terrain_memory`, `entity_memory`, `skills`, `quests`, `attributes`, `inventory_items`, etc.

### 2. Static Data Endpoint (`/static`)

**Before:** Buildings, resource nodes, treasure chests, and regions included in every `/state` poll
**After:** New `GET /api/v1/static` endpoint fetched once on mount

Contents: ~20 buildings, ~117 resource nodes, ~26 treasure chests, ~25 regions ≈ **47 KB** (one-time)

### 3. RLE-Compressed Map Grid

**Before:** `/map` returns `grid: number[][]` (2D array) = ~876 KB
**After:** `/map` returns `grid: number[]` (RLE flat array: `[value, count, ...]`) = ~270 KB

Frontend decodes via `decodeRLE()` in `useSimulation.ts`. Compression ratio: **~69% smaller**.

### 4. Frontend Data Flow Restructured

- `useSimulation` fetches `/map` + `/static` once on mount (parallel)
- `useSimulation` passes `?selected=<id>` to `/state` using a ref (no re-render on selection change)
- `useCanvas` accepts `EntitySlim[]` + `Entity | null` — uses slim for rendering, full for fog-of-war
- `GameCanvas`, `Sidebar`, `InspectPanel`, `EntityList` all updated for new types

## Results

### Measured Payload Sizes (10 ticks, ~360 entities)

| Endpoint | Frequency | Before | After | Reduction |
|----------|-----------|--------|-------|-----------|
| `/state` (no selection) | Every 80ms | ~800 KB | ~75 KB | **~91%** |
| `/state` (with selection) | Every 80ms | ~800 KB | ~78 KB | **~90%** |
| `/map` | Once | ~876 KB | ~270 KB | **~69%** |
| `/static` | Once | N/A (in /state) | ~47 KB | **100% removed from poll** |

### Bandwidth Impact

| Metric | Before | After |
|--------|--------|-------|
| Per-poll payload | ~800 KB – 1.6 MB | ~75 KB |
| Bandwidth at 80ms poll | ~10–20 MB/s | ~0.9 MB/s |
| One-time load | ~876 KB | ~317 KB (map + static) |

### Test Coverage

- **575 existing tests pass** (0 failures)
- **8 new payload tests** in `tests/test_api_payload.py`:
  - RLE encoding correctness and decode round-trip
  - Slim schema field validation (must have / must not have)
  - Per-entity JSON size < 300 B
  - Full `/state` response < 100 KB (no selection)
  - `WorldStateResponse` has no static fields
  - `StaticDataResponse` has all static fields
- **TypeScript compiles clean** (0 errors)

## Files Changed

### Backend
- `src/api/schemas.py` — `EntitySlimSchema`, `StaticDataResponse`, `MapResponse` (RLE grid), `WorldStateResponse` (slimmed)
- `src/api/routes/state.py` — `/state` (slim + selected), `/static` endpoint
- `src/api/routes/map.py` — RLE encoding

### Frontend
- `frontend/src/types/api.ts` — `EntitySlim`, `StaticData`, `MapData` (RLE)
- `frontend/src/hooks/useSimulation.ts` — `decodeRLE()`, `DecodedMapData`, fetch `/static` once, `selectedIdRef`
- `frontend/src/hooks/useCanvas.ts` — `EntitySlim[]` + `Entity | null` params
- `frontend/src/components/GameCanvas.tsx` — `selectedEntity` prop, minimap uses full entity
- `frontend/src/components/Sidebar.tsx` — `EntitySlim[]` + `selectedEntity` prop
- `frontend/src/components/InspectPanel.tsx` — `DecodedMapData` type
- `frontend/src/components/EntityList.tsx` — `EntitySlim` type
- `frontend/src/App.tsx` — pass `selectedEntity`

### Tests & Scripts
- `tests/test_api_payload.py` — 8 payload optimization tests
- `scripts/profile_api_payload.py` — API payload size profiler

## How to Profile

```bash
python scripts/profile_api_payload.py                # Default: 10 ticks, seed 42
python scripts/profile_api_payload.py --ticks 50     # More ticks = more memory accumulated
python scripts/profile_simulation.py --ticks 500     # Engine tick profiling (unchanged)
```
