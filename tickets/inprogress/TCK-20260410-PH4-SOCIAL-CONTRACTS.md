# TCK-20260410-PH4-SOCIAL-CONTRACTS

## Title
Implementation of Phase 4 Social Contracts, Party Formation, and Cooperative Coordination

## Status
INPROGRESS

## Request Summary
Implement the social contract layer to upgrade groups from tactical cliques to negotiated parties with explicit terms, role expectations, and remembered social consequences.

## Scope
- [x] phase_4_task_1: Define social contract and party records in the strategic domain
- [x] phase_4_task_2: Extend strategic updates and authoritative application for contracts
- [x] phase_4_task_3: Build ally discovery and candidate ranking logic
- [x] phase_4_task_4: Implement recruitment, negotiation, and offer mechanics
- [x] phase_4_task_5: Connect contracts to tactical group instantiation
- [x] phase_4_task_6: Role-aware party behavior and tactical coordination
- [x] phase_4_task_7: Apply social and reputational consequences for contract outcomes
- [x] phase_4_task_8: Integrate public reputation into recruitment viability
- [x] phase_4_task_9: Enhance social surfaces (Inns) for coordination
- [ ] phase_4_task_10: Observability and regression tests for social loops

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
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
