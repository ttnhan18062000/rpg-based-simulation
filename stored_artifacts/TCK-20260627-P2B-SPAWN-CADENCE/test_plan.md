# Test Plan — TCK-20260627-P2B-SPAWN-CADENCE

## Regression Surface (existing tests that must pass)

| Test | File | What it covers |
|---|---|---|
| `test_difficulty_tier_1_baseline` | `tests/unit/world/test_difficulty_scaling.py` | Tier 1 spawn stat scaling |
| `test_difficulty_tier_4_scaling` | `tests/unit/world/test_difficulty_scaling.py` | Tier 4 spawn stat scaling |
| `test_difficulty_tier_determines_level_range` | `tests/unit/world/test_difficulty_scaling.py` | Level range per tier |
| `test_goblin_difficulty_scaling` | `tests/unit/world/test_difficulty_scaling.py` | Goblin stats with tier |
| All tests in `tests/unit/systems/test_spawn_lock_condition.py` | Lock early-release (TCK-P2A) | Must not regress |

## New Tests Required (per AC)

### Unit tests — `tests/unit/world/test_spawn_cadence.py`

| Test | Purpose | AC |
|---|---|---|
| `test_spawn_config_defaults` | `SpawnConfig` defaults: `base_spawn_batch_size=1`, `late_spawn_threshold_tick=500`, `late_spawn_batch_size=2` | Config struct present |
| `test_early_game_spawns_one_per_region` | At tick=100 (below threshold), only 1 entity spawned per below-density region | Two-tier logic correct |
| `test_late_game_spawns_batch_per_region` | At tick=600 (above threshold), up to 2 entities spawned per below-density region | Batch spawn fires |
| `test_batch_capped_by_density_deficit` | If region only needs 1 entity to reach target, batch spawns exactly 1 even in late game | Density cap respected |
| `test_no_spawn_on_non_interval_tick` | At tick=101 (not multiple of 50), returns empty `StateUpdate` | Interval unchanged |
| `test_batch_rng_determinism` | Two calls with same state/tick produce identical entity list | Determinism preserved |

### Scoped Pytest Commands

```bash
# Unit tests only (fast):
pytest tests/unit/world/test_spawn_cadence.py tests/unit/world/test_difficulty_scaling.py tests/unit/systems/test_spawn_lock_condition.py -v

# With slow integration test:
pytest tests/unit/world/test_spawn_cadence.py tests/unit/world/test_difficulty_scaling.py tests/unit/systems/test_spawn_lock_condition.py -v -m "not slow"
```

## Anti-Drift Test Guards

- `test_batch_rng_determinism`: ensures batch spawning uses indexed keys correctly and doesn't alter
  the existing single-spawn RNG path (batch_idx=0 uses same key as before)
- `test_early_game_spawns_one_per_region`: ensures the `base_spawn_batch_size` path is unchanged
  from the pre-fix behavior — regression guard on the non-late-game path
