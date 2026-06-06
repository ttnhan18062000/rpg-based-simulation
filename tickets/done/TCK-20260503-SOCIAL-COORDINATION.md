# TCK-20260503-SOCIAL-COORDINATION

## Title
Hardening Social Contracts, Party Cooperation, and Goal Registry (Domain 4)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Complete the final domain (Domain 4) of the `unchecked_logic_implementation_plan.md` to achieve full hardening of the RPG V2 engine.

## Scope
- Implement trust/reputation consequences for contract honoring/betrayal in `SocialContractSystem`.
- Enforce strict `ContractStatus` transitions with comprehensive validation.
- Implement shared-target validity checks in `PartyCoordinationSystem`.
- Enhance `GoalRegistry` to ensure uniqueness and stable mapping of strategic goals.
- Implement basic place attachment and nemesis memory logic.

## Out of Scope
- Major expansion of social simulation beyond the V2 authoritative contract requirements.

## Acceptance Criteria
- Contracts transitioning to `FULFILLED`, `FAILED`, or `BETRAYED` affect trust scores in the `SocialComponent`.
- Invalid contract transitions are rejected by `SocialContractSystem`.
- Party members clear shared targets if the target is dead or invalid.
- `GoalRegistry` rejects duplicate scorers and provides stable goal mappings.
- Tests verify nemesis creation after repeated hostile encounters.

## Related Tickets
- TCK-20260503-HARDEN-COGNITION (Domain 2 & 3)

## Related Docs
- `unchecked_logic_implementation_plan.md` (Domain 4)

## Related Code Areas
- `src/systems/social_contract.py`
- `src/systems/party.py`
- `src/ai/goals/base.py`
- `src/core/strategic.py`
- `src/core/state.py`
