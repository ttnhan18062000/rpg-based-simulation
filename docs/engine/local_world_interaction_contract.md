# Local Environment & World-Interaction Contract (Phase 8)

This document defines the authoritative semantics for environment and building interactions in the `src` engine.

## 1. Terrain & Spatial Constraints
### 1.1 Blocked Movement (WALL)
- Any tile marked as `WALL` in the `AuthoritativeState.terrain` map is impassable.
- Movement attempts into a `WALL` tile are rejected with `PATH_NOT_FOUND`.

### 1.2 Combat Obstruction (Line of Sight)
- `WALL` tiles and `Buildings` obstruct Line of Sight (LoS).
- Attacks through an obstructed tile are rejected with `LOS_OBSTRUCTED`.
- LoS is calculated via a Manhattan-step path check between attacker and target.

## 2. Building Interaction Semantics
### 2.1 Occupancy & Obstruction
- Functional buildings act as solid obstacles for movement and combat LoS.
- Rejection reason: `BUILDING_OBSTRUCTION`.

### 2.2 Building Services (REST)
- Entities located at a building tile of type `inn` or `home` can issue a `REST` intent.
- **REST Bonus**: 5x Passive Healing multiplier + 10.0 Readiness boost per tick.
- Sabotaged buildings (Functional: False) do not provide services.

## 3. Position-Sensitive Tactical Behavior
### 3.1 High Ground Bonus
- Attacker on a `HILL` terrain receives a damage bonus (+5).

### 3.2 Bracketing (Flanking)
- A target is **Bracketed** if it is adjacent to at least two hostiles on opposite sides (e.g., North and South, or East and West).
- Attackers receive a bracketing bonus (+3) when attacking a bracketed target.

## 4. Known Exclusions
- **Dynamic Terrain**: Terrain cannot currently be modified during a simulation (Except for buildings via sabotage).
- **Complex LoS**: Sophisticated raycasting is deferred; Manhattan-step is the current authoritative law.
- **Atmospheric Effects**: Fog/Night effects are currently out of scope for Phase 8.
