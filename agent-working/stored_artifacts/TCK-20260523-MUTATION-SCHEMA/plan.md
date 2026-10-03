---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-SCHEMA
artifact_type: plan
tags: [mutation, schema]
---

# Implementation Plan - MutationSpec Schema & Validator

This plan outlines the technical steps to implement Milestone 84 in the `src/lab/` package.

---

## 1. Steps of Implementation

### Phase 1: Schema Integration
1. Open `src/lab/schema.py`.
2. Implement custom exception `InvalidMutationSpecError` (extending `Exception`).
3. Add helper classes:
   - `BaseMutation` (BaseModel)
   - `NumericMutation` (BaseMutation)
   - `SetMutation` (BaseMutation, Literal operation="set", value=Any)
   - `AddMutation` (NumericMutation, Literal operation="add")
   - `MultiplyMutation` (NumericMutation, Literal operation="multiply")
   - `ToggleMutation` (BaseMutation, Literal operation="toggle", value=Optional[bool])
   - `RemoveMutation` (BaseMutation, Literal operation="remove")
   - `DuplicateMutation` (BaseMutation, Literal operation="duplicate", value=str)
4. Combine into `MutationItem` type alias using Pydantic `Annotated[Union[...], Field(discriminator="operation")]`.
5. Implement `MatrixSpec`, `ExpectedRelationshipSpec`, `MutationBudgetsSpec` sub-models.
6. Implement root `MutationSpec` model with all required validations (like `schema_version` matching `"mutationspec.v1"`).
7. Implement `load_mutation_spec_from_yaml` function with clean error handling, logging, and traceback-protection.
8. Expose new items in `__all__` or imports as appropriate.

### Phase 2: Pluggable Validator Integration
1. Open `src/lab/validator.py`.
2. Define base class `MutationValidationRule`.
3. Implement `BaseReferencesRule` to check existence of referenced world and scenario specs against active repository collections.
4. Implement `MetamorphicRelationshipRule` to verify metamorphic variant identifiers exist in `mutations` and reference standard metrics or emit unrecognized warnings.
5. Implement root `MutationValidator` engine orchestrator to run all rules, manage results, and support `strict` error-elevation policies.

### Phase 3: Comprehensive Unit Tests
1. Create `tests/unit/lab/test_mutationspec_schema.py`.
2. Add tests covering YAML safe loading, polymorphic union operation types, invalid operation values/types, invalid matrix modes, and unknown field preservation.
3. Create `tests/unit/lab/test_mutationspec_validator.py`.
4. Add tests covering base references verification, metamorphic variant existence checks, unrecognized metric warnings, and strict validation mode.

---

## 2. Verification Steps

1. Run newly implemented tests using:
   ```bash
   python3 -m pytest tests/unit/lab/test_mutationspec_schema.py tests/unit/lab/test_mutationspec_validator.py -v
   ```
2. Run full lab unit test suite to check for regressions:
   ```bash
   python3 -m pytest tests/unit/lab/ -v
   ```
