# Test Plan: Final Non-Partial Implementation Tasks

## Test Cases

### 1. Mind Aspect Structural Integrity
- **Objective**: Ensure `MindAspect` uses typed models and rejects generic `Any` types.
- **Verification**: Use Pydantic's `model_validate` with strict typing on mock data. Correct types must be used for `perception`, `navigation`, `narrative`.

### 2. Typed Update Migration for Town Handlers
- **Objective**: Verify that `ActionProposal.updates` contains the necessary `IntentUpdate` subclasses for town/interaction activities.
- **Verification**: Mock `AIBrain.decide` for a hero with various town-state needs (shopping, crafting, Resting). Assert that `intent_metadata` is empty and `updates` contains correctly populated `ProgressionUpdate`, `IdentityUpdate`, etc.

### 3. ActionSystem Application of New Updates
- **Objective**: Ensure `ActionSystem` correctly applies the new `IntentUpdate` subclasses to the authoritative world state.
- **Verification**: Use integration tests involving `ResolutionPhase` and `ActionSystem.process_applied_actions`. Assert that `gold`, `inventory`, `hp`, etc., are correctly updated based on typed updates.

### 4. Phase-Boundary Enforcement
- **Objective**: Ensure AI handlers do not directly mutate snapshot actors.
- **Verification**: In a unit test, call `StateHandler.handle` with a mocked `AIContext` and `actor`. Assert that the `actor`'s state *before* and *after* the call is identical. Ensure `MappingProxyType` or `Frozen` assertions are triggered if mutation is attempted.

### 5. Regression Testing
- **Objective**: Run existing E2E tests to ensure no regressions in current combat and simulation flows.
- **Verification**: Command: `pytest tests/e2e/test_rpg_combat_scenarios.py`.
