# Implementation Plan: Legacy Restoration

## Goal
Restore and isolate legacy source and test assets to serve as a behavior oracle without interfering with the authoritative V2 engine.

## Proposed Changes

### [RESTORE] src_legacy/
- Restore from `6e5c289^`.
- Fix imports: `s/from src\./from src_legacy\./g`.

### [RESTORE] tests_legacy/
- Restore from `6e5c289^`.
- Fix imports: `s/from tests\./from tests_legacy\./g`.
- Fix imports to point to `src_legacy`.

### [MODIFY] tests/
- Relocate `tests/parity/` to `tests_legacy/parity/`.
- Ensure `tests/` is strictly V2.

### [MODIFY] tests/integrity/test_parity_guards.py
- Update `ORACLE_ROOT` to `tests_legacy/parity`.

## Verification Plan
- Run `pytest tests/` to ensure no regressions in the authoritative engine.
- Verify `src_legacy` is importable via `python3 -c "import src_legacy"`.
