# TCK-20260410-PH4-SOCIAL-CONTRACTS

## Title
Implementation of Phase 4 Social Contracts, Party Formation, and Cooperative Coordination

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implementing Phase 4 of the social system: Social Contracts and Party Formation.

## Scope
- recruitment negotiation lifecycle
- contract-to-group instantiation (GroupKind.PARTY)
- role-aware tactical hints (vanguard, support, healer)
- social and reputational consequence engine
- reputation-aware candidate selection
- Inn as a social hub for recruitment

## Acceptance Criteria
- [x] RecruitmentOfferRecord and SocialContractRecord models defined
- [x] RecruitmentNegotiationService handles offer generation and appraisal
- [x] GroupSystem authoritatively links SocialContractRecord to GroupRecord (PARTY)
- [x] AIBrain populates tactical hints based on contract roles
- [x] ContractOutcomeService applies bond and reputation updates
- [x] SocialCandidateSelectionService uses public reputation tags
- [x] VisitInnHandler allows offer evaluation
- [x] Integration test test_social_contract_flow.py passing

## Out of Scope
- Full implementation of multi-objective group projects (reserved for later).
- Dynamic faction-level treaty negotiations (out of current scope).

## Acceptance Criteria
- Entities can negotiate contract-backed parties with explicit terms (e.g. reward split, roles).
- Tactical groups are instantiated from accepted contracts and follow role-based coordination.
- Honoring or breaking contracts results in durable trust, debt, and reputation changes.
- Recruitment is filtered by trust, debt, and public reputation scores.
- All Phase 4 tests pass.

## Related Tickets
- TCK-20260410-PH3-STRATEGIC-KNOWLEDGE (Prerequisite)

## Related Docs
- thinking_implementation_phase_4.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260410-PH3-STRATEGIC-KNOWLEDGE/

## Related Code Areas
- src/core/models/strategy.py
- src/core/models/lived_structure.py
- src/actions/base.py
- src/systems/social/group_system.py
- src/ai/strategy/social_candidate_selection.py
- src/ai/strategy/recruitment_negotiation.py

## Assumptions / Open Questions
- **Question**: Should we allow multiple simultaneous contracts per entity? (Proposed: Yes, but with obligation conflicts if they overlap).

## Implementation Notes
- Maintain clean separation between Strategic Contracts and Tactical Groups.
- Use authoritative update path for all contract lifecycle events.

## Test Summary
- **Integration Test**: `tests/integration/social/test_social_contract_flow.py` (PASS)
- Verified E2E lifecycle: Candidate Selection -> Offer -> Acceptance -> Group Formation -> Tactical Coordination -> Resolution -> Consequences.

## Files Changed
- `src/core/models/strategy.py`: Added `SocialContractRecord`, `RecruitmentOfferRecord`, `ContractTermRecord`.
- `src/core/models/lived_structure.py`: Added `GroupKind.PARTY`.
- `src/actions/base.py`: Added `StrategicUpdate` (for contracts) and `SocialUpdate` (for bonds).
- `src/systems/social/group_system.py`: Implemented contract-to-group instantiation and dissolution consequences.
- `src/ai/brain.py`: Implemented role-aware tactical hints (vanguard, support, healer).
- `src/ai/strategy/social_candidate_selection.py`: Implemented reputation-aware ranking.
- `src/ai/strategy/recruitment_negotiation.py`: Implemented offer generation and appraisal.
- `src/ai/strategy/contract_outcome.py`: Implemented social/reputation consequence logic.
- `src/ai/states/town.py`: Updated Inn as recruitment hub.
- `tests/integration/social/test_social_contract_flow.py`: New E2E test.

## Completion Summary
Phase 4 successfully shifted the social layer from tactical cliques to negotiated cooperation. Entities now form purposeful parties with explicit roles and contract terms. The consequences of these interactions are durably remembered via the relationship and reputation systems, ensuring that social capital has real strategic value in the world.
