---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION
artifact_type: test_plan
tags: [observability, engine, simulation-quality, progression]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION

## Regression Surface

- `tests/unit/observability/` (full directory), `tests/unit/kernel/`, `tests/integration/kernel/`.

## New Tests Required

`tests/unit/observability/test_event_shapers_progression.py` (new, 18 tests): direct field-read
events (10: fire + non-fire for xp_granted/level_up/skill_unlocked/trait_expressed/
pillar_trait_unlocked/progression_conversion_applied, plus no-identity-update and
no-prior-entity edge cases), plateau detection (7: any-update-gating regression test, threshold
boundary, dedup, skill_silence fire + non-fire, tracking reset), registry membership (1).

## Scoped Pytest Commands

```
pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q
```

## Anti-Drift Test Guards

- `_reset_shaper_state` autouse fixture, same pattern as `StrategyShaper`'s test file.
- `test_plateau_xp_rate_zero_fires_without_identity_update` directly regression-guards the
  any-update-vs-identity-update gating bug found and fixed this ticket — passing `identity=None`
  on the entity update deliberately, matching the real kernel run that first exposed the bug.
- Fixed a cross-shaper test-isolation issue found while writing this ticket's own registry test:
  `test_event_shapers_strategy.py`'s mock entity updates needed `.identity = None` added once
  `ProgressionShaper` joined the same registry — flagged for children 4-5 to watch for the same
  pattern with their own new fields.

## Results (this session)

- `pytest tests/unit/observability/test_event_shapers_progression.py -q`: 18 passed.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  986 passed, 6 skipped, 3 deselected (was 968/6/3 after Child 2 — +18 matches exactly).
- Real kernel run (`dungeon_crawl_seed42_500t`): `ON` mode shows `event_extractor=32,
  event_shapers=32` for `progression_plateau_detected` — exact parity, confirming the fix.
  `SHADOW` mode confirmed 0 delivered.
