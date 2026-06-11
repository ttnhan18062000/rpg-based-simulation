---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260527-COG-SOCIAL-CONTRACTS
phase: done
date: 2026-05-27
tags: [cog, social, contracts]
---

# TCK-20260527-COG-SOCIAL-CONTRACTS

## Title

Integrate social contracts (Loan and Recruitment) into authoritative pipeline and active strategic projects

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Fully integrate the social contract lifecycle into the simulation loop and strategic projects. When a loan or recruitment contract is accepted, it must create a real project/objective on the entity. Wire the active contracts and offer reapers into Phase 7 of the apply pipeline. Verify with integration tests.

## Scope

- Wire `ContractService.process_active_contracts` and `ContractService.reap_expired_offers` into `src/engine/pipeline.py` (Phase 7).
- Update `ContractService.accept_contract` in `src/systems/social_systems/contracts.py` to spawn corresponding `ProjectState` and `ObjectiveState` when transitioning contracts to active.
- Create an integration test suite `tests/unit/strategic/test_social_contracts.py` verifying:
  - Accepted contract creates active project/objective.
  - Failed contract/betrayal decreases trust/sentiment.
  - Betrayal history reduces future contract acceptance.

## Out of Scope

- Implementing multi-agent bidding wars or complex negotiation loops.

## Acceptance Criteria

- Contracts processed automatically in the apply pipeline.
- Accepted recruitment/loan contracts automatically update entity's `current_project_id` and objectives list.
- All new and existing strategic/social tests pass.

## Related Tickets

- `TCK-20260527-COG-AUTHORITATIVE-PATH` (Done)

## Related Docs

- `entity_cognition_fix_phase0.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/systems/social_systems/contracts.py`
- `src/engine/pipeline.py`
- `tests/unit/strategic/test_social_contracts.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Added `tests/unit/strategic/test_social_contracts.py` verifying active project/objective spawning, trust/sentiment degradation, and betrayal checks.
- verified all 142 strategic unit tests passed.

## Files Changed

- `src/engine/pipeline.py`
- `src/systems/social_systems/contracts.py`
- `tests/unit/strategic/test_social_contracts.py`

## Completion Summary

- Wired `ContractService.process_active_contracts` and `ContractService.reap_expired_offers` into Phase 7 (final integrity & cognitive pass) of the authoritative apply pipeline.
- Refactored `accept_contract` to construct a corresponding `ProjectState` and `ObjectiveState` when a `RECRUITMENT` or `LOAN` contract is accepted.
- verified all strategic unit tests pass cleanly with zero regressions.
