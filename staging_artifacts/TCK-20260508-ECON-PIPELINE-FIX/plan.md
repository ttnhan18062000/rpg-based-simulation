# RPG Pipeline Stabilization & Regression Fix

## Goal Description
Restore full parity across the regression test suite (101 current failures) by reconciling the `ResourceTransactionSystem` with the engine's auditing requirements and restoring omitted world simulation systems.

## Proposed Changes

### [Component] Engine Economy
#### [MODIFY] [economy.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/economy.py)
- Record `IntentResult` objects for every processed `ResourceTransferIntent`.
- Populate `EntityUpdate.intent_results` with these results to ensure downstream systems and tests can audit transaction outcomes.

### [Component] Engine Interaction
#### [MODIFY] [interaction.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/interaction.py)
- Update `InteractionSystem.enforce` to set `reset=True` on the `InteractionUpdate` when an interaction is completed or fails due to pressure.
- This ensures that entities don't get stuck in a "finished" interaction state.

### [Component] Authoritative Pipeline
#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Restore `WorldDynamicsSystem.resolve_dynamics` to the orchestration flow.
- Order it before Resource Transactions to ensure hazards are calculated against the pre-transfer state if necessary, or after if they depend on results (Phase 7 standard is after Action but before Movement).
- Verify and correct all system method calls (`GroupSystem`, `LifecycleSystem`, etc.).
- Ensure `EntityGenerator` is properly provided to systems that require it (e.g., `WorldDynamicsSystem`).

## Verification Plan

### Automated Tests
- Run the core regression suite:
  `pytest tests -k "not (test_long_run_determinism.py or test_long_run_stability.py)"`
- Specifically verify:
  - `tests/unit/test_interaction_system.py`
  - `tests/verify/test_recovery_gaps.py`
  - `tests/engine/test_transaction_grouping.py`

### Manual Verification
- None required; the regression suite is exhaustive.
