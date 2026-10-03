# Plan — TCK-20260627-P2B-SPAWN-CADENCE

## Ordered Steps

### Step 1 — Add `SpawnConfig` dataclass to `src/world/spawn_config.py`
**File:** `src/world/spawn_config.py`
**Change:** Add a frozen dataclass `SpawnConfig` with three fields:
- `base_spawn_batch_size: int = 1` — entities to spawn per region per interval (early game)
- `late_spawn_threshold_tick: int = 500` — tick at which late-game cadence kicks in
- `late_spawn_batch_size: int = 2` — entities to spawn per region per interval (late game)

Add `DEFAULT_SPAWN_CONFIG = SpawnConfig()` instance for use as default.

Add an explanatory comment above the dataclass documenting the two-tier rationale.

**Scope guard:** Do NOT modify `BASE_MONSTER_DENSITY`, `SPAWN_POOLS`, `DIFFICULTY_ZONES`, or `DIFFICULTY_TIERS`. Only add the new struct.

**Depends on:** nothing

---

### Step 2 — Update `SpawnService.process_spawns()` in `src/world/spawn.py`
**File:** `src/world/spawn.py`
**Change:**
1. Add import of `SpawnConfig, DEFAULT_SPAWN_CONFIG` from `src.world.spawn_config`
2. Add `spawn_config: SpawnConfig = DEFAULT_SPAWN_CONFIG` parameter to `process_spawns()`
3. After the tick-interval guard, determine `batch_size`:
   ```python
   batch_size = (
       spawn_config.late_spawn_batch_size
       if state.tick >= spawn_config.late_spawn_threshold_tick
       else spawn_config.base_spawn_batch_size
   )
   ```
4. Inside the per-region loop, replace the single-entity spawn with a batch loop:
   - Compute `deficit = target_count - current_count` (how many below target)
   - Loop `for batch_idx in range(min(batch_size, deficit))`
   - For `batch_idx == 0`: use original RNG keys (`r_id`, `f"x_{r_id}"`, `f"y_{r_id}"`) — **preserves existing determinism**
   - For `batch_idx > 0`: use suffixed keys (`f"{r_id}_b{batch_idx}"`, etc.) — new late-game draws
   - Append each spawned entity to `entities_add`

**Scope guard:** Do NOT change `SPAWN_INTERVAL`. Do NOT change density formula. Do NOT alter the `generator._last_id` update logic (it is already set to `generator._last_id + 1` per entity via the generator methods).

**Depends on:** Step 1

---

### Step 3 — Add unit tests in `tests/unit/world/test_spawn_cadence.py`
**File:** `tests/unit/world/test_spawn_cadence.py` (new file)
**Tests:**
- `test_spawn_config_defaults` — verify `SpawnConfig()` field values
- `test_early_game_spawns_one_per_region` — mock state at tick=100, one region below density, assert 1 entity in `StateUpdate.entities_add`
- `test_late_game_spawns_batch_per_region` — mock state at tick=600, one region below density by 2+, assert 2 entities in `StateUpdate.entities_add`
- `test_batch_capped_by_density_deficit` — tick=600, region only 1 below target, assert 1 entity (not 2)
- `test_no_spawn_on_non_interval_tick` — tick=601 (not multiple of 50), assert empty StateUpdate
- `test_batch_rng_determinism` — call process_spawns() twice with same state, assert entity lists match

**Depends on:** Step 2

---

### Step 4 — Add parity ledger entry in `docs/parity_ledger/world_dynamics.yaml`
**File:** `docs/parity_ledger/world_dynamics.yaml`
**Change:** Append entry WORLD-103 documenting the two-tier spawn cadence behavior.

**Depends on:** Step 2

---

## Dependency Map
```
Step 1 (SpawnConfig struct) → Step 2 (process_spawns update) → Step 3 (unit tests)
                                                              → Step 4 (parity entry)
```

## Explicit Scope Guards (what NOT to touch)
- `SPAWN_INTERVAL = 50` — leave untouched; only batch size changes
- `BASE_MONSTER_DENSITY`, `SPAWN_POOLS`, `DIFFICULTY_ZONES`, `DIFFICULTY_TIERS` — untouched
- `tests/unit/world/test_difficulty_scaling.py` — do not modify
- `tests/unit/systems/test_spawn_lock_condition.py` — do not modify
- `src/worldassembly/entity_spawner.py` — not involved in runtime spawn cadence
- No combat lethality changes

## Acceptance Criteria → Steps Mapping
| AC | Steps |
|---|---|
| `alive_avg >= 12.0` throughout 1,000-tick run seeds 42+137 | Step 2 (increased late-game spawn rate) |
| Spawn cadence change documented with two-tier comment | Steps 1+2 (comment in SpawnConfig, code comments) |
| Regression: existing spawn tests pass | Step 3 guards against regressions |

## Deviations
_(none — fill in if implementation diverges from plan)_
