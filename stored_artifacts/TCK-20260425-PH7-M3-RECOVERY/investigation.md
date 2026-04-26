# Investigation — PH7 M3: Inn, Home, and Class Hall Services

## Goal
Implement town recovery services and progression hubs.

## Requirements
- **Inn Service**: Recovery of `BiologicalComponent.sleep_debt` and `hunger`. Requires gold.
- **Home Service**: Private storage (already done in M5) and "private rest" (no gold cost but slower recovery).
- **Class Hall**: Learning "recipes" or "skills" (represented as `IdentityComponent.known_recipes`).
- **Blocker Resolution**: Skills should resolve `BlockerState` of type `capability`.

## Proposed Architecture

### 1. Inn Service (`town/inn.py`)
- `InnAction.rest(entity, state) -> StateUpdate`:
  - Consumes gold (e.g., 5 gold).
  - Resets `sleep_debt` to 0.0 and sets `well_rested_until`.

### 2. Home Service (`town/home.py`)
- `HomeAction.rest(entity, state) -> StateUpdate`:
  - Reduces `sleep_debt` (e.g., by 50%).
  - No gold cost.

### 3. Class Hall (`town/class_hall.py`)
- `ClassHallAction.train(entity, skill_id, state) -> StateUpdate`:
  - Consumes gold (e.g., 50 gold).
  - Adds `skill_id` to `IdentityComponent.known_recipes`.
  - Scans `strategic.blockers` for `kind="capability"` and `subject=skill_id` to resolve them.

## Questions
- Is "well-rested" a buff?
  Yes, `BiologicalComponent` has `well_rested_until`.
- How do we handle "Maintenance Blockers"?
  Task 7.3 says "Home upgrade resolves maintenance blocker". This might involve a `HomeAction.upgrade`.
