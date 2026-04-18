# Test Plan: Resource-Safe Engine Milestone 5

## Purpose
Verify the authoritative resource governor and degradation state machine for Milestone 5.

## Test Areas

### 1. Pressure detection and Mode Transition (`tests_v2/engine/test_resource_governor_contract.py`)
- **Goal**: Verify correct escalation / recovery.
- **Tests**:
  - `test_escalation_path`: Normal -> Constrained -> Degraded -> Survival as signals rise.
  - `test_recovery_hysteresis`: Verify that recovery requires multiple ticks of low pressure.
  - `test_threshold_integrity`: Verify transitions happen at the exact profile limits.

### 2. Degradation Policy (`tests_v2/engine/test_degradation_order.py`)
- **Goal**: Verify that shedding follows the matrix.
- **Tests**:
  - `test_opportunistic_shedding`: Verify `OPPORTUNISTIC` is dropped first.
  - `test_diagnostic_reduction`: Verify `DIAG_VERBOSITY` is lowered in `CONSTRAINED`.
  - `test_authoritative_preservation`: Verify `CRITICAL` work *never* drops even in `SURVIVAL`.

### 3. State Consistency
- **Goal**: Ensure `RuntimeMode` is authoritative.
- **Tests**:
  - `test_mode_survives_checkpoint`: Verify that mode state is captured in the hasher and survives restart.

## Success Criteria
- 100% test pass.
- No semantic corruption in SURVIVAL mode.
