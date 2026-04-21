# TCK-20260421-RESOURCE-CONTRACT

## Title
Resource Contract and Domain invariants

## Status
DONE

## Request Summary
Establish authoritative contract tests for resource interactions and ensure the InteractionSystem enforces all domain invariants (weight pressure, slot capacity, etc.) regardless of AI proposals.

## Scope
- Implement `tests_v2/contract/test_resource_contract.py`.
- Verify weight pressure law in `InteractionSystem.enforce`.
- Verify slot pressure law in `InteractionSystem.enforce`.
- Verify node depletion and respawn triggers.

## Out of Scope
- Actually implementing node respawn logic (that's economy system).
- Movement anti-oscillation (done in Milestone 2).

## Acceptance Criteria
- `test_resource_contract.py` passes all scenarios.
- InteractionSystem correctly rejects/resets proposals that violate capacity laws.
- Node charges are correctly decremented upon successful harvest.

## Related Tickets
- TCK-20260421-RESOURCE-INTERACT-PARITY

## Related Docs
- docs/engine/src_v2_principle.md

## Related Code Areas
- src_v2/engine/interaction.py
- src_v2/core/state.py

## Implementation Notes
- Use `pytest` for contract testing.
- Focus on "Refining" the updates to be legal.

## Test Summary
- 100% Pass in `tests_v2/contract/test_resource_contract.py`.
- 100% Pass in `tests_v2/contract/test_resource_intelligence_contract.py`.

## Files Changed
- `src_v2/engine/interaction.py`
- `src_v2/systems/strategic.py`
- `src_v2/core/strategic.py`

## Completion Summary
- Established authoritative contract tests for resource interaction and intelligence.
- Verified that weight/slot pressure laws are enforced in the engine hot-path.
- Implemented `StrategicIntelligenceSystem` for deterministic blocker and lead generation.
