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

### F1: A* Pathfinding
- Implement `Pathfinder` class in `src/ai/pathfinding.py`
- A* algorithm with Manhattan distance heuristic
- Path computed from current position to target, cached for N ticks
- Path invalidated when: target moves, obstacle changes, entity gets attacked
- Fallback to greedy movement if A* fails (timeout or no path)
- **Extensibility:** `Pathfinder` is a pluggable strategy — swap algorithms without changing AI code

### F2: Terrain Cost Weights
- Different tile types have different movement costs:
  - FLOOR/TOWN/SANCTUARY: 1.0 (baseline)
  - ROAD/BRIDGE: 0.7 (faster — preferred)
  - FOREST: 1.3 (slightly slower)
  - SWAMP: 1.5 (slow, difficult terrain)
  - MOUNTAIN: 1.4 (rocky, slower)
  - DESERT: 1.2 (sand, slightly slower)
- A* uses tile cost in its heuristic — entities naturally prefer roads
- **Extensibility:** Tile costs defined in a `TERRAIN_MOVE_COST` registry, not in the pathfinder code

### F3: Hazard Avoidance
- Entities consider territory debuffs when routing
- Heroes avoid enemy territory when a safer path exists (cost penalty for hostile tiles)
- Enemies avoid sanctuary/town tiles unless specifically hunting
- Avoidance weight configurable (0.0 = ignore hazards, 1.0 = strongly avoid)
- **Extensibility:** Hazard costs layered on top of terrain costs via faction-aware cost function

### F4: Path Caching
- Computed paths stored in entity memory for reuse
- Cache key: `(start_pos, target_pos, tick)`
- Cache invalidation: target moved > 3 tiles, path blocked, N ticks elapsed
- Shared path cache per snapshot tick for entities moving to the same target
- **Extensibility:** Cache strategy is pluggable (LRU, tick-based, etc.)

### F5: Movement Formations
- Groups of allied entities moving together maintain formation spacing
- Formation types: Line, Wedge, Circle (defensive)
- Leader entity computes path; followers offset their target position
- Formation breaks when under attack (entities scatter to fight)
- **Extensibility:** Formation patterns defined as offset arrays, not hard-coded positions

### F6: Perpendicular Obstacle Avoidance
- When the direct path is blocked (wall, water), try perpendicular steps first
- Preference order: toward target → perpendicular (random left/right) → away from target
- Prevents entities from getting stuck at concave wall corners

### F7: Movement Speed Modifiers
- Road tiles grant +30% movement speed (already partially implemented)
- Swamp tiles apply -20% movement speed
- Rain weather applies -10% movement speed on open terrain
- SPD attribute and status effects affect movement delay
- **Extensibility:** Speed modifiers stack multiplicatively from: base SPD, terrain, weather, effects

### F8: Frontend Visualization
- When spectating, draw the entity's computed path as a dotted line on the overlay canvas
- Path color: green (safe), yellow (through neutral territory), red (through hostile territory)
- Path updates in real-time as the entity moves

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
