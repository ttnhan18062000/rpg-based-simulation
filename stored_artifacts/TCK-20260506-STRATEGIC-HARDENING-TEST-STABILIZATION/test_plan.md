# Test Plan - Strategic Hardening Test Stabilization

## Strategy

1. Run all tests in `tests/strategic/` to confirm baseline failures.
2. For each test file:
    - Replace `EntityState(...)` with `V2EntityBuilder(id).kind(kind).at(pos)...build()`.
    - Run the specific test file to verify the fix.
3. Final pass: Run all tests in `tests/strategic/`.

## Tests

- [ ] `test_biological_needs.py`
- [ ] `test_detour_suggestion.py`
- [ ] `test_event_interpretation.py`
- [ ] `test_interruption_resistance.py`
- [ ] `test_role_biasing.py`
