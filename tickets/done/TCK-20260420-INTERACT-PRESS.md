# TCK-20260420-INTERACT-PRESS

## Title
Weight Pressure and Inventory Parity Enforcement

## Status
INPROGRESS

## Request Summary
Implement the 'Pressure Law' for inventory weight, matching the original `src` behavior. Current v2 only checks slot availability.

## Scope
- Implement `current_weight` calculation in `ApplyPath`.
- Enforce `max_weight` limit in `InteractionSystem.enforce`.
- Define item weight (default 1.0 if not specified).

## Acceptance Criteria
- [ ] Entities cannot harvest or loot if it would exceed `max_weight`.
- [ ] Interaction resets on weight-based rejection.

## Files Changed
- `src/engine/interaction.py`
- `src/engine/apply.py`
