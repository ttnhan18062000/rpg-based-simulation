# Test Plan: TCK-20260403-FINAL-CONVERGENCE

## Goals
Verify that the architectural pivot resolves circular dependencies and ensures deep recursive immutability without regression.

## Test Cases

### 1. Pydantic Model Stability (Happy Path)
- **Scenario**: Import `Entity` and `Snapshot` from different modules.
- **Verification**: Ensure no `PydanticUserError` or `NameError`.
- **Command**: `pytest tests/integration/test_snapshot_safety.py -v`

### 2. Deep Immutability (Edge Cases)
- **Scenario**: Freeze an entity with nested `list[str]` or `dict[str, int]`.
- **Verification**: Attempting to mutate nested collections must raise `TypeError` or `RuntimeError`.
- **Command**: `pytest tests/unit/core/test_aoa_integrity.py -v -k "test_deep_freeze"`

### 3. API Payload Determinism
- **Scenario**: Generate a grid and verify RLE encoding.
- **Verification**: Ensure that `MappingProxyType` serializes correctly with the custom `model_serializer`.
- **Command**: `pytest tests/integration/api/test_api_payload.py -v`

### 4. Full Regression Surface
- **Scenario**: Run all integration tests (748 test cases total).
- **Verification**: Total pass rate of 100%.
- **Command**: `./.venv/bin/pytest tests/integration/ -v | grep -v "chaos"`

## Failure Scenarios
- If `model_rebuild()` still fails, investigate import order in `__init__.py`.
- If serialization fails, verify `SimulationJSONEncoder` compatibility with `MappingProxyType`.
