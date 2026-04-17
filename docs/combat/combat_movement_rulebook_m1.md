# Combat-Movement Rulebook — Milestone 1

## 1. Purpose
Define the exact spatial and temporal laws of the simulation. This document serves as the authoritative source for the `LegalityService` implementation and rule-contract tests.

## 2. Spatial Rules

### 2.1 Distance Metric
All distance calculations in the simulation (movement, range, AoE radius) use **Manhattan Distance**.
- Formula: `dist(a, b) = abs(a.x - b.x) + abs(a.y - b.y)`
- Diagonal tiles are treated as distance 2.

### 2.2 Adjacency
An entity is considered adjacent to a target if and only if the Manhattan distance is exactly **1**.
- This implies orthogonal adjacency (North, South, East, West).
- Diagonal adjacency is not supported in Milestone 1.

### 2.3 Occupancy and Pass-through
- **Hard Occupancy**: One entity occupies exactly one tile.
- **Mutual Exclusion**: A tile occupied by one entity is impassable for all others.
- **No Pass-through**: There is no ally or enemy pass-through in Milestone 1.

### 2.4 AoE targeting (Milestone 1)
- **Impact Tile**: AoE skills target a `LocationTarget`.
- **Center Legality**: The impact tile must be within the defined attack range from the attacker.
- **Line of Sight**: Clear LOS must exist between the attacker and the impact tile.
- **Splash Radius**: Affected entities are those within the Manhattan radius of the impact tile.

## 3. Timing Rules

### 3.1 World-Time Continuity
The world clock (`tick`) is continuous and uniform.
- Every tick progresses world-time regardless of entity activity.
- Passive systems (status effects, needs decay, environmental updates) process every tick.

### 3.2 Action Readiness
Entities act based on a readiness model.
- An entity may only propose an action when the current `tick >= entity.next_act_at`.
- Taking an action resets `next_act_at` based on the entity's speed stat.

## 4. Enforcement
Rules are enforced at two levels:
1. **Selection**: AI and UI use `LegalityService` to filter choices.
2. **Authority**: The `ActionSystem` re-validates all proposals using `LegalityService` immediately before execution. Illegal proposals are rejected.
