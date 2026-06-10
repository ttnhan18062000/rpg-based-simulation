# Test Plan — TCK-20260610-ENUM-REWARD-INFLUENCE

## Regression Surface
- `tests/unit/world/test_influence.py` — all 2 tests must pass
- `tests/unit/world/test_world_dynamics.py` — all tests must pass

## New Tests Required

In `tests/unit/world/test_influence.py`:
1. `test_clean_catalog_entity_hero_triggers_influence_shift` — entity with `faction_id="hero_guild"` in properties → is_protector() path → -5.0 delta
2. `test_clean_catalog_entity_monster_triggers_influence_shift` — entity with `faction_id="goblin_warband"` (invader bucket) → is_invader() path → +5.0 delta
3. `test_mixed_legacy_and_clean_entities_coexist` — one legacy enum hero + one clean catalog monster → both trigger correct deltas

## Scoped Pytest Commands

```
pytest tests/unit/world/test_influence.py tests/unit/world/test_world_dynamics.py -v
```

## Anti-Drift Test Guards
- Conquest threshold remains -50.0 (CONQUEST_THRESHOLD)
- Liberation threshold remains 50.0 (LIBERATION_THRESHOLD)
- `owner_faction_id_set` value for conquest remains `Faction.MONSTER_HORDE` (int)
- Liberation sentinel `-1` unchanged
