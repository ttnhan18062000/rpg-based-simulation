# Test Plan: TCK-20260330-CORE-STABILIZATION (Updated)

## Automated Verification

### 1. AI Cognitive Purity (Pillar 1)
- Test: `pytest tests/unit/ai/test_cognitive_pipeline.py`
- Expectation: `AIBrain.decide()` produces `memory_remove` metadata for dead entities, and the actor object remains unchanged.
- Case: Entity A is in Entity B's memory. Entity A dies. Entity B's next `decide()` call should propose removing Entity A from memory.

### 2. Engine Phase Orchestration
- Test: `pytest tests/unit/engine/test_world_loop_phases.py`
- Expectation: `WorldLoop` correctly initializes and executes phases in the order: `Scheduling > Collection > Resolution > Cleanup > Persistence`.
- Case: Mock each phase and verify they are called exactly once per tick with the correct context.

### 3. Determinism Verification
- Test: `pytest tests/integration/test_determinism_aoa.py`
- Expectation: `world.compute_hash()` is stable.
- Case: Run two identical worlds (same seed) and verify hashes match at tick 100, 500, 1000.
- Case: Verify results are DIFFERENT if seeds differ.

### 4. Legacy Regression (748 Tests)
- Test: `pytest tests/`
- Expectation: All existing tests pass after refactor.

## Manual Verification
- Visual Audit: Verify `src/engine/phases/` is completely decoupled from `WorldLoop` implementation.
- Visual Audit: Verify `src/ai/states/navigation.py` contains no direct state mutations.
