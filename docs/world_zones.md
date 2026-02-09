# World Zones & Tile Types

Technical documentation for the world map structure, zone placement, and tile behavior.

---

## Overview

The simulation world is a 2D grid of tiles. Each tile has a `Material` type that determines walkability, zone effects, and visual appearance. Zones are placed during world initialization in `EngineManager._build()` and `__main__._run_cli()`.

**Primary files**: `src/core/grid.py`, `src/core/enums.py`, `src/api/engine_manager.py`

---

## Tile Materials

```python
class Material(IntEnum):
    FLOOR     = 0  # Default open terrain
    WALL      = 1  # Impassable barrier
    WATER     = 2  # Impassable (currently)
    TOWN      = 3  # Safe zone for heroes
    CAMP      = 4  # Enemy stronghold
    SANCTUARY = 5  # Debuff zone surrounding town
```

### Walkability

| Material | Walkable | Hero Can Enter | Enemy Can Enter |
|----------|----------|----------------|-----------------|
| FLOOR | Yes | Yes | Yes |
| WALL | No | No | No |
| WATER | No | No | No |
| TOWN | Yes | Yes | Yes (but triggers retreat AI) |
| CAMP | Yes | **No** (blocked) | Yes |
| SANCTUARY | Yes | Yes | Yes (but debuffed) |

The hero is explicitly blocked from entering CAMP tiles in `MoveAction.validate()`. Enemies can enter town/sanctuary but their AI triggers retreat behavior.

### Grid Helpers

```python
grid.is_walkable(pos)   # FLOOR, TOWN, CAMP, SANCTUARY
grid.is_town(pos)       # TOWN only
grid.is_camp(pos)       # CAMP only
grid.is_sanctuary(pos)  # SANCTUARY only
```

---

## Zone: Town

The safe zone where the hero spawns, rests, and heals.

### Placement
```python
town_center = Vector2(config.town_center_x, config.town_center_y)
# Fill square from (cx - radius) to (cx + radius) with Material.TOWN
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `town_center_x` | 3 | Town center X coordinate |
| `town_center_y` | 3 | Town center Y coordinate |
| `town_radius` | 2 | Half-width of the town square |

This creates a **5×5 town** (radius 2 in each direction) centered at (3, 3).

### Behavior
- **Hero healing**: Heroes in `RESTING_IN_TOWN` state heal `hero_heal_per_tick` (default 3) HP per tick
- **Hero respawn**: Dead heroes teleport to `town_center` and enter `RESTING_IN_TOWN`
- **Enemy AI**: Enemies will not chase the hero into town tiles; they transition to `RETURN_TO_CAMP` or `WANDER`

---

## Zone: Sanctuary

A debuff ring surrounding the town that weakens enemies and causes them to retreat.

### Placement
```python
# Fill ring between town_radius and sanctuary_radius with Material.SANCTUARY
for sy in range(cy - sanctuary_radius, cy + sanctuary_radius + 1):
    for sx in range(cx - sanctuary_radius, cx + sanctuary_radius + 1):
        pos = Vector2(sx, sy)
        if grid.in_bounds(pos) and grid.get(pos) == Material.FLOOR:
            grid.set(pos, Material.SANCTUARY)
```

Only `FLOOR` tiles are converted — town tiles are preserved.

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sanctuary_radius` | 5 | Half-width of the sanctuary square |
| `sanctuary_debuff_atk` | 0.5 | ATK multiplier for non-hero entities |
| `sanctuary_debuff_def` | 0.5 | DEF multiplier for non-hero entities |

This creates an **11×11 sanctuary area** (radius 5) with the **5×5 town** in the center.

### Behavior
- **Combat debuff**: Non-hero entities on sanctuary tiles have ATK and DEF halved during combat
- **Enemy retreat**: Enemies on sanctuary tiles transition to `RETURN_TO_CAMP`
- **Chase prevention**: Enemies pursuing the hero will not follow into sanctuary tiles
- **Hero benefit**: Heroes fight at full strength on sanctuary tiles

### Visual Layout (approximate)
```
. . S S S S S S S S S . .
. S S S S S S S S S S S .
S S S S S S S S S S S S S
S S S S T T T T T S S S S
S S S S T T T T T S S S S
S S S S T T * T T S S S S  (* = town center)
S S S S T T T T T S S S S
S S S S T T T T T S S S S
S S S S S S S S S S S S S
. S S S S S S S S S S S .
. . S S S S S S S S S . .

. = FLOOR, S = SANCTUARY, T = TOWN, * = center
```

---

## Zone: Goblin Camps

Enemy strongholds placed far from town, defended by elite guards.

### Placement Algorithm
```python
for camp_idx in range(num_camps):
    for attempt in range(50):  # Up to 50 placement attempts per camp
        1. Generate random position using deterministic RNG
        2. Check manhattan(camp_pos, town_center) >= camp_min_distance_from_town
        3. Check no other camp within camp_radius * 4 distance
        4. Check grid bounds
        5. Fill square area with Material.CAMP
        6. Record camp position in world.camps
        7. Break on success
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_camps` | 3 | Number of goblin camps to place |
| `camp_radius` | 2 | Half-width of each camp square |
| `camp_min_distance_from_town` | 12 | Minimum Manhattan distance from town center |
| `camp_max_guards` | 4 | Maximum warrior guards per camp |

Each camp is a **5×5 area** of CAMP tiles.

### Camp Spawns

Each camp receives:
- **1 Goblin Chief** (ELITE tier, `GUARD_CAMP` state)
- **Up to 3 Goblin Warriors** (WARRIOR tier, `GUARD_CAMP` state)

Guards spawn near the camp center and patrol within the camp radius.

### Behavior
- **Hero blocked**: The hero cannot walk onto CAMP tiles (must fight guards outside)
- **Guard AI**: Camp guards in `GUARD_CAMP` state patrol within `camp_radius` and engage intruders within `vision_range / 2`
- **Enemy return**: Fleeing enemies with a camp navigate back to their nearest camp
- **Camp positions** are stored in `WorldState.camps` and included in `Snapshot.camps` for AI perception

---

## Zone Interaction Matrix

| Zone | Hero Movement | Enemy Movement | Hero Combat | Enemy Combat |
|------|---------------|----------------|-------------|--------------|
| FLOOR | Normal | Normal | Normal | Normal |
| TOWN | Normal | Enters but retreats | Normal | Normal |
| SANCTUARY | Normal | Enters but debuffed | Normal | ATK/DEF × 0.5 |
| CAMP | **Blocked** | Normal | N/A | Normal |
| WALL | Blocked | Blocked | N/A | N/A |
| WATER | Blocked | Blocked | N/A | N/A |

---

## World Initialization Order

1. Create empty grid (all FLOOR)
2. Place TOWN tiles (5×5 at town center)
3. Place SANCTUARY tiles (11×11 ring, preserving TOWN)
4. Place CAMP tiles (3 camps, 5×5 each, far from town)
5. Spawn hero at town center with inventory
6. Spawn tiered goblins on FLOOR tiles (not town/sanctuary)
7. Spawn camp guards at each camp position

This order ensures zones don't overlap incorrectly (SANCTUARY only replaces FLOOR, not TOWN).
