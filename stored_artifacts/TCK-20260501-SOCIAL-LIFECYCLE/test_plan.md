# Test Plan: Phase E4.4 Social Contract Lifecycle

## Unit Tests
- `src/systems/social_contract.py`:
    - `test_contract_state_machine`: Verify all valid/invalid transitions.
    - `test_contract_expiration`: Ensure contracts move to `EXPIRED` after tick limit.

## Integration Tests
- `src/social/appraisal.py`:
    - `test_recruitment_appraisal`: Verify high trust vs low trust outcomes.
    - `test_betrayal_consequences`: Verify trust drops to near-zero after a `BETRAYED` status.

## Lifecycle Tests
- `tests/engine/test_social_lifecycle.py`:
    - **Scenario 1**: Recruitment -> Party Formation -> Shared Goal -> Fulfillment -> Party Dissolution.
    - **Scenario 2**: Recruitment -> Party Formation -> Betrayal during goal -> Relationship Rupture.
    - **Scenario 3**: Multi-party coordination: Leader issues a "retreat" command, members update their strategic detour.
