---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH7-M4-SABOTAGE
artifact_type: plan
tags: [ph7, m4, sabotage]
---

# PH7 M4: Building Damage and Sabotage

Implement authoritative building damage and regional trauma.

## Proposed Changes

### [World Logic] [NEW] [sabotage.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/sabotage.py)
- Implement `SabotageAction.apply(entity, building_id, state)`.
- Validates target and applies damage.

### [Regional Trauma] [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Update `apply_generation` to increment regional `trauma_score` when a building becomes non-functional.

## Verification Plan

### Automated Tests
- `tests/town/test_building_sabotage.py`:
  - Verify sabotage reduces building HP.
  - Verify building becomes non-functional at 0 HP.
  - Verify regional trauma increases on building destruction.

#### Manual Verification
- Snapshot audit of building functional status after simulated raid.
