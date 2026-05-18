# Implementation Plan - RPG Documentation Rework [COMPLETED]

This plan outlines the restructuring of the V2 RPG Engine documentation into a hierarchical, developer-first suite. It aims to provide 100% clarity on the authoritative refinement process and the underlying state architecture.

## User Review Required

> [!IMPORTANT]
> **Nested Hierarchy**: I have moved existing files (e.g., `architecture.md` -> `docs/engine/architecture.md`). All links have been updated to reflect the new structure.
> **Logic Discrepancies**: I have identified a few missing checks in `ActorValidityPhase` (e.g., `CombatUpdate` checks for dead/stunned actors, `status_sleeping` check). I have added `TODO:` comments in the code to flag these for implementation.

## Proposed Changes

### Documentation Restructuring [COMPLETED]

The following structure has been established to mirror the `src/` organization:

#### docs/core/
- **state.md**: Technical specification of `AuthoritativeState`, component composition, and the "Frozen Lifecycle" law.
- **entities.md**: Entity composition and component mapping.

#### docs/engine/
- **authoritative_pipeline.md**: A high-resolution dive into the 17 refinement phases, including causal interdependencies and Logic IDs.
- **kernel.md**: Detailed breakdown of the 6-phase deterministic simulation loop.
- **architecture.md**: Relocated from `docs/` and updated to include the "Immediate Halt" law and certification proof paths.
- **README.md**: Entry point for engine documentation.

#### docs/systems/
- **combat_and_progression.md**: Relocated and updated to link explicitly to the `CombatRoutingPhase` and `RewardPhase`.
- **strategic_cognition.md**: Relocated and updated to define the "Cognition Capacity" and "Interruption Resistance" laws.
- **README.md**: Entry point for systems documentation.

#### docs/guidelines/
- **README.md**: Entry point for guidelines.

---

### Phase-by-Phase Documentation (authoritative_pipeline.md) [COMPLETED]

Documented each of the 17 phases with:
1. **Semantic Goal**: What does this phase achieve?
2. **Logic ID mapping**: (e.g., `COMB-028`).
3. **Primary Classes/Functions**: (e.g., `MovementPhase.resolve_position_swaps`).
4. **Causal Impact**: How does this phase affect subsequent phases.

### Audit & TODO Integration [COMPLETED]

Performed a final audit of the `src/` code against the new documentation and added `TODO:` tags for:
- Missing `status_sleeping` checks in `ActorValidityPhase`.
- Missing `CombatUpdate` rejection for dead actors in `ActorValidityPhase`.
- Magic number `30` in `StrategicIntelligenceSystem`.

## Verification Plan [COMPLETED]

### Automated Verification
- [x] **Link Check**: Used a custom Python script to ensure zero broken internal links in the new `.md` files.
- [x] **Integrity Tests**: Ran `pytest tests/docs/` (9 passed, 1 skipped).

### Manual Verification
- [x] **Visual Review**: Verified the clarity of the 17-phase causal chain in `authoritative_pipeline.md`.
- [x] **TODO Review**: Confirmed `TODO:` tags are placed in the correct source locations.
