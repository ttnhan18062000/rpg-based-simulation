# Stabilizing Social Contract Expiration

The test `test_contract_expiration_resolves_and_dissolves` fails because `ACTIVE` social contracts that reach their `expiry_tick` are not being transitioned to terminal states (like `FULFILLED`/`COMPLETED`). While `ContractService.process_active_contracts` exists in `src/social/contracts.py` to handle this, it is not integrated into the `AuthoritativeApplyPipeline`.

## Proposed Changes

### Authoritative Engine Pipeline

#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Update `_resolve_contract_expirations` to also call `ContractService.process_active_contracts`.
- Ensure all social updates (heroism, notoriety) from the service are correctly merged into the pipeline's `StateUpdate`.
- Consolidate imports to avoid circular dependencies.

### Social Contract Service

#### [MODIFY] [contracts.py](file:///home/vboxuser/Work/rpg-based-simulation/src/social/contracts.py)
- Refine `process_active_contracts` to use more robust merging if needed (though it looks mostly correct).
- Ensure it aligns with the `SocialContractSystem`'s transition logic.

## Verification Plan

### Automated Tests
- `pytest tests/rpg/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves -v -s`
- `pytest tests/quests/test_quest_lifecycle.py` (to ensure no regressions in quest rewards which often interact with contracts)

### Manual Verification
- Trace the heroism/notoriety updates in logs to ensure they are being applied exactly once per expiration.
