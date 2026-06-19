---
status: active
layer: engine
authority: P1
audience: developer
---

# `src` Known Limitations

This document records the current technical limitations, unsupported features, and runtime constraints of the `src` engine.

## 1. Gameplay / Mechanics Limitations

### 1.1 Spatial / Navigation
- **Linear Stepping Only**: Pathfinding through dynamic obstacles (e.g., other entities or newly spawned objects) is best-effort. V2 currently relies on direct linear stepping toward coordinates for supported proofs.
- **Congestion Weakness**: While congestion is handled by yielding, high-density entity overlaps are not yet hardened against all edge cases.

### 1.2 Resource loops
- **No Complex Regeneration**: Resource nodes do not currently support complex regeneration logic (e.g., seasonal growth, depletion cooldowns). Nodes are static or reset on scenario reload.
- **Town Buildings**: `TownResolutionSystem` currently supports Blacksmith (crafting), Inn (REST), and Tavern (EAT) building types. Guilds, Class Halls, and other building types are not yet functionally integrated.

### 1.3 Strategic AI
- **Material-Only Blockers**: The `StrategicIntelligenceSystem` only recognizes and resolves crafting blockers for "Material" resources. Social, capability, or plot-based blockers are unsupported.
- **Location-Only Leads**: Strategic leads are restricted to coordinate-based locations. Concept or person-based leads are not yet modeled in the supported slice.

## 2. Runtime / Performance Constraints

### 2.1 Execution Modes
- **Worker Parity**: While concurrency (Thread/Worker) is implemented, bit-identical parity vs original `src` is only officially ratified for the **Sequential** execution mode.

### 2.2 System Contention
- **Deterministic Resolution**: Contention for limited resources (e.g., two entities looting the same corpse) is resolved by deterministic registration order. Complex social negotiation or "roll-off" logic is not yet implemented.

## 3. Tooling / Observability
- **Metric Granularity**: Some runtime signals (e.g., per-entity strategic bandwidth) are visible in the engine but not yet exported to the external Prometheus/Grafana baseline.

---
*Last updated: 2026-04-21.*
