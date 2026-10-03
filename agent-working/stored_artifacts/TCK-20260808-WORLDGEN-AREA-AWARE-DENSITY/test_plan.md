---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY
artifact_type: test_plan
tags: [world]
---

# Test Plan — TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY

Extends `tests/unit/worldgeneration/test_generator.py`.

1. `test_population_matches_flat_formula_at_default_reference_point` — `target_world_size=
   (100,100)`, `population_scale=1.0`, `danger_level=1.0` (all defaults): assert citizen count
   == 15, monster count == 8 — the new formula must be byte-identical to the old flat formula at
   the reference point (backward-compat by construction, not by accident).
2. `test_population_scales_with_target_world_size` — same `population_scale`/`danger_level`,
   `target_world_size=(300,300)` vs `(100,100)`: assert citizen AND monster counts strictly
   increase with world size — `target_world_size` is no longer a dead field.
3. `test_monster_population_scales_with_danger_level` — same `target_world_size`/
   `population_scale`, `danger_level=3.0` vs `1.0`: assert monster count strictly increases,
   citizen count UNCHANGED (town hazard is always 0, no dependency).
4. `test_faction_fallback_survives_catalog_with_no_defender_or_invader_factions` — construct a
   minimal in-memory catalog stub with real factions but none flagged `defender`/`invader`;
   assert `.generate()` still produces a valid `WorldSpec` (no dangling faction reference) — the
   real robustness fix, not the corrected-away original bug.
5. `test_no_reasonable_parameter_combination_breaches_high_entity_density_warning` — sweep
   `target_world_size` (50×50 to 400×400), `population_scale` (0.5-5.0), `danger_level` (0.5-3.0);
   assert `total_pop <= map_area * 0.5` for every combination (`HighEntityDensityWarningRule`'s
   own real threshold, computed fresh, not hardcoded).
6. Existing 4 tests in `test_generator.py` must still pass unmodified (regression guard for the
   reference-point backward-compat claim).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms the exact faction-reference bug location and real region.area/hazard semantics | Done — bug location confirmed as investigation-methodology error, not a real default-path bug; real latent gap in constructor-injected usage confirmed and will be hardened |
| generate() produces a valid WorldSpec for a real, non-trivial scale/size combination | Already true (verified in Investigate); test 2/3/5 extend the coverage |
| Population formula factors in target_world_size's own area | Test 1, 2 |
| Confirmed generation-time density stays under WORLD-WARN-002's threshold | Test 5 |
| Scoped pytest passes | Tests 1-6 |
