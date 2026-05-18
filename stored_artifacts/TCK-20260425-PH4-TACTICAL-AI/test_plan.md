# Test Plan: Tactical Roles and Capacity

## Automated Tests
- `pytest tests/parity/test_tactical_roles.py`
    - `test_vanguard_closes_distance`: Verifies closing logic.
    - `test_skirmisher_kites`: Verifies kiting logic.
    - `test_strategic_capacity_limits`: Verifies max projects enforcement.

## Verification
- All tests must pass with `v2_contract` marker.
