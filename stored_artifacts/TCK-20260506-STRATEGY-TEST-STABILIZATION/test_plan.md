# Test Plan - Strategy Test Stabilization

## Strategy

1. Run all tests in `tests/strategy/` to confirm baseline failures.
2. For each test file:
    - Replace `EntityState(...)` with `V2EntityBuilder(id).kind(kind).at(pos)...build()`.
    - Run the specific test file to verify the fix.
3. Final pass: Run all tests in `tests/strategy/`.

## Tests

- [ ] `test_cognition_capacity.py`
- [ ] `test_leads.py`
- [ ] `test_project_continuity.py`
- [ ] `test_strategic_memory_v2.py`
- [ ] `test_strategic_reprioritization.py`
