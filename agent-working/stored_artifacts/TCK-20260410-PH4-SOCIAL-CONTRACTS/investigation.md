---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260410-PH4-SOCIAL-CONTRACTS
artifact_type: investigation
tags: [ph4, social, contracts]
---

# Investigation: Phase 4 Social Contracts

## Current State Analysis
- **Strategic Models**: `src/core/models/strategy.py` has a stub for `SocialContractRecord` but it's very basic.
- **Group Records**: `src/core/models/lived_structure.py` has `GroupRecord`, which is used for tactical coordination. It has `shared_goal` and `target_id`.
- **Group System**: `src/systems/social/group_system.py` handles group maintenance, auto-forming cliques.
- **Negotiation/Ally Selection**: No centralized logic exists for ranking candidates or negotiating terms.

## Technical Gaps
1. **Model Depth**: `SocialContractRecord` needs many more fields (purpose, terms, founder, members, role requirements).
2. **Contract Lifecycle**: `StrategicUpdate` needs to support issuance, acceptance, and breach of contracts.
3. **Ally Ranking**: We need a service that factors in trust, debt, reputation, and role fit.
4. **Negotiation**: We need a way to generate and evaluate offers between entities.
5. **Tactical Connection**: The `GroupSystem` needs to be able to "instantiate" a group from a strategic contract.

## Proposed Strategy
- Expand `SocialContractRecord` with a `ContractKind` enum in `enums.py`.
- Add `RecruitmentOfferRecord` to handle the asynchronous negotiation process.
- Implement `SocialCandidateSelectionService` for Task 3.
- Implement `RecruitmentNegotiationService` for Task 4.
- Update `GroupSystem` to support contract-backed parties.
