# TCK-20260527-COG-PHASE1-OPPORTUNITIES

## Title

Implement Phase 1 OpportunityProvider Layers (Resource & Service)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement ResourceOpportunityProvider and ServiceOpportunityProvider to expose a bounded set of relevant action choices based on nearby visible nodes or active blockers (crafting, buy/sell, resting, info, quests). Ensure that opportunities expose structured requirement lists for strategic tracing.

## Scope

- Implement Opportunity schemas and providers under `src/world/providers/resources.py` and `src/world/providers/services.py`.
- Support Resource gather and Service affordance opportunities (shop, blacksmith, guide, guild, inn).
- Add comprehensive unit tests under `tests/unit/strategic/test_opportunities.py`.

## Out of Scope

- Implementing the route-family classifier or performance budgets (Tasks 9-10).

## Acceptance Criteria

- Opportunity results are scoped and capped (e.g. max 5 results per query).
- Opportunities carry detailed lists of `Requirement` objects.
- Unit tests under `tests/unit/strategic/test_opportunities.py` pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Tasks 6 & 7)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/world/providers/resources.py`
- `src/world/providers/services.py`
- `tests/unit/strategic/test_opportunities.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Developed state-free static opportunity resolvers.
- Sorted opportunities dynamically by reward and capped output at 5.

## Test Summary

- Run `pytest tests/unit/strategic/test_opportunities.py` validating basic resource mapping, blocker-based reward boosting, and town service Rest/Repair dynamically.
- All 4 tests passed successfully.

## Files Changed

- `tickets/inprogress/TCK-20260527-COG-PHASE1-OPPORTUNITIES.md`
- `src/world/providers/resources.py`
- `src/world/providers/services.py`
- `tests/unit/strategic/test_opportunities.py`

## Completion Summary

- Implemented `ResourceOpportunityProvider` and `ServiceOpportunityProvider` with correct requirement structures, reward scaling based on biological/equipment states, and strict output caps of 5. All unit tests verified successfully.

