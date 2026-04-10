# Test Plan: Phase 4 Social Contracts

## Candidate Selection
- **Test**: `tests/ai/test_social_candidate_selection.py`
- **Focus**:
  - Higher trust produces higher candidate ranking.
  - Owed debts (from social bonds) provide recruitment leverage.
  - High public cowardice reduces recruitment viability for RAID/ESCORT contracts.
  - Role-mismatch penalizes candidates (e.g. inviting a crafter to a hunt).

## Negotiation & Offers
- **Test**: `tests/ai/test_recruitment_negotiation.py`
- **Focus**:
  - Recruiter issues `RecruitmentOfferRecord` via `StrategicUpdate`.
  - Candidate evaluates offer using `RecruitmentNegotiationService`.
  - Acceptance creates `SocialContractRecord` and clears the offer.
  - Refusal records social cost or simple "not interested" based on trust.

## Contract-Backed Groups
- **Test**: `tests/systems/test_contract_group_integration.py`
- **Focus**:
  - `GroupSystem` detects a new active contract.
  - Instantiates a `GroupRecord` with matching members and `shared_goal`.
  - Verify that members follow the party leader and protect contract-specified targets.

## Consequences & Memory
- **Test**: `tests/core/test_contract_consequences.py`
- **Focus**:
  - Resolving a contract (DONE) increases trust and reputation.
  - Abandoning a contract (BREACH) increases resentment and public greed/cowardice scores.
  - Verify that breached contracts are remembered and affect future recruitment offers.

## Regression
- **Test**: `pytest tests/social/test_gossip.py` (Verify leads/rumors still propagate).
- **Test**: `pytest tests/ai/test_strategic_uncertainty.py`.
