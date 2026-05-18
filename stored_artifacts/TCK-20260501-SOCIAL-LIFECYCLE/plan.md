# Plan: Phase E4.4 — Complete Social Contract and Party Lifecycle

This phase hardens the social layer by ensuring cooperation is backed by durable, authoritative contracts and that parties act as coordinated units.

## Proposed Changes

### [Component] Social State Models
#### [MODIFY] [social.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/social.py)
- Expand `ContractStatus` enum to include full lifecycle: `OFFERED`, `ACCEPTED`, `ACTIVE`, `FULFILLED`, `FAILED`, `BETRAYED`, `EXPIRED`, `CANCELLED`.
- Add `BetrayalRecord` to track who betrayed whom and when.
- Ensure `SocialComponent` has a clean `contracts` registry.

### [Component] Contract Lifecycle Logic
#### [NEW] [contracts.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_contract.py)
- Implement `SocialContractSystem` to manage transitions.
- Validate state jumps (e.g., `OFFERED` -> `ACCEPTED` is valid, `FAILED` -> `FULFILLED` is invalid).
- Trigger `SocialUpdate` for all changes.

### [Component] Offer Appraisal
#### [MODIFY] [appraisal.py](file:///home/vboxuser/Work/rpg-based-simulation/src/social/appraisal.py)
- Implement `AppraisalSystem.appraise_offer`.
- Factors:
    - **Trust**: Base multiplier for reward value.
    - **Risk**: Penalty based on target danger vs self capability.
    - **Greed**: Modifier on reward expectation.
    - **History**: Check for previous betrayals by the offerer.

### [Component] Party Coordination
#### [MODIFY] [party.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/party.py)
- Bind party membership to active contracts.
- Implement `coordinate_party_objectives`:
    - Leader distributes objectives based on party role (e.g., Tank, DPS, Scout).
    - Members update their `StrategicComponent` with these distributed objectives.

### [Component] Social Consequences
#### [MODIFY] [appraisal.py](file:///home/vboxuser/Work/rpg-based-simulation/src/social/appraisal.py)
- Implement `apply_contract_outcome`:
    - `FULFILLED` -> Trust boost.
    - `FAILED` -> Minor trust penalty.
    - `BETRAYED` -> Massive trust penalty + permanent betrayal record.

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_social_lifecycle.py`
    - Test: Contract state machine validity.
    - Test: Recruitment appraisal with varying trust/greed.
    - Test: Party coordination (moving to shared target).
    - Test: Betrayal consequence propagation.

### Manual Verification
- Inspect entity state via logs to ensure `party_id` is cleared after contract failure.
