# TCK-20260510-SOCIAL-EXPIRATION

## Title
Stabilizing Social Contract Expiration

## Status
DONE

## Request Summary
Resolve the regression in `test_contract_expiration_resolves_and_dissolves` where `ACTIVE` contracts were not expiring correctly in the authoritative pipeline.

## Scope
- Integrate `ContractService.process_active_contracts` into `AuthoritativeApplyPipeline`.
- Hardened `ContractService` merging logic to use `StrategicUpdate.merge` and `SocialUpdate.merge`.
- Ensure group dissolution correctly triggers when contracts expire.

## Out of Scope
- Major refactoring of the social contract system.
- Implementation of new contract types.

## Acceptance Criteria
- `test_contract_expiration_resolves_and_dissolves` passes.
- All quest lifecycle tests pass.
- Contract terminal states (`FULFILLED`, `FAILED`) correctly propagate social consequences.

## Related Tickets
- None

## Related Docs
- None

## Related Stored Artifacts
- `stored_artifacts/TCK-20260510-SOCIAL-EXPIRATION/plan.md`

## Related Code Areas
- `src/engine/pipeline.py`
- `src/social/contracts.py`
- `src/systems/social_contract.py`

## Assumptions / Open Questions
- None

## Implementation Notes
- Identified that `SocialContractSystem.check_expirations` was only handling non-active contracts.
- Integrated `ContractService` as the service layer to handle the more complex outcome resolution of active contracts.

## Test Summary
- `pytest tests/rpg/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves` (PASSED)
- `pytest tests/quests/test_quest_lifecycle.py` (PASSED)

## Files Changed
- `src/engine/pipeline.py`
- `src/social/contracts.py`

## Completion Summary
Successfully integrated active contract expiration into the authoritative pipeline. This ensures that recruitment, loans, and other long-term social contracts are correctly resolved when they reach their expiry tick, triggering appropriate social bond updates and group dissolutions.
