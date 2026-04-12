# Phase 1 Stage 15: Strategic Reprioritization — Plan

## Goal
Implement the link between the **Regional Consequence System** (Phase 4 legacy) and the **Strategic Appraisal Pass** (Phase 1). This ensures that heroes do not just experience world trauma as a background metric, but actively reprioritize their life goals and projects in response to high danger or the presence of local scars (battlefields, raids).

## Proposed Changes

### Logic Tier

#### [MODIFY] [strategic_evaluator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/strategic_evaluator.py)
- **Signature Change**: Update `evaluate(cls, entity: 'Entity', current_tick: int)` to `evaluate(cls, entity: 'Entity', world: 'WorldState', current_tick: int)`.
- **Regional Threat Detection**:
    - Use `src.core.world.regions.find_region_at(entity.spatial.pos, world.regions)` to find the current region.
    - Read `world.region_consequence_registry[region_id]`.
    - If `danger_level > 0.6` or `stability < 0.4`, create or update a `ConcernRecord(ConcernKind.THREAT)` with high priority (6.0+).
- **Scar Detection**:
    - Scan `world.scar_registry` for any scars within 10 units of the entity.
    - If found, create a `ConcernRecord(ConcernKind.OPPORTUNITY)` to investigate the site.
- **Project Selection Extension**:
    - Implement **Unified Concern Aggregation**: The evaluator now consolidates existing concerns with newly identified ones in a single pass to ensure the highest priority threat is selected.
    - **ID-Specific Dispatch**: Refined the project selection logic to only pivot to specialized projects (Survival vs. Stabilization) when the matching Concern ID is identified.
    - **Priority Normalization**: Capped Project and Objective priority at 5.0 to align with Phase 1 Pydantic schema constraints, while allowing Concern priority to remain high (up to 10.0) for interruption salience.
    - **Hysteresis Recovery**: Implemented threshold sensing (<0.3 danger) to clear crisis concerns and allow potential resumption of original projects.

#### [MODIFY] [brain.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/brain.py)
- Update `_strategic_appraisal_phase` to pass the `snapshot` (WorldState) to `StrategicEvaluatorService.evaluate`.

## Verification Plan

### Automated Tests
- **Integration Test**: `tests/integration/ai/test_strategic_reprioritization.py`
    - Setup: Seed a hero in a region with 0 danger. Verified pivot during crisis and recovery during safety.
    - Verification 1: Confirm hero pursues default directive-based project.
    - Mutation: Spike danger to 0.9.
    - Verification 2: Confirm hero generates a "Regional Threat" concern and pivots to "project_stabilization".
    - Recovery: Drop danger to 0.1.
    - Verification 3: Confirm threat concern is removed and strategic state stabilizes.

### Manual Verification
- Use CLI inspector to watch a hero's strategic state shift when a neighboring town is raided (simulated event).
