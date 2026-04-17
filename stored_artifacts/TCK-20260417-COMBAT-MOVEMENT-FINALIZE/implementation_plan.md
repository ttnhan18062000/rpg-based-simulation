# Implementation Plan - Finalizing Combat Movement Milestone 7

Finalize the observability, rollout-hardening, and documentation consolidation for the Combat and Movement Overhaul.

## User Review Required

> [!IMPORTANT]
> This plan focuses on finishing the "ActionSystem Rejection Prefix" discrepancy and ensuring 100% documentation integrity for all seven milestones.

## Proposed Changes

### Core Models & Logic

#### [MODIFY] [reason_codes.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/reason_codes.py)
- Update `ActionReason` to include an optional `is_rejection` boolean field.
- Update `reason_text` to prepend "REJECTED: " if `is_rejection` is True.

#### [MODIFY] [action_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/gameplay/action_system.py)
- Ensure all legality failures use `ActionReason(code=..., is_rejection=True)`.
- Eliminate the legacy string-based prefixing logic.

### Documentation

#### [MODIFY] [combat_movement_implementation_milestone_7.md](file:///home/vboxuser/Work/rpg-based-simulation/combat_movement_implementation_milestone_7.md)
- Update implementation comments to reflect the finalized rejection prefixing logic.

#### [MODIFY] [combat_movement_overhaul_spec.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/combat/combat_movement_overhaul_spec.md)
- Final polish to ensure all rules are presented as "Authoritative" rather than "Proposed."

---

## Verification Plan

### Automated Tests
- Run all Milestone 7 tests safely:
  ```bash
  pytest tests/observability/ tests/rollout/ tests/docs/
  ```
- Verify `ActionSystem` rejections now carry the "REJECTED: " prefix in their string representation.

### Manual Verification
- N/A (Automated tests are authoritative).
