---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260411-SOCIAL-CONTRACTS
phase: done
date: 2026-04-11
tags: [social, contracts]
---

# TCK-20260411-SOCIAL-CONTRACTS: Social Contract Hardening (Phase 3 Improvement)

**Title**: Implement Negotiation Lifecycle, Consequence closure, and Role-Aware Parties

**Status**: DONE

**Request Summary**: Execute [Improvement Phase 3] from `thinking_implementation_improvement.md`. Harden recruitment negotiation, implement authoritative contract consequences, and upgrade parties to be role-aware.

**Scope**:
- [MODIFY] `src/core/models/strategy.py`: Add negotiation history.
- [MODIFY] `src/ai/strategy/recruitment_negotiation.py`: Implement haggling loop and expiry.
- [NEW] `src/core/logic/contract_consequence_service.py`: Centralize honor/breach logic.
- [MODIFY] `src/systems/social/group_system.py`: Integrate consequence service and assign roles.
- [MODIFY] `src/ai/strategy/objective_to_goal_mapper.py`: Expand role-based biases.

**Out of Scope**:
- Implementing a full graphical UI for negotiation.
- Changing basic GroupSystem cohesion physics.

**Acceptance Criteria**:
- Entities can counter-offer terms during recruitment.
- Negotiation history is persisted and affects future willingness.
- Honoring or breaching a contract has deterministic effects on Trust and Reputation.
- Part members behave according to assigned roles (e.g., Vanguard vs Support).
- Verified with integration tests.

**Related Tickets**:
- TCK-20260410-BUILDING-UNIFICATION (Phase 2 Improvement)

**Related Docs**:
- `thinking_implementation_improvement.md`
- `doc/architecture.md`

**Implementation Notes**:
- Implemented multi-turn haggling in `RecruitmentNegotiationService`.
- Created `ContractConsequenceService` for authoritative Trust/Reputation updates.
- Expanded `ObjectiveToGoalMapper` with role-based tactical biases.

**Test Summary**:
- `tests/test_social_contracts.py`: PASSED (Negotiation & Consequences)
- `tests/test_party_tactics.py`: PASSED (Role-Aware Biases)

**Files Changed**:
- `src/core/models/strategy.py`
- `src/ai/strategy/recruitment_negotiation.py`
- `src/systems/social/group_system.py`
- `src/ai/strategy/objective_to_goal_mapper.py`
- `src/core/logic/contract_consequence_service.py` [NEW]
- `tests/test_social_contracts.py` [FIXED/EXPANDED]
- `tests/test_party_tactics.py` [NEW]

**Tier:** standard
**Type:** chore
**Priority:** P1
