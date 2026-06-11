---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260508-ECON-PIPELINE-FIX
artifact_type: investigation
tags: [econ, pipeline, fix]
---

# Investigation - TCK-20260508-ECON-PIPELINE-FIX

## Initial Findings
101 tests failed after Phase E5 hardening.

### Missing Intent Results
`test_transaction_grouping.py` fails because `EntityUpdate.intent_results` is empty. 
`ResourceTransactionSystem.resolve_all` processes the intents but never populates the `intent_results` list.

### Missing World Dynamics
`test_regional_hazard_impact` and others fail with `KeyError: 1` or missing damage.
`WorldDynamicsSystem.resolve_dynamics` was found to be completely omitted from `AuthoritativeApplyPipeline.refine`. This system handles:
- Regional hazards
- Calamity progression
- Node/Chest cooldowns
- Decay of corpses/ground items

### Interaction Reset Logic
`test_interaction_channeling_success` fails because the interaction is not reset to `None`/`reset=True` after a successful harvest. 
The `InteractionSystem` generates the `ResourceTransferIntent` but doesn't set the reset signal.

### API Drift
Some system calls in `pipeline.py` were using outdated names (e.g. `LifecycleSystem.enforce` instead of `resolve_lifecycle`).
