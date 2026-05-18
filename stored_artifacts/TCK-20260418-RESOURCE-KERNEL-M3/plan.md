# Implementation Plan: Resource-Safe Engine Milestone 3

## Purpose
Establish the bounded-state foundation and separate hot-path models from diagnostic/export models.

## Proposed Changes
1. **Documentation**: `runtime_state_contract_m3.md`, `m3_retention_matrix.md`.
2. **Primitives**: `BoundedList`, `BoundedDict` in `collections.py`.
3. **Model Separation**: `ExportModel`, `DiagnosticModel`. Refactor `AuthoritativeState`.
4. **Retention Logic**: Apply bounds to logs, history, and registries.

## Task List
- [ ] Draft docs and matrices
- [ ] Implement `collections.py` (Bounded containers)
- [ ] Implement `export.py` and `diagnostic.py`
- [ ] Refactor `state.py` for purity/slots
- [ ] Write `tests/` for boundedness and separation
- [ ] Verify memory stability
