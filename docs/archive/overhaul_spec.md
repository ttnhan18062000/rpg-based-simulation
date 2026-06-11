---
status: archive
authority: P2
audience: historical
layer: misc
original_date: unknown
---

# Combat and Movement Overhaul: Authoritative Specification

This document serves as the singular, authoritative reference for the core simulation mechanics as refined during the Combat and Movement Overhaul.

## 1. Spatial Legality & Occupancy
- **Singular Authority**: `LegalityService` is the sole source of truth for spatial rules.
- **Occupancy Rule**: Exactly one entity per walkable tile. No "passing through" occupied tiles.
- **Rejection Contract**: All legal rejections MUST return a structured `ActionReason` with `is_rejection=True`.

## 2. Combat Mechanics
- **Interaction Logic**: Engaging a target creates a bidirectional `combat_target_id` sticky link.
- **Weapon Range**: Manhattan-metric based, determined by `ITEM_REGISTRY` templates.
- **Resolution Services**:
  - `DamageResolutionService`: Handles mitigation, crits, and elemental logic.
  - `CombatAftermathService`: Handles social Interpretation, threat, and narrative memory.
- **Contextual Modifiers**:
  - **High Ground**: Multiplier bonus for terrain elevation (MOUNTAIN vs non-MOUNTAIN).
  - **Cover**: Defensive bonus vs ranged attacks (dist > 1) when behind WALL tiles.
  - **Flanking**: Attack bonus when target is bracketed by two hostiles on opposite sides (cardinal/diagonal geometry).
  - **Movement Penalty**: Accuracy/Damage penalty if the attacker moved in the current tick.

## 3. Tactical AI (MindAspect)
- **Evaluation Modes**:
  - `CLOSE`: Prioritize moving into combat range.
  - `MAINTAIN`: Hold position while in ideal range.
  - `WIDEN`: Reposition to increase distance from closer threats.
  - `RETREAT`: Flee when HP is critical.
  - `COVER`: Seek adjacent WALL tiles when threatened by ranged hostiles.
  - `CHOKEPOINT`: Hold 1-tile gaps when defending against approaching hostiles.
- **Role Ceilings**: Base stat growth obeys `TacticalRole` ceilings (Melee, Ranged, Tank, Support), while equipment allows for bounded specialization beyond base identity.

## 4. Anti-Stalemate & Oscillation
- **Combat Stalemate**: Detected when global HP and position entropy remain static for X cycles.
- **Movement Oscillation**: Detected when an entity jumps between two points (A-B-A-B) for 2 cycles; results in temporary pathing suppression.
- **Yielding**: Adjacent entities of the same faction will yield pathing priority to higher-ID actors to prevent gridlocks.

## 5. Observability & Auditing
- **Authoritative Reasons**: Every action proposal MUST contain an `ActionReason`.
- **Reason Codes**: Standardized mapping (e.g., `OCCUPANCY_VIOLATION`, `OUT_OF_RANGE`, `KITING`).
- **Arena Auditing**: `ScenarioReport` aggregates authoritative rejection counts to identify pathological simulation patterns during regression.

## 6. Resource Stability
- **Watchdog**: Simulation ticks are capped (default 2s) to prevent infinite loops/pathing hangs.
- **Hermetic Cleanup**: Each arena iteration performs explicit GC and reference clearing to ensure linear memory stability.
