---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH4-TACTICAL-AI
artifact_type: test_plan
tags: [ph4, tactical, ai]
---

# Test Plan: Tactical Roles and Capacity

## Automated Tests
- `pytest tests/parity/test_tactical_roles.py`
    - `test_vanguard_closes_distance`: Verifies closing logic.
    - `test_skirmisher_kites`: Verifies kiting logic.
    - `test_strategic_capacity_limits`: Verifies max projects enforcement.

## Verification
- All tests must pass with `v2_contract` marker.
