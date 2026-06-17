---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 8 Entry Support Boundary

This document defines the honest truth of combat and tactical support in `src` at the start of Phase 8.

## 1. Currently Supported Semantics (Legacy Precursors)

### A. Combat Legality (Basic)
- **Melee Adjacency**: Supported via `SpatialHash` and `LegalityService`.
- **Ranged Distance**: Supported (flat distance checks).
- **LoS (Line of Sight)**: Basic ray-casting against world grid.

### B. Combat Outcomes (Substrate Only)
- **Authoritative Resolution**: The engine supports emitting combat results (damage/defeat) as updates.
- **HP/Readiness Drain**: Basic state application is supported.

### C. Basic Movement AI
- **Pathfinding (A*)**: Supported for world grid.
- **Flow Fields**: Supported for swarm-style navigation.
- **Redirection**: Yielding and sidestepping are supported for congestion.

## 2. Explicitly Unsupported / Gap Remainder

### A. Advanced Tactical Logic (Phase 8 Targets)
- **Cover Seeking**: Entities do not yet recognize or seek cover during combat.
- **Chokepoint Holding**: No spatial tactical awareness.
- **Flanking/Bracketing**: No group-coordinated tactical positioning.
- **Target Stickiness**: Entities may oscillate between targets without bias.

### B. Strategic & Social Semantics (Phase 9 Targets)
- **Betrayal/Avenge**: Social trust history does not yet drive strategic decision-making.
- **Dynamic Quests**: Pending.
- **Rumors & Narrative**: Pending.

## 3. Divergence Record
- **Authoritative State**: All combat results are frozen until the end of the tick (Phase 7 rule).
- **Determinism**: Combat RNG is strictly driven by the `Platform.RNG` system.

## 4. Readiness Rating
- **Substrate**: **GOLD** (Phase 7 hardened).
- **Semantics**: **BRONZE** (Primitive combat, minimal tactical awareness).
