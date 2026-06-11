---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260502-E5-CLOSURE-HARDENING
artifact_type: plan
tags: [e5, closure, hardening]
---

# Implementation Plan - E5 Closure Hardening

## Goal
Achieve architectural closure for Phase E5 by implementing robust conflict resolution, verifiable proof validation, and a machine-readable checklist ledger.

## Proposed Changes

### 1. Conflict Resolution (P0-2)
- [MODIFY] `src/core/conservation.py`: Ensure all destructive sources (`GROUND_ITEM`, `CORPSE`, `SHOP_BUY`) use the `reservations` system to prevent multi-actor duplicate looting in a single tick.
- [NEW] `tests/engine/test_resource_conflicts.py`: Add multi-actor conflict scenarios.

### 2. Transaction Grouping (P0-3)
- [VERIFY] `src/engine/pipeline.py`: Ensure `intent_groups` correctly collects non-contiguous intents.
- [NEW] `tests/engine/test_transaction_grouping.py`: Add tests for non-contiguous intent groups and group rollbacks.

### 3. Protocol Validator (P0-5)
- [NEW] `scripts/protocol_validator.py`: A script that parses `logic_checklist_exhaustive_v2.md` and validates that all checked rows have existing source and test paths.
- [MODIFY] `logic_checklist_exhaustive_v2.md`: Standardize markers to be machine-readable (e.g. `[DONE] source:path/to/src test:path/to/test`).

### 4. Certification Gate (P0-1)
- [MODIFY] `tests/certification/test_final_gate.py`: Update to validate real artifacts in `reports/release_proof/` instead of faking them in the test.

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_resource_conflicts.py`
- `pytest tests/engine/test_transaction_grouping.py`
- `python3 scripts/protocol_validator.py logic_checklist_exhaustive_v2.md`
- `pytest tests/certification/test_final_gate.py` (after running other tests)
