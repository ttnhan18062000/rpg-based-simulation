# AOA Convergence Implementation Plan (TCK-20260405-CONVERGENCE)

## Proposed Changes

### Core System Alignment
1. **Combat Statistics**: Restore `bravery_mult` shim in `CombatAspect` for AI scaling.
2. **Entity Construction**: Update `EntityBuilder.build()` to pass `difficulty_tier` to the `SpatialAspect`.
3. **Action System**: Finalize `ActionSystem.apply_action_state_transitions` for authoritative quest reward mapping.

### Test Suite Migration
1. **Quest Tests**: Refactor `tests/test_quests.py` to use `ProgressionAspect` for reward and status logic.
2. **AI Goal Tests**: Refactor `tests/unit/ai/test_goals.py` to use `GoalType` enums.
3. **World Mapping**: Refactor `tests/integration/world/test_regions.py` and `test_voronoi_regions.py` to use direct attribute access on `Region` and `Location` models.
4. **Perception & Emotions**: Repath `test_attention.py` and `test_emotions.py` to modular `MindAspect` sub-models.

## Affected Components
- `src_legacy.core.entities.entity_builder`
- `src.core.aspects.combat`
- `tests.test_quests`
- `tests.unit.ai.*`
- `tests.integration.world.*`
- `tests.benchmarks.*`
