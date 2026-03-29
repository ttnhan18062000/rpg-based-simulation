# Performance Report — Frontend Rendering Optimization

## Problem

With the 512×512 map (expanded from 192×192), the frontend became extremely laggy during dragging and zooming, especially in spectate mode (fog-of-war active). UI operations felt unresponsive.

### Root Causes

| Bottleneck | Impact | Frequency |
|-----------|--------|-----------|
| Minimap terrain: 262K `fillRect` calls | ~50ms per frame | Every poll (80ms) + every drag event |
| Fog overlay: 8192×8192 canvas (67M pixels) | GPU compositing lag during CSS transform | Every drag frame |
| Overlay redraw: 262K tile iterations | ~30ms per redraw | Every poll (object ref changed) |
| `Object.keys(terrain_memory).length` | O(10K) per render | Every render during drag (~60fps) |
| `selectedEntity` setState every poll | Triggers re-renders + canvas effects | Every 80ms (even same data) |
| Minimap `canvas.width` reset every frame | GPU reallocation | Every poll |

## Optimizations Applied

### 1. Minimap Terrain Caching (`GameCanvas.tsx`)

**Before:** 262K `fillRect` calls on every poll and drag event (terrain + fog-of-war in single effect).
**After:** Split into two effects:
- **Cache effect** — draws 262K terrain tiles to offscreen `<canvas>` (`mmTerrainCacheRef`). Only re-runs when `mmTerrainKey` changes (selection or `terrain_memory` size change).
- **Dynamic effect** — blits cached terrain via `drawImage()`, then draws ~300 entity dots + viewport rect.

**Result:** During drag, only 1 `drawImage` + ~300 entity dots instead of 262K `fillRect`.

### 2. Overlay Canvas Shrunk 256× (`useCanvas.ts` + `GameCanvas.tsx`)

**Before:** Overlay canvas was 8192×8192 (67M pixels). GPU had to composite this massive texture on every CSS transform during drag.
**After:** Overlay is 512×512 (1 pixel per tile), CSS-scaled via `transform: scale(CELL_SIZE × zoom)` with `imageRendering: pixelated`.

- Fog drawn at 1px/tile: `fillRect(x, y, 1, 1)` instead of `fillRect(x*16, y*16, 16, 16)`
- Vision border, weapon range ring, ghost markers moved to entity canvas (need sub-tile precision)

**Result:** GPU composites 262K pixels instead of 67M pixels during drag — **256× reduction**.

### 3. Overlay Position-Based Skip (`useCanvas.ts`)

**Before:** Overlay effect depended on `selectedEntity` (new object ref every poll) → 262K tile iterations every 80ms.
**After:** Memoized `overlayKey` string (`id_x_y_memSize_emSize`). Effect early-returns if key unchanged.

**Result:** Fog only redraws when entity actually moves or memory grows.

### 4. Memoized Overlay Key (`useCanvas.ts`)

**Before:** `Object.keys(selectedEnt.terrain_memory).length` computed on every render (O(10K) during drag at 60fps).
**After:** `overlayKey` wrapped in `useMemo` with `[selectedEnt, selectedEntityId]` deps.

**Result:** O(10K) computation only runs when `selectedEntity` state changes (once per tick), not on every drag frame.

### 5. Smart State Updates (`useSimulation.ts`)

**Before:** `setEntities()`, `setSelectedEntity()`, etc. called every poll (80ms), even when paused or data unchanged.
**After:**
- `selectedEntity` tracked via `lastSelKeyRef` (`responseEntityId_tick`) — skips setState when unchanged
- `entities` / `groundItems` only update when tick advances
- `selectedIdRef` synced immediately in callback (not via `useEffect` delay)

**Result:** Zero re-renders from simulation state when paused. During same tick, only status updates.

### 6. Minimap GPU Reallocation Fix (`GameCanvas.tsx`)

**Before:** `canvas.width = mmW; canvas.height = mmH;` set every frame — triggers GPU memory reallocation even when size unchanged.
**After:** Only set if dimensions actually changed; use `clearRect()` otherwise.

## Fog-of-War Visual Levels

Three distinct brightness levels when spectating:

| State | Overlay | Main Canvas | Minimap |
|-------|---------|-------------|---------|
| **In vision** | Clear | 100% brightness | `TILE_COLORS[tile]` |
| **Explored (fog)** | `rgba(0,0,0,0.5)` | ~50% brightness | `TILE_COLORS_DIM[tile]` |
| **Unseen** | `rgba(0,0,0,1.0)` | Fully black (hidden) | `#000000` |

## Performance Impact

### During Drag (spectate mode)

| Metric | Before | After |
|--------|--------|-------|
| Minimap terrain draws | 262K fillRects | 1 drawImage |
| Fog overlay GPU pixels | 67M (8192²) | 262K (512²) |
| Canvas effects per drag frame | 3 (grid+entity+overlay) | 1 (minimap dynamic only) |
| Overlay redraws per drag | Every frame | 0 (cached by overlayKey) |

### During Polling (running)

| Metric | Before | After |
|--------|--------|-------|
| State updates per poll | 5+ setState calls | 1-2 (tick-gated) |
| Overlay redraws per poll | Every poll | Only on entity move |
| Object.keys per render | O(10K) | 0 (memoized) |

### During Polling (paused)

| Metric | Before | After |
|--------|--------|-------|
| React re-renders per poll | Full component tree | 0 (all state skipped) |

## Files Changed

- `frontend/src/hooks/useCanvas.ts` — tile-res overlay (512×512), memoized overlayKey, entity canvas draws vision border/range/ghosts, removed TILE_COLORS_DIM import
- `frontend/src/components/GameCanvas.tsx` — minimap terrain cache (offscreen canvas + split effects), overlay CSS `scale(CELL_SIZE*zoom)` + pixelated, GPU realloc fix
- `frontend/src/hooks/useSimulation.ts` — tick-based state skip, selKey for selectedEntity, immediate ref sync
