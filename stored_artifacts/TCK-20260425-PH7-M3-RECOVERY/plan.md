# PH7 M3: Inn, Home, and Class Hall Services

Implement deterministic recovery and progression through town services.

## Proposed Changes

### [Biological Logic] [NEW] [inn.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/inn.py)
- Implement `InnAction.rest(entity, state)`.
- Resets biological debt and applies "well-rested" status.

### [Home Progression] [NEW] [home.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/home.py)
- Implement `HomeAction.rest(entity, state)`.
- Implement `HomeAction.upgrade(entity, state)` to resolve maintenance blockers.

### [Progression Hub] [NEW] [class_hall.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/class_hall.py)
- Implement `ClassHallAction.train(entity, skill_id, state)`.
- Updates `IdentityComponent` and resolves capability blockers.

## Verification Plan

### Automated Tests
- `tests/town/test_recovery_class_hall.py`:
  - Verify Inn resets sleep debt and consumes gold.
  - Verify Class Hall training adds skill and resolves blocker.
  - Verify Home upgrade functionality.

#### Manual Verification
- Trace biological debt values across ticks after an Inn visit to ensure "well-rested" correctly delays debt accumulation.
