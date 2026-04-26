# Phase 8 Milestone 3: Bounded Tactical Audit

## 1. Current State of Tactical Decision Paths
As of Milestone 2 completion, the `src` engine lacks a centralized tactical decision layer. 

- **Target Selection**: Non-existent. Entities have no mechanism to evaluate neighbors or select a hostile target.
- **Engagement Logic**: Currently "implicit". Entities only act if their `TaskComponent` is manually set to `ENTITY_MOVE` or `ENTITY_ACT`. There is no reactive logic to engage a hostile that enters visibility.
- **Disengagement/Pursuit**: Unsupported. Entities follow a fixed `navigation.target` and do not adjust based on target movement.
- **Stickiness**: Non-existent. No state tracks which target an entity is currently "committed" to.
- **Anti-Stalemate**: Non-existent. 0-damage loops are possible if two entities have high defense and low attack.

## 2. Identified Strategy Leakage
- **Observation**: Some "Strategic" markers (leads/blockers) in `systems/strategic.py` are used to guide high-level goals (e.g., "Go buy gold"). 
- **Risk**: If these markers are used to directly pick combat targets, it breaks the phase boundary.
- **Remedy**: Tactical decisions must be based ONLY on the current `AuthoritativeState` (neighbors, relative HP, range) without consulting the long-horizon lead graph.

## 3. Gap Audit vs Phase 8 Backlog

| Gap ID | Description | Backlog Row Ref | Priority |
| :--- | :--- | :--- | :--- |
| **GAP-T01** | Missing deterministic target selection (ID-sorted, HP-based) | LEG-RPG-070 | HIGH |
| **GAP-T02** | Missing engage/pursuit intent generation | LEG-RPG-071 | HIGH |
| **GAP-T03** | Missing disengage/retreat threshold logic | LEG-RPG-072 | MEDIUM |
| **GAP-T04** | Missing combat stickiness (Target lock) | LEG-RPG-073 | MEDIUM |
| **GAP-T05** | Missing anti-stalemate (Action diversity/Timeout) | LEG-RPG-074 | LOW |

## 4. Proposed Tactical Evaluator Integration
The Tactical Evaluator should be integrated into the **INIT** phase or as a **PERIODIC** upkeep task that runs before **SCHEDULING**.

- **Option A (INIT)**: kernel calls `TacticalSystem.evaluate(state)` for all ready entities.
- **Option B (SCHEDULING)**: `DeterministicScheduler` calls `TacticalSystem` if an entity has no task.
- **Decision**: **Option B** is preferred as it keeps the `ApplyPipeline` clean of "planning" logic and only triggers AI when work is actually needed.
