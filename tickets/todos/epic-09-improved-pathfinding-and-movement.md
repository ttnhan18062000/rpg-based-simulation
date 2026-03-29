# Epic 09: Improved Pathfinding & Movement

## Summary

Replace the current greedy step-by-step movement with a proper pathfinding system that supports A* navigation, path caching, movement formations, and terrain-aware routing. Entities navigate intelligently around obstacles, prefer roads, and avoid hazards.

Inspired by: Warcraft III unit pathing, Rimworld pawn movement, StarCraft pathfinding, D&D movement rules.

---

## Motivation

- Current movement is greedy (move toward target one step at a time) — entities get stuck on walls and water
- No path caching means entities recalculate direction every tick
- No road preference — roads exist but entities don't prefer them
- No hazard avoidance — entities walk through enemy territory without considering alternatives
- Aligns with "realistic RPG simulation" — intelligent entities should navigate smartly

---

## Features

### F1: A* Pathfinding ✅ DONE
- `Pathfinder` class in `src/ai/pathfinding.py`
- A* algorithm with Manhattan distance heuristic, performance-bounded (`max_nodes=200`)
- `find_path(start, goal, occupied)` → `list[Vector2] | None`
- `next_step(start, goal, occupied)` → `Vector2 | None`
- Goal tile excluded from occupied check (entity moving toward it)
- Fallback to `_greedy_move_toward()` if A* fails or distance ≤ 2
- **Integration:** `propose_move_toward()` in `src/ai/states.py` uses A* for dist > 2
- **Files:** `src/ai/pathfinding.py` (new), `src/ai/states.py`

### F2: Terrain Cost Weights ✅ DONE
- `TERRAIN_MOVE_COST` registry in `src/ai/pathfinding.py`:
  - FLOOR/TOWN/SANCTUARY/RUINS/DUNGEON_ENTRANCE: 1.0
  - ROAD/BRIDGE: 0.7 (preferred)
  - DESERT: 1.2
  - FOREST: 1.3
  - MOUNTAIN: 1.4
  - SWAMP: 1.5
- `tile_cost(grid, pos)` helper used by A* step cost calculation
- A* naturally routes through roads and avoids expensive terrain

### F3: Hazard Avoidance ⏸️ DEFERRED
- Faction-aware cost penalties for hostile territory

### F4: Path Caching ✅ DONE
- `cached_path: list | None` and `cached_path_target: object | None` on Entity model
- Cache hit: target unchanged and entity at expected position → reuse path
- Cache miss: recompute A* and store new path
- **Files:** `src/core/models.py`, `src/ai/states.py`

### F5: Movement Formations ⏸️ DEFERRED
- Line, Wedge, Circle formations for allied groups

### F6: Perpendicular Obstacle Avoidance ✅ DONE (pre-existing)
- Already implemented in `_greedy_move_toward()` (perpendicular fallback)
- A* now handles complex obstacle navigation natively

### F7: Movement Speed Modifiers ⏸️ DEFERRED
- Road +30% already exists in `MoveAction.apply()`; swamp/weather penalties pending

### F8: Frontend Visualization ⏸️ DEFERRED
- Path overlay on canvas (dotted line showing A* route)

### F9: Intra-Region Terrain Detail ✅ DONE (new, not in original spec)
- `TerrainDetailGenerator` class in `src/systems/terrain_detail.py`
- Per-biome features after Voronoi assignment:
  - **Forest:** Clearings (FLOOR), dense groves (WALL), streams (WATER + BRIDGE), forest paths (ROAD)
  - **Desert:** Rocky ridges (WALL), oases (WATER), hard-packed ground (FLOOR), caravan routes (ROAD)
  - **Swamp:** Stagnant pools (WATER), dead tree thickets (WALL), mudflats (FLOOR), bog paths (ROAD/BRIDGE)
  - **Mountain:** Cliff faces (WALL), valleys (FLOOR), lava vents (LAVA, difficulty≥3 only), mountain passes (ROAD)
- Scatter-based cluster placement (deterministic via RNG)
- River generation with winding paths and bridge crossings
- Road networks connecting locations within each region (MST-like)
- Difficulty-gated features (lava only in high-difficulty mountains)
- **Files:** `src/systems/terrain_detail.py` (new), `src/api/engine_manager.py`

### F10: Tile Hover Tooltip ✅ DONE (new, not in original spec)
- Hover any tile to see **all** information on that tile in a multi-line tooltip
- **Terrain type** shown with coordinates (e.g. "🗺 Forest (42, 67)")
- **All entities** on the tile (kind, level, HP, stamina, state) — not just the first
- **Ghost markers** for remembered entities in fog
- **Buildings** on the tile
- **Ground loot** piles on the tile
- **Resource nodes** on the tile (name, remaining harvests, yields)
- Added `TILE_NAMES` map in `frontend/src/constants/colors.ts`
- **Files:** `frontend/src/hooks/useCanvas.ts`, `frontend/src/components/GameCanvas.tsx`, `frontend/src/constants/colors.ts`

---

## Design Principles

- Pathfinding runs in worker threads (reads snapshot, produces move proposal) — no world mutation
- Path computation is deterministic (same snapshot = same path)
- Terrain costs are data-driven — adding new terrain = add cost entry
- Pathfinder is optional — entities fall back to greedy movement if A* is too expensive
- Performance: A* limited to max 200 nodes explored per call; fallback on timeout

---

## Dependencies

- Grid system with walkability checks (already exists)
- Terrain types (already exists)
- Territory system (already exists)
- Movement action processing in WorldLoop (already exists)

---

## Estimated Scope

- Backend: ~5 files new/modified (new pathfinding.py, modified states.py, brain.py)
- Frontend: ~2 files modified (useCanvas path overlay)
- Data: Terrain cost registry, formation offset definitions
