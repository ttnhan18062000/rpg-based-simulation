# Implementation Plan - Town Test Stabilization

Migrate `tests/town/` to `V2EntityBuilder` to resolve `TypeError` regressions.

## Proposed Changes

### Tests Migration

Migrate all files in `tests/town/`:
- `test_building_sabotage.py`
- `test_economy.py`
- `test_economy_contract.py`
- `test_guild_intel.py`
- `test_guild_pipeline.py`
- `test_home_storage.py`
- `test_recovery_class_hall.py`
- `test_town_building_contract.py`
- `test_town_services.py`

## Verification Plan

### Automated Tests
- `pytest tests/town -vv --tb=short`
