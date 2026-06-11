---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260408-PH1-2-DS-REMEDIATION
artifact_type: test_plan
tags: [ph1, ds, remediation]
---

# Test Plan for TCK-20260408-PH1-2-DS-REMEDIATION

## Existing Tests to Run
- `tests/behavioral/test_ai_divergence.py` (if it exists)
- `tests/behavioral/test_social_bonds.py`
- `tests/engine/test_action_system.py`

## New Tests to Add
- `tests/remediation/test_reputation_unification.py`:
    - Verify `IdentityAspect.reputation` is the only source updated.
    - Verify `Entity.reputation` (if it still exists as a property) mirrors `IdentityAspect.reputation`.
- `tests/remediation/test_inspection_serialization.py`:
    - Verify `entity_memory` in schema now contains full objects.
    - Verify `AIPresenter` doesn't crash on distance calculation with beliefs.
- `tests/remediation/test_authoritative_gossip.py`:
    - Setup two entities.
    - Perform an action that triggers gossip.
    - Verify the "listener" entity receives the update in the SAME tick application pass.
- `tests/remediation/test_archetype_diversity.py`:
    - Spawn 100 entities.
    - Verify distribution of archetypes is not 100% BALANCED.

## Regressions to Watch
- Broken binary serialization (though we are fixing it, we must ensure it doesn't break other things).
- Entity builder crashes if archetype is missing.
