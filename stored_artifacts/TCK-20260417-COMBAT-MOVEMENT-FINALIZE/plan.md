# Implementation Plan - Combat Movement Milestone 7 Continuation

This plan outlines the steps to finalize Milestone 7 of the Combat and Movement Overhaul, focusing on structured observability, rollout hardening, and documentation integrity.

## User Review Required

> [!IMPORTANT]
> **Typed Reason Architecture**: We will migrate from free-form strings to a dedicated `ActionReason` model containing a `ReasonCode` Enum and a structured `ReasonPayload`. A `reason_text` property will be provided for backward compatibility with logs and the UI.

## Proposed Changes

### Core Logic and Models

#### [NEW] [reason_codes.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/reason_codes.py)
- Define `ReasonCode` Enum (e.g., `ADVANCING`, `OCCUPANCY_VIOLATION`, `OUT_OF_RANGE`, `LOW_HP_RETREAT`).
- Define `ActionReason` dataclass/model.

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/base.py)
- Update `ActionProposal` and `IntentUpdate` to use `ActionReason`.
- Implement `reason_text` property that formats the structured data for display.

#### [MODIFY] [movement_model.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/movement_model.py)
- Populate `ActionReason` with stable codes for all movement outcomes (Yielding, Sidestepping, Waiting).

#### [MODIFY] [action_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/gameplay/action_system.py)
- Update legality rejections to use `ActionReason` with specific codes and range/ID parameters.

#### [MODIFY] [tactical_evaluator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/tactical/tactical_evaluator.py)
- Update tactical evaluation to return structured `ActionReason` (e.g., `RETREAT`, `MAINTAIN_DISTANCE`).

### Documentation

#### [MODIFY] [combat_movement_overhaul_spec.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/combat/combat_movement_overhaul_spec.md)
- Expand the specification to include exhaustive tables of all structured reason keys and their meanings.
- Ensure all Milestone 7 contracts are fully detailed.

### Verification Plan

#### Automated Tests
- Expand `tests/observability/test_combat_movement_observability_contract.py` to verify all documented reason keys.
- Add regression tests to ensure that toggling `overhaul_features` flags does not cause inconsistent state transitions.
- Run `tests/docs/test_combat_movement_documentation_integrity.py` to ensure 1:1 mapping between code and docs.

#### Manual Verification
- Inspect entity decisions via the API/Presenter output to ensure `last_reason` contains the new structured data.
