---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260427-LEGACY-RESTORATION
artifact_type: test_plan
tags: [legacy, restoration]
---

# Test Plan: Legacy Restoration

## Automated Tests
- **V2 Suite**: Run `python3 -m pytest tests/`. 
    - Expected: 521+ passing tests. No `ModuleNotFoundError` for legacy assets.
- **Import Verification**: 
    - `export PYTHONPATH=$PYTHONPATH:$(pwd) && python3 -c "import src_legacy; from src_legacy.core.state import AuthoritativeState; print('Legacy Import OK')"`

## Integrity Verification
- **Parity Guards**: Run `pytest tests/integrity/test_parity_guards.py`.
    - Expected: PASS (verifies oracles are found in `tests_legacy/parity`).

## Manual Verification
- Verify `src_legacy/` exists and contains files.
- Verify `tests/parity/` no longer exists.
