---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-DETERMINISM-TEST
artifact_type: test_plan
tags: [world, determinism, testing]
---

# Test Plan — TCK-20260821-NOISE-FILL-DETERMINISM-TEST

## Regression Surface

Existing tests that must keep passing (no behavior change expected — this ticket is test-only):

**Unit — `tests/unit/worldbuilding/test_world_compiler.py`** (all 43 tests in the file, but the ones directly load-bearing for this ticket's area):
- `test_compiler_terrain_variants_declared_produces_per_tile_variation`
- `test_compiler_terrain_variants_deterministic_same_seed` — **will be extended by this ticket** (see New Tests Required)
- `test_compiler_terrain_variants_different_seed_differs`
- `test_compiler_terrain_variants_never_writes_outside_bounds`
- `test_compiler_terrain_variants_town_tiles_membership_unaffected_by_terrain_choice`
- `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`
- `test_compiler_terrain_variants_reuses_weighted_choice_respects_weight`
- `test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration`
- `test_compiler_terrain_variants_empty_list_behaves_as_not_declared`
- `test_compiler_terrain_variants_tile_offset_injective_across_wide_regions`
- `test_compiler_minimal_world` (asserts `isinstance(report["state_hash"], str)`)

**Certification — `tests/certification/test_world_compile_determinism.py`**:
- `test_compiler_seeding_determinism` — the pattern this ticket mirrors; must remain unmodified and passing.
- `test_compiler_layout_variation_under_different_seeds`
- `test_compile_report_contents`

## New Tests Required

Only one net-new assertion is required, per AC #4. Recommended approach: **extend the existing `test_compiler_terrain_variants_deterministic_same_seed` test** rather than add a new standalone test, because:
1. AC #4's own wording — "reuses ... as ONE signal, IN ADDITION TO the tile-level dict comparison" — describes a single test carrying both signals, not two separate tests.
2. `test_compiler_terrain_variants_deterministic_same_seed` already performs the two same-seed `compile()` calls AC #4 needs; adding a `report1`/`report2` capture and one assertion line is a minimal, non-duplicative change.
3. Splitting it into a second standalone test would duplicate the same two `compile()` calls and spec setup for no behavioral gain, which cuts against this file's existing pattern of one assertion-focus per test only where the setup actually differs (contrast: `..._different_seed_differs` is a separate test because its *setup* differs — two seeds, not one).

- **Test name**: `test_compiler_terrain_variants_deterministic_same_seed` (extended in place, not renamed — the behavior it verifies is unchanged, only the assertion coverage grows)
- **Category**: unit
- **What it verifies**: same-seed compiles of a variant-declaring spec produce (a) `report1["state_hash"] == report2["state_hash"]` (mirroring `test_compiler_seeding_determinism`'s pattern) as one signal, and (b) bit-identical per-tile `state.terrain` dicts over the region's bounds as the primary, more precise signal — since (a) alone is insufficient (`StateFingerprinter` never reads `state.terrain`, per Investigation).
- **Where it lives**: `tests/unit/worldbuilding/test_world_compiler.py`, replacing lines 716-731.

Concrete diff shape (for the implementer, not to be treated as pre-approved code — Plan phase owns the exact diff):
```python
def test_compiler_terrain_variants_deterministic_same_seed():
    """Compiling the same terrain_variants-declaring spec twice with the same seed produces
    an identical per-tile terrain dict within the region's bounds, and an identical
    report["state_hash"] as one additional signal (mirroring test_compiler_seeding_determinism)."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)

    state1, report1 = WorldCompiler.compile(spec, seed=42)
    state2, report2 = WorldCompiler.compile(spec, seed=42)

    assert report1["state_hash"] == report2["state_hash"]

    region_tiles_1 = {(x, y): state1.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    region_tiles_2 = {(x, y): state2.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    assert region_tiles_1 == region_tiles_2
```

No other new test is required. ACs #1-#3 are fully covered by existing tests (see Investigation) and must not be re-implemented.

## Scoped Pytest Commands

```bash
PYTHONPATH=. pytest tests/unit/worldbuilding/test_world_compiler.py tests/certification/test_world_compile_determinism.py -v
```

Never `pytest tests/`. This is the correct scope: both files this ticket's Related Code Areas name as test targets, covering the full regression surface for `WorldCompiler.compile()` determinism and terrain-fill behavior.

## Anti-Drift Test Guards

- `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` (already exists) guards against a future change accidentally coupling `report["state_hash"]` equality with terrain-content correctness — its docstring explicitly documents that `state_hash` cannot detect a terrain-painting regression. Do not remove or weaken this test as "redundant" with the new state_hash assertion; they check different things by design.
- `test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration` (already exists) guards against the new noise-fill draw (`Domain.INIT`) perturbing `Domain.WORLD`'s existing entity/resource/building draw sequence. This is the test that would catch scope creep if a future change moved noise-fill draws into `Domain.WORLD` or changed draw ordering.
- `test_compiler_terrain_variants_tile_offset_injective_across_wide_regions` (already exists) guards against regression to the collision-prone `(x << 8) | y` tile-offset encoding; keep it passing as a precondition for this ticket's determinism claim to mean anything (a colliding encoding could still produce a same-seed-identical hash by coincidence while masking a real per-tile collision bug).
- The extended `test_compiler_terrain_variants_deterministic_same_seed` itself, once `report1`/`report2` are captured, doubles as a guard against any future change to `StateFingerprinter.get_fingerprint()` that would make `state_hash` sensitive to per-tile terrain content while keeping the two same-seed dicts still equal only by coincidence — an unlikely failure mode, but the assertion order (state_hash first, then dict) means a state_hash mismatch surfaces before the more expensive dict comparison, which is a minor efficiency win worth preserving in the diff shape above.
