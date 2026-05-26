# Investigation: Social Contracts Integration

Our investigation of the social system revealed:
1. `SocialContractSystem` and `ContractService` are beautifully defined under `src/systems/social_systems/contracts.py` and `appraisal.py`.
2. However, the simulation loop does not process contracts at all. `process_active_contracts` and `reap_expired_offers` are never called in `src/engine/pipeline.py`.
3. When contracts are accepted (transition to `ACTIVE`), they do not spawn strategic projects or objectives to guide agent behavior.

We will wire contracts into Phase 7 of the apply pipeline and spawn strategic projects on contract acceptance.
