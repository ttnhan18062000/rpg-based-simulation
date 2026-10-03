---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION
artifact_type: test_plan
tags: [determinism]
---

# Test Plan — TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION

## New tests
- `tests/unit/core/test_calendar.py` — confirms `TICKS_PER_FANTASY_YEAR == 288000` and
  `fantasy_years_to_ticks()`'s arithmetic, locking in the named constant as the single source of
  truth.

## Updated tests (boundary-value assertions migrated to the new numbers)
- `tests/unit/progression/test_lifecycle.py`
- `tests/unit/world/test_demographics.py`
- `tests/unit/strategic/test_coming_of_age_archetype_choice.py`
- `tests/unit/strategic/test_life_stage_transitions.py`

## Regression scope
`pytest tests/unit/core/ tests/unit/progression/ tests/unit/world/test_demographics.py tests/unit/strategic/ tests/unit/domains/optimization/ tests/integration/optimization/ -m "not slow"`

## Result
All tests pass. `test_calendar.py` (3 new tests), the 4 updated existing test files, and 2
additional files found only during implementation (`tests/unit/world/test_natural_creature_reproduction.py`
had its own independent copy of the same stale `3000`-tick literal; `src/systems/world_systems/
generator.py`'s `spawn_natural_creature_offspring()` was a real production consumer the original
ticket scope missed). Full regression sweep:
`pytest tests/unit/core/ tests/unit/progression/ tests/unit/world/ tests/unit/strategic/ tests/unit/domains/optimization/ tests/integration/optimization/ -m "not slow"`
→ 1087 passed, 2 deselected, 0 failed. `pytest tests/unit/engine/ tests/unit/kernel/ tests/certification/ -m "not slow"`
→ 315 passed, 2 skipped (pre-existing, unrelated), 0 failed.
