# Phase 10 Test Plan

## Automated Tests
- `tests/engine/test_phase10_replay.py`:
    - Simulate rejected harvest.
    - Assert `EntityState.latest_intent_results` contains the failure.
    - Assert `AuthoritativeState.global_resources` reflects the item delta on success.
    - Assert bit-identical replay parity.
