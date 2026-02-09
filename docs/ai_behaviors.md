# AI Behaviors, Goals & Memory

Technical documentation for the entity AI system, including state machine, perception, memory, and goal derivation.

---

## Overview

Each entity runs a finite state machine (FSM) that determines its behavior each tick. The AI operates on **immutable snapshots** — no world state mutation occurs from worker threads. Decisions are returned as `ActionProposal` objects and applied by the main `WorldLoop` thread.

**Primary files**: `src/ai/states.py`, `src/ai/brain.py`, `src/ai/perception.py`

---

## AI State Machine

### States

| State | Value | Description |
|-------|-------|-------------|
| `IDLE` | 0 | Initial state, transitions immediately to WANDER |
| `WANDER` | 1 | Random movement, scanning for enemies and loot |
| `HUNT` | 2 | Moving toward a detected enemy target |
| `COMBAT` | 3 | Engaged in melee combat with adjacent enemy |
| `FLEE` | 4 | Retreating from combat when HP is low |
| `RETURN_TO_TOWN` | 5 | Hero navigating back to town (safe zone) |
| `RESTING_IN_TOWN` | 6 | Hero healing passively in town |
| `RETURN_TO_CAMP` | 7 | Enemy navigating back to nearest goblin camp |
| `GUARD_CAMP` | 8 | Enemy patrolling within camp radius, engaging intruders |
| `LOOTING` | 9 | Hero moving to and picking up ground loot |

### Transition Diagram

```
IDLE → WANDER
WANDER → HUNT | RETURN_TO_TOWN | LOOTING | RETURN_TO_CAMP
HUNT → COMBAT | FLEE | WANDER | RETURN_TO_CAMP
COMBAT → FLEE | RETURN_TO_TOWN | RETURN_TO_CAMP | HUNT | WANDER
         (may propose USE_ITEM instead of ATTACK)
FLEE → RETURN_TO_TOWN | RETURN_TO_CAMP | WANDER | HUNT
RETURN_TO_TOWN → RESTING_IN_TOWN
RESTING_IN_TOWN → WANDER
RETURN_TO_CAMP → GUARD_CAMP | WANDER
GUARD_CAMP → HUNT | COMBAT | GUARD_CAMP
LOOTING → WANDER | LOOTING
```

---

## Brain Dispatcher

`AIBrain.decide(entity, snapshot)` dispatches to the correct handler based on the entity's current `ai_state`:

```python
_HANDLERS = {
    AIState.IDLE: handle_idle,
    AIState.WANDER: handle_wander,
    AIState.HUNT: handle_hunt,
    AIState.COMBAT: handle_combat,
    AIState.FLEE: handle_flee,
    AIState.RETURN_TO_TOWN: handle_return_to_town,
    AIState.RESTING_IN_TOWN: handle_resting_in_town,
    AIState.RETURN_TO_CAMP: handle_return_to_camp,
    AIState.GUARD_CAMP: handle_guard_camp,
    AIState.LOOTING: handle_looting,
}
```

Each handler returns an `ActionProposal` (REST, MOVE, ATTACK, USE_ITEM, or LOOT) with an optional `new_ai_state` to transition.

---

## State Handlers

### `handle_idle`
Immediately transitions to `WANDER`.

### `handle_wander`
- Scans for enemies within vision range
- If enemy found → transition to `HUNT`
- If hero and ground loot nearby → transition to `LOOTING`
- If enemy on sanctuary tile → transition to `RETURN_TO_CAMP`
- Otherwise → random directional movement

### `handle_hunt`
- Moves toward the nearest enemy
- If adjacent to enemy → transition to `COMBAT`
- If HP drops below `flee_hp_threshold` → transition to `FLEE`
- **Enemies will NOT chase** into town or sanctuary tiles
- If target enters sanctuary → enemy transitions to `RETURN_TO_CAMP`

### `handle_combat`
- **Potion check**: If HP < 50% and entity has potions → propose `USE_ITEM` (large > medium > small)
- Otherwise → propose `ATTACK` on adjacent enemy
- If no adjacent enemy → transition to `HUNT` or `WANDER`
- If HP critical → transition to `FLEE`

### `handle_flee`
- Hero → moves toward `home_pos` (town), transitions to `RETURN_TO_TOWN`
- Enemy → moves toward nearest camp, transitions to `RETURN_TO_CAMP`
- If no camp → moves away from threats
- If HP recovers above threshold → transition to `HUNT`

### `handle_return_to_town`
- Hero moves toward `home_pos` step by step
- On arrival at town tile → transition to `RESTING_IN_TOWN`

### `handle_resting_in_town`
- Hero rests (REST action) while HP < max
- Passive healing: `hero_heal_per_tick` (default 3) HP per tick
- When fully healed → transition to `WANDER`

### `handle_return_to_camp`
- Enemy moves toward nearest camp center from snapshot
- On arrival at camp tile → transition to `GUARD_CAMP`
- If no camp found → transition to `WANDER`

### `handle_guard_camp`
- Enemy patrols within camp radius (random moves near camp center)
- Scans for intruders within `vision_range / 2` (tighter detection)
- If intruder detected → transition to `HUNT`

### `handle_looting`
- Hero moves toward nearest ground loot position
- When adjacent/on loot → propose `LOOT` action
- If no more loot nearby → transition to `WANDER`
- If enemy detected while looting → transition to `HUNT`

---

## Perception System

`src/ai/perception.py` provides static helper methods that operate on snapshots:

| Method | Description |
|--------|-------------|
| `visible_entities(entity, snapshot)` | All alive entities within `vision_range` |
| `nearest_enemy(entity, snapshot)` | Closest enemy by Manhattan distance |
| `direction_toward(from_pos, to_pos)` | Direction enum pointing toward target |
| `is_in_sanctuary(pos, grid)` | Check if position is on a SANCTUARY tile |
| `is_in_camp(pos, grid)` | Check if position is on a CAMP tile |
| `is_in_town(pos, grid)` | Check if position is on a TOWN tile |
| `ground_loot_nearby(entity, snapshot)` | Nearest ground loot position within vision |
| `nearest_camp(pos, camps)` | Nearest camp center from snapshot.camps |

---

## Entity Memory System

Each entity maintains two memory structures that persist across ticks:

### Terrain Memory

```python
terrain_memory: dict[tuple[int, int], int]
```

Maps `(x, y)` coordinates to `Material` enum values. Updated each tick in `WorldLoop._update_entity_memory()`:

- All tiles within `vision_range` (Manhattan distance) are recorded
- Memory is **cumulative** — tiles are never forgotten
- Represents the entity's **explored map knowledge**

### Entity Memory

```python
entity_memory: list[dict]
```

Each entry tracks a remembered entity sighting:

```python
{
    "id": int,        # Entity ID
    "x": int,         # Last known X position
    "y": int,         # Last known Y position
    "kind": str,      # Entity kind (e.g. "goblin_warrior")
    "hp": int,        # Last known HP
    "max_hp": int,    # Last known max HP
    "tick": int,      # Tick when last seen
    "visible": bool,  # Currently within vision range?
}
```

**Update rules** (per tick):
1. Entities within vision range are updated with current position/HP, `visible = True`
2. Entities outside vision range are marked `visible = False`
3. Entries for **defeated/removed entities** are pruned immediately (no ghost lingering)
4. Surviving entries older than **200 ticks** are pruned (forgotten)

### Frontend Visualization

When an entity is selected:
- **Visible tiles**: Shown at full brightness (no overlay)
- **Remembered tiles**: Shown dimmed (55% dark overlay)
- **Unknown tiles**: Shown as heavy fog (82% dark overlay)
- **Stale entity memories**: Shown as ghost markers with `?` labels

---

## Goal Derivation

Goals are computed each tick in `WorldLoop._update_entity_goals()` and stored in `entity.goals: list[str]`. They are purely **descriptive** — used for UI display, not for decision-making.

### Hero Goals

Derived from multiple factors:

| Condition | Goal Text |
|-----------|-----------|
| HP < 30% | "Survive — find safety and heal" |
| HP < 60% | "Find potions or return to town to heal" |
| Level < 5 | "Grow stronger — gain XP from enemies" |
| Level 5–9 | "Become powerful enough to raid goblin camps" |
| Level 10+ | "Dominate the battlefield" |
| Inventory > 80% full | "Inventory nearly full — prioritize upgrades" |
| Inventory < 30% full | "Collect more loot and equipment" |
| No weapon equipped | "Find a weapon" |
| No armor equipped | "Find armor" |
| Explored < 30% | "Explore unknown territory" |
| Explored 30–70% | "Continue mapping the world" |
| Explored > 70% | "Most of the world has been explored" |
| In COMBAT state | "Defeat the current enemy" |
| In LOOTING state | "Pick up nearby loot" |
| In RESTING_IN_TOWN | "Rest and recover in town" |

### Enemy Goals

| Condition | Goal Text |
|-----------|-----------|
| GUARD_CAMP state | "Guard the camp from intruders" + "Patrol the perimeter" |
| RETURN_TO_CAMP | "Return to the safety of camp" |
| HUNT state | "Hunt down a nearby target" |
| COMBAT state | "Fight to the death" |
| FLEE state | "Flee — too wounded to fight" |
| WANDER state | "Wander and search for prey" |
| HP < 30% | "Desperate — need to escape" |
| HP 30–60% | "Wounded — be cautious" |
| HP > 60% | "Feeling strong" |

---

## Thread Safety

- AI handlers run on **worker threads** and only read from immutable `Snapshot` objects
- All state mutations (memory updates, goal derivation, AI state transitions) happen on the **main WorldLoop thread**
- `ActionProposal.new_ai_state` carries state transitions from workers back to the main thread
- Memory and goals are updated in `_update_entity_memory()` and `_update_entity_goals()` after all actions are applied
