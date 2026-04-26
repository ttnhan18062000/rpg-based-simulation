# TCK-20260421-RESOURCE-INTERACT-PARITY

## Title
Implement Initial Resource Interaction Differential Parity Proof

## Status
DONE

## Request Summary
Introduce the first old-vs-new proof layer for resource interaction behavior (Harvesting and Looting) to ensure bit-identical outcome parity where preservation is intended.

## Scope
- Create `tests/parity/test_resource_interaction_parity.py`.
- Integrate with existing `tests/parity/interaction_oracle/results.json` oracle data.
- Refactor logic from `tests/parity/interaction_oracle/capture_src_interaction.py` into `pytest` assertions.
- Verify parity for:
  - Harvesting progress advancement.
  - Harvesting completion (item addition, node depletion).
  - Looting completion.
  - Inventory pressure (slots/weight) failure cases.

## Out of Scope
- Implementing new interaction features.
- Broad economy or crafting resolution.
- Performance benchmarking.

## Acceptance Criteria
- `pytest tests/parity/test_resource_interaction_parity.py` passes using `results.json` as the source of truth.
- Failures are clearly reported with diffs between oracle and V2 outcomes.
- Supported cases (Harvest, Loot, Pressure) are covered.

## Related Tickets
- TCK-20260421-MOV-PARITY-PROMO (Previous parity promotion)

## Related Docs
- [resource_phase5_implementation_milestone_1.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase5_implementation_milestone_1.md)
- [src_principle.md](file:///home/vboxuser/Work/rpg-based-simulation/src_principle.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/interaction.py`
- `tests/parity/interaction_oracle/`

## Assumptions / Open Questions
- **Assumption**: `results.json` captures all currently intended preserved behaviors for the supported slice.
- **Question**: Should we also test "respawn_cooldown" parity here? (The high-level plan mentions depletion/respawn).

## Implementation Notes
- Use `pytest.mark.parametrize`.
- Mock or setup `AuthoritativeState` with required `ResourceNode` and `EntityState` containing inventory.

## Test Summary
- 100% Pass in `tests/parity/test_resource_interaction_parity.py`.
- Verified bit-identical harvest and loot outcomes.

## Files Changed
- `src/engine/interaction.py`
- `tests/parity/test_resource_interaction_parity.py`

## Completion Summary
- Implemented the first resource-specific differential parity layer.
- Verified that harvesting progress and inventory addition match src logic.
- Enforced inventory pressure (slots/weight) laws in the interaction system.
