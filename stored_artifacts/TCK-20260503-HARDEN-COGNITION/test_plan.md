---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260503-HARDEN-COGNITION
artifact_type: test_plan
tags: [harden, cognition]
---

# Test Plan: Strategic Cognition Hardening

## Regression Testing
- `pytest tests/engine/test_strategic_hardening.py`: Ensures existing capacity and frequency logic remains intact.

## New Test Cases
- `tests/engine/test_status_hardening.py`:
    - `test_frozen_actor_skips_concerns`: Verify that an entity with `status_frozen=True` does not have its concerns evaluated.
    - `test_stunned_actor_skips_intent`: Verify that an entity with `status_stunned=True` does not evaluate strategic intent.
    - `test_staggered_frequency_distribution`: Verify that entities with different IDs process at different ticks (0-9) but each only every 10 ticks.

## Validation
- `graphify update .`: Keep the knowledge graph current.
- `python3 tools/ledger_validator.py`: Final certification.
