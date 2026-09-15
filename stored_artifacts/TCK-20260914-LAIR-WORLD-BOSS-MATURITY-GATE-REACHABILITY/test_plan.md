# Test Plan — TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY

## New coverage: `tests/unit/world/test_boss_gate_reachability.py`

7 tests, all passing:

1. `test_difficulty_tier_5_is_defined_and_stronger_than_tier_4` — regression guard for the silent
   tier-1 fallback: tier 5 must exist and be strictly stronger than tier 4 on hp/atk/def/level.
2. `test_spawn_monster_at_tier_5_does_not_fall_back_to_tier_1` — direct proof that
   `EntityGenerator.spawn_monster(difficulty_tier=5)` no longer produces tier-1 stats, with exact
   expected values derived from `DIFFICULTY_TIERS[5]`.
3. `test_ancient_core_is_registered` — `ItemRegistry.get("ancient_core")` returns a real definition,
   not `None`.
4. `test_ancient_core_survives_the_real_inventory_add_path` — direct regression test for the
   original defect: `InventoryService.apply_update()` with an `ancient_core` add-stack must land in
   the resulting inventory, not silently `continue` past it.
5. `test_boss_spawn_gate_reachable_at_lowered_thresholds` — a region meeting the new, lower
   thresholds (`maturity=2.0`, `trauma_score=8.0`) spawns a formidable (strictly-stronger-than-tier-4)
   `world_boss` carrying `ancient_core`.
6. `test_boss_spawn_gate_still_closed_just_below_lowered_thresholds` — the gate is still a real
   gate: `trauma_score` one hundredth below the new threshold spawns nothing. Guards against
   accidentally making the gate a no-op (always-open) rather than genuinely lowered.
7. `test_lair_spawn_gate_reachable_at_lowered_thresholds_and_is_formidable` — same reachability +
   formidability proof as #5, for `check_for_lair_spawn()` (place-scoped `dragonkin`), which shares
   the identical gate constants.

## Existing coverage re-run, confirmed still passing unchanged

- `tests/unit/world/test_difficulty_scaling.py` (15 tests) — tier 1-4 values untouched by this
  ticket; all still pass.
- `tests/unit/world/test_world_dynamics.py` — boss/Lair-spawn idempotency tests use fixtures with
  `maturity=90`/`trauma_score=30.0`, comfortably above both the old (`50.0`/`20.0`) and new
  (`2.0`/`8.0`) thresholds, so behavior is unchanged for those tests.
- `tests/unit/core/test_registry_bridge.py`, `test_registry_parity.py`,
  `test_registry_cross_reference.py`, `test_migration_proof.py`,
  `tests/unit/content/test_runtime_content_mode.py`, `tests/unit/runtime/test_registry_bootstrap_modes.py`
  (33 tests) — confirms the new `ancient_core` catalog entry doesn't break registry
  bridging/parity/cross-reference checks.
- `tests/integration/content/` + `tests/unit/resource/test_inventory_serialization.py` (112 tests)
  — confirms the new catalog entry doesn't break content-catalog validation or inventory
  serialization round-trips.

## End-to-end proof (not a unit test — a real instrumented run, per peer's explicit acceptance bar)

Real, unmodified `frontier_living_world` corpus world, seed=42, real `Kernel.tick_once()` loop
(`PROD_SMALL` profile), 3000 ticks:
- `world_boss` spawned at tick 2101.
- Stats: `hp=325, atk=45, def=17, level=19` — strictly stronger than tier 4
  (`hp=200, atk=30, def=12, level 8-15`), nowhere close to the old tier-1-fallback bug's
  `hp=50, atk=10, def=5, level=3`.
- Inventory at spawn: `[('ancient_core', 1)]`.
- Direct `InventoryService.apply_update()` check on an empty inventory + an `ancient_core` add-stack
  confirmed the item survives the real loot-add path (previously silently dropped).

Same probe against `generated_frontier_3_42` (the one corpus world with a real `LAIR`-kind Place),
5000 ticks: no `dragonkin` ever appeared, because that world's `moon_cave` region (the LAIR's own
region) recorded `0.0` `trauma_score` for the entire run — a separate defect, not this fix's
concern; filed as `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`. The gate itself is proven
reachable and correct (test #7 above, at the unit level, with a region meeting the threshold
directly) — what's unproven end-to-end is only whether any real corpus world's LAIR region actually
accumulates enough trauma in practice, which is a content/routing question outside this ticket.

## Scoped pytest command used

```
pytest tests/unit/world/test_boss_gate_reachability.py tests/unit/world/test_difficulty_scaling.py \
  tests/unit/world/test_world_dynamics.py tests/unit/core/test_registry_bridge.py \
  tests/unit/core/test_registry_parity.py tests/unit/core/test_registry_cross_reference.py \
  tests/unit/core/test_migration_proof.py tests/unit/content/test_runtime_content_mode.py \
  tests/unit/runtime/test_registry_bootstrap_modes.py tests/integration/content/ \
  tests/unit/resource/test_inventory_serialization.py -q
```
