# Implementation Plan - TCK-20260325-RPG_SIMULATION_OVERHAUL

## Goal Description
Fully transition the WorldLoop RPG into a production-grade ARPG engine by merging "Cognitive Thinking" refinements (TCK-20260322) with "Systemic Performance & Depth" overhauls (TCK-20260325).

## Proposed Changes

### 1. Cognitive Overhaul (Mind & Thinking)
- [MODIFY] `src/ai/brain.py`:
    - Refactor `decide()` into explicit 7-step pipeline: Sensing → Perception → Memory → Appraisal → Deliberation → Tactical → Proposal.
    - Optimize by caching `visible_entities` in `AIContext`.
    - Implement **Softmax Temperature Selection** based on the `Openness` trait.
- [MODIFY] `src/core/aspects/mind.py`: Add `life_directive` (Ambition enum) and `region_fatigue` (Memory).

### 2. High-Performance Movement (The Path)
- [NEW] `src/ai/flow_fields.py`: `FlowFieldManager` (Dijkstra Maps) for Town/Camps.
- [MODIFY] `src/actions/movement.py`: Switch to Flow Field vectors for dist > 15 to bypass A* overhead.

### 3. Combat & Physicality (The Body)
- [MODIFY] `src/core/attributes.py`: 
    - Replace logarithmic action delay with **Fractional Hyperbola** `10 / (10 + spd)`.
    - Implement **Attribute Soft-Caps** at `(Level * 5) + Base`.
- [MODIFY] `src/actions/damage.py`: Implement **Fractional Armor Mitigation** `raw / (raw + def*2)`.
- [MODIFY] `src/systems/progression_system.py`: Add `EXHAUSTED` state and debuffs.

### 4. Economy & Heritage (Social & Trade)
- [NEW] `src/systems/enhancement_system.py`: Material-gated gold sinks (+1 to +15).
- [MODIFY] `src/core/buildings.py`: Blacksmith enhancement + Town Treasury (Trade caps).
- [NEW] `src/core/corpse.py`: `Corpse_Node` drop/recovery system.

### 5. World Purity (Evolution & Strategy)
- [NEW] `src/systems/evolution_system.py`: **Nemesis Evolution** (Monster Tier-up on killing heroes).
- [MODIFY] `src/systems/strategy_system.py`: Replace regional debuffs with **Stronghold Auras**.

### 6. Ambition & Memory (Long-Term Cognition)
- [MODIFY] `src/ai/goals.py`:
    - Apply `life_directive` score multipliers (The "Obsession" gravity well).
    - Implement **Memory Fatigue** penalties for recently visited regions (The "Anti-Loop" mechanism).

---

## Verification Plan
### Automated Tests
- `pytest tests/unit/ai/test_cognitive_pipeline.py`: Verify 7-step decoupled logic.
- `pytest tests/unit/ai/test_ambition_bias.py`: Verify life directives bias scoring correctly.
- `pytest tests/unit/systems/test_flow_fields.py`: Verify O(1) pathfinding lookups.
- `pytest tests/unit/systems/test_nemesis_progression.py`: Verify monster evolution.
