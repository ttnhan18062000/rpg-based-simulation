# Test Plan - Town Test Stabilization

## Strategy

1. Run all tests in `tests/town/` to confirm baseline failures.
2. For each test file:
    - Replace `EntityState(...)` with `V2EntityBuilder(id).kind(kind).at(pos)...build()`.
    - Run the specific test file to verify the fix.
3. Final pass: Run all tests in `tests/town/`.

## Tests

- [ ] `test_building_sabotage.py`
- [ ] `test_economy.py`
- [ ] `test_economy_contract.py`
- [ ] `test_guild_intel.py`
- [ ] `test_guild_pipeline.py`
- [ ] `test_home_storage.py`
- [ ] `test_recovery_class_hall.py`
- [ ] `test_town_building_contract.py`
- [ ] `test_town_services.py`
