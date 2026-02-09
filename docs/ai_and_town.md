# AI State Machine & Town System

This document covers the overhauled AI state machine, town safe-zone mechanics, hero respawn system, and the richer entity behaviors introduced in this update.

## Overview of Changes

1. **Fixed AI state machine** — entities no longer get stuck in HUNT/COMBAT after their target dies
2. **Added Town safe zone** — a rectangular area on the grid that goblins cannot enter
3. **Hero respawn** — hero respawns at town after death instead of being permanently removed
4. **Hero retreat-to-town** — hero flees toward town when wounded, rests there to heal
5. **Richer AI behaviors** — dead-target memory cleanup, perpendicular pathfinding, threat assessment, wound-aware wandering
6. **Two new AI states** — `RETURN_TO_TOWN` and `RESTING_IN_TOWN`

---

## Town System

### Grid Representation

A new `Material.TOWN` (value `3`) tile type has been added. Town tiles form a rectangular area on the grid, configured by:

| Config Parameter | Default | Description |
|------------------|---------|-------------|
| `town_center_x` | 3 | X coordinate of town center |
| `town_center_y` | 3 | Y coordinate of town center |
| `town_radius` | 2 | Radius of town area (produces a 5×5 square) |

Town tiles are placed during world construction in both `EngineManager._build()` (server mode) and `_run_cli()` (CLI mode):

```python
for ty in range(center_y - radius, center_y + radius + 1):
    for tx in range(center_x - radius, center_x + radius + 1):
        grid.set(Vector2(tx, ty), Material.TOWN)
```

### Walkability Rules

| Tile | Hero | Goblin |
|------|------|--------|
| FLOOR | ✅ walkable | ✅ walkable |
| WALL | ❌ blocked | ❌ blocked |
| WATER | ❌ blocked | ❌ blocked |
| TOWN | ✅ walkable | ❌ blocked (safe zone) |

This is enforced at four levels:
- **`Grid.is_walkable(pos)`** — returns `True` for FLOOR and TOWN (physical walkability)
- **`Grid.is_town(pos)`** — returns `True` only for TOWN tiles
- **`MoveAction.validate()`** — rejects moves by non-hero entities onto TOWN tiles
- **`CombatAction.validate()`** — rejects attacks against entities standing on TOWN tiles
- **AI state helpers** — `_is_tile_passable(actor, pos, snapshot)` combines both checks

This means heroes inside town are **fully protected**: goblins cannot enter, and attacks against entities on TOWN tiles are rejected even from adjacent non-town tiles.

### Spawn Protection

- **Hero** always spawns at town center (`town_center_x`, `town_center_y`)
- **Goblins** are prevented from spawning on TOWN tiles via BFS fallback (`_find_nearest_walkable_non_town`)
- **Generator** uses the same BFS to avoid placing periodic goblin spawns on town tiles

---

## Hero Respawn

### Configuration

| Config Parameter | Default | Description |
|------------------|---------|-------------|
| `hero_respawn_ticks` | 10 | Cooldown ticks before hero can act again after death |
| `hero_heal_per_tick` | 3 | HP restored per tick while resting in town (applied by WorldLoop) |

### Town Healing

Healing is applied by `WorldLoop._heal_town_heroes()` on the main simulation thread (not in the AI brain handler) to ensure thread safety. Each tick, heroes in `RESTING_IN_TOWN` state standing on a TOWN tile receive `hero_heal_per_tick` HP, capped at `max_hp`. Once fully healed, the brain transitions the hero back to `WANDER`.

### Respawn Flow

When a hero's HP drops to 0:

```
Hero dies (hp <= 0)
  │
  ▼ (in WorldLoop._phase_cleanup)
  ├─ HP restored to max_hp
  ├─ Position teleported to home_pos (town center)
  ├─ AI state set to RESTING_IN_TOWN
  ├─ next_act_at set to current_tick + hero_respawn_ticks
  ├─ Memory cleared
  └─ Spatial index updated
```

Unlike goblins (which are permanently removed on death), the hero entity is **never removed** from the world. It is instantly healed and teleported home with a cooldown delay.

### Entity Model Addition

A new `home_pos: Vector2 | None` field was added to the `Entity` dataclass. For heroes, this is set to the town center on spawn. For goblins, it remains `None`.

---

## AI State Machine (Revised)

### State Diagram

```
                        ┌───────────────────────────┐
                   ┌───►│          IDLE              │
                   │    └────────────┬──────────────┘
                   │                 │ always
                   │    ┌────────────▼──────────────┐
                   │    │         WANDER             │
                   │    │  • random movement         │
                   │    │  • scan for enemies        │
                   │    │  • hero: check wounds      │
                   │    └──┬────────┬───────────┬───┘
                   │       │        │           │
                   │  enemy visible  │      hero wounded
                   │       │        │      (HP < 70%)
                   │       ▼        │           │
                   │  ┌─────────┐   │    ┌──────▼───────┐
                   │  │  HUNT   │   │    │RETURN_TO_TOWN│◄──── hero flee
                   │  │ pursue  │   │    │ navigate home│      from any state
                   │  └──┬──┬───┘   │    └──────┬───────┘
                   │     │  │       │           │
                   │ adjacent lost  │      arrived at town
                   │     │  target  │           │
                   │     ▼  │       │    ┌──────▼───────┐
                   │  ┌─────┴───┐   │    │RESTING_IN    │
                   │  │ COMBAT  │   │    │   TOWN       │
                   │  │ attack  │   │    │ heal per tick │
                   │  └──┬──┬───┘   │    └──────┬───────┘
                   │     │  │       │           │
                   │ low HP  enemy  │      fully healed
                   │     │  dead    │           │
                   │     ▼  │       │           │
                   │  ┌─────┴───┐   │           │
                   │  │  FLEE   │   │           │
                   │  │ (goblin)│   │           │
                   │  └────┬────┘   │           │
                   │       │        │           │
                   └───────┴────────┴───────────┘
                      (safe / recovered / healed)
```

### State Transitions

| From | Condition | To | Actor |
|------|-----------|-----|-------|
| IDLE | always | WANDER | all |
| WANDER | enemy visible, HP OK | HUNT | all |
| WANDER | enemy visible, low HP | RETURN_TO_TOWN | hero |
| WANDER | enemy visible, low HP | FLEE | goblin |
| WANDER | wounded (HP < 70%) | RETURN_TO_TOWN | hero |
| HUNT | adjacent to enemy | COMBAT | all |
| HUNT | lost target + no memory | WANDER | all |
| HUNT | low HP | RETURN_TO_TOWN | hero |
| HUNT | low HP | FLEE | goblin |
| COMBAT | enemy dead / vanished | WANDER | all |
| COMBAT | enemy retreated | HUNT | all |
| COMBAT | low HP | RETURN_TO_TOWN | hero |
| COMBAT | low HP | FLEE | goblin |
| FLEE | no threats visible | WANDER | goblin |
| FLEE | HP recovered (> 1.5× threshold) | HUNT | goblin |
| FLEE | always (hero) | RETURN_TO_TOWN | hero |
| FLEE | arrived at town | RESTING_IN_TOWN | hero |
| RETURN_TO_TOWN | arrived at town tile | RESTING_IN_TOWN | hero |
| RETURN_TO_TOWN | not yet at town | RETURN_TO_TOWN | hero |
| RESTING_IN_TOWN | HP < max | RESTING_IN_TOWN | hero |
| RESTING_IN_TOWN | fully healed | WANDER | hero |

### Key Fix: Dead-Target Transitions

**Before:** When a goblin killed the hero (or any target), it could remain stuck in HUNT or COMBAT state indefinitely because:
- Memory still referenced the dead entity
- `nearest_enemy()` returned `None` but memory kept the hunt going

**After:** Every state handler now calls `_clear_dead_from_memory()` at the start, which removes dead or despawned entity IDs from the actor's memory dict. Combined with the existing `enemy is None → WANDER` transitions in HUNT and COMBAT, entities now correctly return to wandering when their target dies.

```python
def _clear_dead_from_memory(actor, snapshot):
    dead_ids = [eid for eid in actor.memory
                if eid not in snapshot.entities or not snapshot.entities[eid].alive]
    for eid in dead_ids:
        del actor.memory[eid]
```

---

## Richer AI Behaviors

### Perpendicular Pathfinding

When the direct path toward a target is blocked, entities now try perpendicular directions before falling back to REST:

```python
# In _propose_move_toward:
# 1. Try direct path
# 2. If blocked, try perpendicular axes
# 3. If all blocked, REST
```

Similarly, `_propose_move_away` tries perpendicular escape routes when the primary flee direction is blocked.

### Threat Assessment Before Engagement

In WANDER state, entities now check their HP before engaging a spotted enemy:
- If HP is below flee threshold, hero retreats to town; goblin flees
- Only engages if HP is sufficient

### Wound-Aware Wandering (Hero)

The hero checks its HP ratio while wandering. If below 70% (even if above the critical flee threshold of 30%), it proactively returns to town to heal rather than continuing to explore at reduced HP.

### Memory Position Verification

In HUNT state, when following a memory position:
- If the entity reaches the remembered location (Manhattan distance ≤ 1) but the target is not there, it clears that memory entry and transitions to WANDER
- Prevents indefinite circling around stale memory positions

---

## Frontend Updates

### New Tile Color

| Tile | Color | Hex |
|------|-------|-----|
| TOWN | Dark teal | `#2d4a3e` |

### New State Colors

| State | Color | Hex |
|-------|-------|-----|
| RETURN_TO_TOWN | Light blue | `#60a5fa` |
| RESTING_IN_TOWN | Cyan | `#22d3ee` |

### Legend Update

The sidebar legend now includes a "Town" entry with the teal color swatch.

---

## Files Modified

| File | Changes |
|------|---------|
| `src/core/enums.py` | Added `RETURN_TO_TOWN`, `RESTING_IN_TOWN` to `AIState`; `TOWN` to `Material` |
| `src/config.py` | Added `town_center_x/y`, `town_radius`, `hero_respawn_ticks`, `hero_heal_per_tick` |
| `src/core/models.py` | Added `home_pos: Vector2 \| None` to `Entity` |
| `src/core/grid.py` | Updated `is_walkable` to include TOWN; added `is_town()` |
| `src/ai/perception.py` | Added `is_in_town()`, `count_nearby_allies()` |
| `src/ai/states.py` | Full rewrite: 8 state handlers, helper functions, dead-target fix, town-aware pathfinding |
| `src/actions/base.py` | Added `new_ai_state` field to `ActionProposal` for proper state propagation |
| `src/engine/worker_pool.py` | Attaches brain-decided `new_ai_state` to proposals |
| `src/ai/brain.py` | Registered `handle_return_to_town`, `handle_resting_in_town` |
| `src/actions/combat.py` | Added town safe-zone: reject attacks on entities in TOWN tiles |
| `src/actions/move.py` | Added TOWN tile movement restriction for non-hero entities |
| `src/systems/generator.py` | Added `_find_nearest_walkable_non_town` for goblin spawns |
| `src/engine/world_loop.py` | Hero respawn in `_phase_cleanup`, town healing in `_heal_town_heroes` |
| `src/api/engine_manager.py` | Town tile placement, hero spawn at town center |
| `src/__main__.py` | Mirror town placement in CLI mode |
| `frontend/index.html` | TOWN tile color, new state colors, legend update |
