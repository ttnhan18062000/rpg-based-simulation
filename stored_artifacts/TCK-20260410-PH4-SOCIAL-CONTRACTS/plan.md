# Implementation Plan - Phase 4 Social Contracts

Phase 4 implements "Social Contracts, Party Formation, and Cooperative Coordination". The goal is to evolve the AI's social behavior from simplistic clustering to negotiated, contract-backed parties with role-based coordination and long-term social consequences.

## User Review Required

> [!IMPORTANT]
> This phase introduces "Contractual" cooperation. This means entities will no longer just "hang out" in same-faction groups; they will explicitly recruit each other for specific purposes (expeditions, defense, etc.).

> [!WARNING]
> Breaking a contract will now have durable social costs (resentment, reputation loss), which may make some characters harder to recruit in the future.

## Proposed Changes

### Core Models

#### [MODIFY] [enums.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/enums.py)
- Add `ContractKind`: `EXPEDITION`, `ESCORT`, `MILITIA`, `MERCENARY`, `REVENGE_PACT`.
- Add `OfferStatus`: `PENDING`, `ACCEPTED`, `DECLINED`, `EXPIRED`.

#### [MODIFY] [strategy.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/strategy.py)
- Expand `SocialContractRecord` with purpose, founder, member roles, and term metadata.
- [NEW] Add `RecruitmentOfferRecord` to track pending negotiations.
- [NEW] Add `ContractTermRecord` and `ContractOutcomeRecord`.

### Strategic Services

#### [NEW] `src/ai/strategy/social_candidate_selection.py`
- Service to rank potential allies based on trust, debt, reputation, and role capability.

#### [NEW] `src/ai/strategy/recruitment_negotiation.py`
- Service to handle the logic of making and evaluating offers (balancing risk vs. reward vs. relationship).

### Systems Integration

#### [MODIFY] `src/actions/base.py`
- Update `StrategicUpdate` to handle contract and offer lifecycle.

#### [MODIFY] `src/systems/social/group_system.py`
- Update to support contract-backed party formation.

## Open Questions

> [!CAUTION]
> **Contract Sovereignty**: If an entity is in two contracts that conflict (e.g., two different expeditions), how should it prioritize?
> *Proposed*: Use the strategic appraisal's project priority scoring. Higher priority contract wins, and the other is effectively breached or suspended (with social costs).

## Verification Plan

### Automated Tests
- `tests/ai/test_social_candidate_selection.py`: Verify ally ranking logic.
- `tests/ai/test_recruitment_negotiation.py`: Verify offer evaluation and contract creation.
- `tests/systems/test_contract_group_integration.py`: Verify tactical group instantiation from contracts.

### Manual Verification
- Use `EntityInspector` to verify contract terms and active party members.
