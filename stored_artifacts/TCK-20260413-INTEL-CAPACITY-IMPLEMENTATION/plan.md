# Implementation Plan: Intel Capacity Milestone 1

## Goal Description
Implement the `CognitionCapacityProfile` model and `CognitionCapacityBuilder` as the structural foundation for bounded intelligence. This phase ensures a deterministic and typed contract for all later strategic reasoning behavior.

## User Review Required
> [!IMPORTANT]
> The implementation strictly follows the formulas and field names defined in `intel_capacity_implementation_milestone_1.md`. Any divergence from these formulas will be flagged.
>
> The builder is purely deterministic and does not yet change any strategic behavior. 
>
> No personality, trait, or emotional modifiers are included in this phase, as per the milestone document instructions.

## Proposed Changes

### [Component] Cognition Capacity Foundation

Summary: Create the core model and builder for cognition capacity.

#### [NEW] [cognition_capacity.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/cognition_capacity.py)
- Define `CognitionCapacityProfile(SimulationModel)`.
- Define `CognitionCapacityBuilder` with `build(entity, tick)` method.
- Implement exact formulas for sixteen fields using normalized attributes and stamina.

#### [NEW] [test_cognition_capacity_builder.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_cognition_capacity_builder.py)
- Unit tests for golden-value derivation (Case A, B, C from milestone doc).
- Tests for attribute caps and missing input fallbacks.

#### [NEW] [test_cognition_capacity_determinism.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_cognition_capacity_determinism.py)
- Tests to prove purity and determinism.

#### [NEW] [test_cognition_capacity_non_mutation.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/ai/test_cognition_capacity_non_mutation.py)
- Tests to prove the builder does not mutate entity state.

#### [NEW] [bounded_cognition_m1_contract.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/strategy/bounded_cognition_m1_contract.md)
- Documentation of the exact contract, inputs, and formulas.

#### [NEW] [bounded_cognition_m1_test_matrix.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/strategy/bounded_cognition_m1_test_matrix.md)
- Documentation of the test matrix and regression purposes.

## Verification Plan

### Automated Tests
- `pytest tests/ai/test_cognition_capacity_builder.py`
- `pytest tests/ai/test_cognition_capacity_determinism.py`
- `pytest tests/ai/test_cognition_capacity_non_mutation.py`

### Manual Verification
- Review the generated documentation files for accuracy and alignment with the milestone document.
