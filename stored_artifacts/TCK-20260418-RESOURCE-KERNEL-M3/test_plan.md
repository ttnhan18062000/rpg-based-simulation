# Test Plan: Resource-Safe Engine Milestone 3

## Purpose
Verify the memory-safety boundaries, model separation, and retention logic of the Milestone 3 runtime.

## Test Areas

### 1. Bounded Collections (`tests/core/test_bounded_collections.py`)
- **Goal**: Hard enforcement of container limits.
- **Tests**:
  - `test_bounded_list_overflow`: Add 200 items to `BoundedList[100]`, verify size is 100.
  - `test_bounded_dict_eviction`: Verify LRU or FIFO eviction for `BoundedDict`.
  - `test_reject_policy`: Verify that `REJECT` policy fails to add new items when full.

### 2. Model Separation (`tests/engine/test_runtime_state_contract.py`)
- **Goal**: Ensure no leakage of export/diagnostic models into the hot path.
- **Tests**:
  - `test_runtime_model_purity`: Scan `AuthoritativeState` for any Pydantic or complex DTO types.
  - `test_export_conversion`: Verify that `to_export()` produces an valid `ExportState` from a `RuntimeState` without mutating the source.

### 3. Registry Retention (`tests/engine/test_retention_logic.py`)
- **Goal**: Verify that registries and caches don't grow forever.
- **Tests**:
  - `test_event_log_retention`: Verify logs are pruned after 1000 entries.
  - `test_history_window`: Verify world history maintains exactly N generations.

### 4. Determinism vs Overflows (`tests/engine/test_overflow_determinism.py`)
- **Goal**: Ensure truncation/eviction doesn't break simulation determinism.
- **Tests**:
  - `test_deterministic_eviction`: Verify that eviction order is stable and same seed => same eviction sequence.

## Success Criteria
- 100% test pass.
- No memory leaks detected in stress tests.
