# TCK-20260501-STRAT-HARDENING

## Title

Strategic Cognition Lifecycle Hardening

## Status

DONE

## Request Summary

Implement the complete Phase E4.3 Strategic Cognition Lifecycle, ensuring actors pursue durable goals, react to environmental pressures (concerns), infer explicit blockers from failures, and generate alternative paths (detours) using strategic memory.

## Scope

- [x] Implement `Inventory Full` concern and blocker generation.
- [x] Implement `Low HP` and `Reward Pending` concern generation.
- [x] Implement Detour suggestions for `Inventory Full` (Sell/Store) and `Low HP` (Heal).
- [x] Enhance Strategic Memory: Suppress failed leads and bias future goal scoring based on project outcomes.
- [x] Implement `StrategicUpdate` propagation for learning events (Turning Points).
- [x] Create comprehensive lifecycle test suite in `tests/engine/test_strategic_lifecycle.py`.

## Out of Scope

- Full social contract lifecycle (Phase E4.4).
- Advanced crafting/skill unlocking (Phase E4.5).

## Acceptance Criteria

- [ ] Actors generate `INVENTORY_FULL` concerns when storage is at capacity.
- [ ] `ResourceTransactionResolver` rejections for capacity trigger `INVENTORY_FULL` blockers.
- [ ] Detour system suggests "Return to Town" when inventory is full or HP is critically low.
- [ ] Failed leads are suppressed for 500 ticks and marked `EXHAUSTED` after 3 attempts.
- [ ] Project abandonment increments frustration/boredom, biasing future selection.
- [ ] Test suite verifies end-to-end: Project -> Blocker -> Detour -> Success -> Resumption.

## Related Tickets

None

## Related Docs

- [resource_v2_e4_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e4_phases.md)

## Related Stored Artifacts

None

## Related Code Areas

- `src/core/strategic.py`
- `src/engine/cognition.py`
- `src/engine/tactical.py`
- `src/systems/strategic.py`
- `src/systems/detour.py`
- `src/systems/routine.py`

## Implementation Notes

- Use `StrategicUpdate` as the primary carrier for learning and state transitions.
- Ensure all logic is deterministic and relies only on the `AuthoritativeState`.

## Test Summary

None

## Files Changed

None

## Completion Summary

None
