---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260419-MA-TASK5-FINAL-CLOSURE
artifact_type: test_plan
tags: [ma, task5, final, closure]
---

# Test Plan: Milestone A Closure Gating

## Objective
Establish the final "No-Drift" wall for Milestone A. This verification suite ensures that the core v2 engine runtime is strictly compliant with the Core Runtime Contract and that no accidental placeholders or structural departures exist in the baseline state.

## Automated Tests

### 1. Placeholder & Shadow Guard (`test_closure_no_placeholders`)
- **Action**: 
    1. Scan `src/engine` for `TODO`, `FIXME`, or `pass` in authoritative files.
    2. Explicitly verify that the `OPPORTUNISTIC` branch in the scheduler is the ONLY intended no-op.
- **Assertion**: Fail if any unacknowledged placeholders are found in the `Authoritative` path.

### 2. Contract Structural Integrity (`test_milestone_a_structural_compliance`)
- **Action**: Check for presence of:
    - `src/engine/kernel.py`: `Kernel`
    - `src/engine/apply.py`: `ApplyPath`
    - `src/engine/scheduler.py`: `DeterministicScheduler`
    - `src/engine/checkpoint.py`: `CanonicalStateHasher`
- **Assertion**: Fail if core classes or file names deviate from the documented contract.

### 3. Full Integration Regression
- **Action**: Run `pytest tests/engine` with total pass requirement.
- **Assertion**: 100% pass on 90+ tests.

## Manual Verification
- Verify that `runtime_completion_contract_ma.md` is updated with any final logic nuances.
- Ensure all Milestone A tickets are in `tickets/done`.
