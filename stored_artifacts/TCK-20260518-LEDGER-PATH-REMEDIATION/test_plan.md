---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-LEDGER-PATH-REMEDIATION
artifact_type: test_plan
tags: [ledger, path, remediation]
---

# Test Plan: Release Gate Certification

## Automated Tests

### 1. Standalone Ledger Validator Verification
Run the standalone validator script:
```bash
python3 scripts/ledger_validator.py
```
**Expected Outcome**: Output reports `CRITICAL ERRORS (0)` and `[PASS] No critical integrity violations found.`, with 0 `WARNINGS` regarding non-existent paths.

### 2. Standalone Release Gate Verification
Run the authoritative release gate certification script:
```bash
python3 scripts/release_gate.py
```
**Expected Outcome**: Script outputs `[PASS] Checklist is valid.` and `[SUCCESS] Successfully validated 6 certification targets.`, returning exit code 0.

### 3. Pytest Certification Test Suite
Run the CI integration test suite for the final gate:
```bash
pytest tests/certification/test_final_gate.py
```
**Expected Outcome**: All 3 tests (`test_gate_rejects_missing_artifacts`, `test_gate_rejects_malformed_bundle`, `test_real_release_proof_is_valid`) pass successfully in < 1.0s.

## Regression Checks
Run the full active V2 test suite to ensure no collateral regression:
```bash
pytest tests/
```
**Expected Outcome**: All 1118 tests pass successfully.
