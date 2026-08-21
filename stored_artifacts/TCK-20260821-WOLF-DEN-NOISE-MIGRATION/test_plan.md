---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-WOLF-DEN-NOISE-MIGRATION
artifact_type: test_plan
tags: [world, content, determinism]
---

# Test Plan — TCK-20260821-WOLF-DEN-NOISE-MIGRATION

## Regression Surface

### Unit
- `tests/unit/worldbuilding/test_world_compiler.py` — the 10 tests added by
  `TCK-20260821-COMPILER-NOISE-FILL` plus all pre-existing tests in this file (compiler mechanism
  itself is untouched by this ticket, but any real-content-triggered regression in the
  weighted-sampling path would most likely also break one of these synthetic-fixture tests first).
- `tests/unit/worldbuilding/test_worldspec_schema.py` — `allow_overlapping_regions` default-`False`
  assertion (`test_worldspec_schema.py:51`) must keep passing unmodified; this ticket does not touch
  `ValidationSpec` or set `allow_overlapping_regions: true` anywhere.

### Integration
- `tests/integration/worldassembly/test_real_content_world_modules.py` — all of:
  `test_real_world_modules_load_from_data_content`, `test_real_world_modules_normalize`,
  `test_real_world_modules_preserve_count_maps`, `test_real_world_modules_resolve_contributions`,
  `test_hazard_kind_survives_module_pipeline`, `test_terrain_variants_survive_module_pipeline`,
  `test_real_world_modules_reference_graph_edges_exist`. All iterate `MODULE_MATRIX`, which includes
  `wolf_den_near_forest`/`frontier_village_core`; per investigation.md's per-test trace, none inspect
  `terrain`/`terrain_variants` string content for this module — they must all pass **unmodified**
  (this is AC #4 verbatim).
- `tests/integration/content/test_strict_world_matrix.py` — `_MATRIX` includes 7 compositions
  containing `wolf_den_near_forest`; asserts no blocking assembly errors.
- `tests/integration/content/test_resource_region_coverage_corpus.py` — `wolf_den` is in
  `_ACCEPTED_ZERO_CONTENT_REGIONS`; resource-coverage exemption, terrain-unrelated, must stay green.
- `tests/integration/content/test_swamp_border_pack.py` — `wolf_den_near_forest` +
  `sunken_swamp_border` coexistence assembly tests.

### Certification / Determinism
- `tests/certification/test_world_compile_determinism.py` — general compile-determinism
  self-consistency tests (same-seed → identical hash, different-seed → different hash). This
  ticket's change is confined to `state.terrain` content, which `StateFingerprinter` does not hash
  (confirmed by `TCK-20260821-COMPILER-NOISE-FILL`'s investigation) — these tests are expected to
  keep passing, but per that same investigation, passing them is **not sufficient** proof of correct
  terrain content; new tests below cover that directly.

## New Tests Required

1. **`test_wolf_den_near_forest_declares_terrain_variants`**
   - Category: unit (content/schema-level)
   - Verifies: loading `wolf_den_near_forest.yaml` via `WorldModuleRepository` produces a spec whose
     `near_forest` and `wolf_den` regions both have a non-empty `terrain_variants` list, and that the
     module's `terrain` (flat/primary) field is still exactly `"forest"` for both regions, and
     `hazard_level`/`hazard_kind`/`tags`/`type` are unchanged from their pre-migration values
     (`1.0`/`2.0`, `"NATURAL_TERRAIN"`, `["forest"]`, `"wilderness"`).
   - Where: `tests/integration/worldassembly/test_real_content_world_modules.py` (new function, near
     `test_hazard_kind_survives_module_pipeline`/`test_terrain_variants_survive_module_pipeline`,
     following the same `repos` fixture + direct module-load pattern — this is real-content-specific,
     so it belongs beside those two, not in the synthetic-fixture `test_world_compiler.py`).

2. **`test_wolf_den_near_forest_compiles_with_per_tile_terrain_variation`**
   - Category: integration
   - Verifies AC #2: compiling a world composition containing `wolf_den_near_forest` (reuse or build
     a minimal `WorldSpec`/composition fixture including at least `frontier_village_core` +
     `wolf_den_near_forest`, with a topology large enough to contain both regions' bounds, e.g.
     width/height ≥ 106) with a fixed seed produces at least one tile inside `near_forest`'s bounds
     (`x:[45,90], y:[10,55]`) and at least one tile inside `wolf_den`'s bounds (`x:[70,105],
     y:[30,70]`) whose `state.terrain[(x,y)]` differs from `"forest"`. Also asserts tiles strictly
     outside both regions' bounds (e.g. `(0,0)`, or any tile in `frontier_village_core`'s `hometown`
     bounds `x:[10,40],y:[10,40]`) are unaffected — still `"PLAIN"` (base fill) or `"plain"`
     (hometown's own flat terrain), never the wolf-den secondary value.
   - Where: `tests/integration/worldassembly/test_real_content_world_modules.py` or a new
     `tests/integration/worldassembly/test_wolf_den_noise_migration.py` if the fixture setup (full
     resolve→compile, not just normalize→resolve) doesn't fit the existing file's `repos` fixture
     shape — Plan should decide based on whether a real `WorldSpec` needs to be resolved via
     `WorldAssemblyResolver.assemble()` + `WorldCompiler.compile()`, which the existing file's other
     tests do not currently do (they stop at `resolve_module_contribution()`).

3. **`test_wolf_den_overlap_box_resolves_to_wolf_den_terrain`**
   - Category: integration (the direct proof of Decision 3's documented resolution)
   - Verifies: after compiling, every tile in the overlap box `x:[70,90], y:[30,55]` was painted
     using `wolf_den`'s `terrain_variants` (not `near_forest`'s) — concretely, assert that at least
     one overlap-box tile's terrain matches a value only `wolf_den`'s variant list could produce (if
     `near_forest` and `wolf_den` use the same variant set/weights this can't be distinguished by
     value alone; recommend giving each region a distinguishable weight or, more robustly, recompute
     the expected `entity_id`/`weighted_choice` result for a sampled overlap tile using `wolf_den`'s
     `region_hash` and assert it matches `state.terrain[(x,y)]` exactly, proving `wolf_den` — not
     `near_forest` — was the last writer). This is the concrete regression guard for Decision 3's
     "wolf_den wins the overlap" claim — without it, a future accidental YAML reorder would silently
     flip which region's terrain wins the shared box with no test catching it.
   - Where: same file as test #2.

4. **`test_wolf_den_near_forest_recompile_same_seed_is_bit_identical`**
   - Category: integration (determinism)
   - Verifies AC #3: compiling the same world+seed twice produces a bit-identical `state.terrain`
     dict (full dict equality, not just `state_hash` — per `TCK-20260821-COMPILER-NOISE-FILL`'s
     investigation, `state_hash` structurally excludes terrain) and identical `state_hash` (belt and
     suspenders — hash equality is necessary though not sufficient). Recompiling with a different
     seed should produce a measurably different `state.terrain` dict restricted to the two wolf-den
     regions' bounds (sanity check that noise-fill is actually seed-sensitive for this real content,
     not accidentally short-circuited).
   - Where: same file as test #2/#3.

5. **`test_wolf_den_near_forest_module_regions_preserve_non_terrain_fields`**
   - Category: unit (explicit AC #1 field-preservation guard, narrower/faster than test #1)
   - Verifies: `hazard_level == {"near_forest": 1.0, "wolf_den": 2.0}`, `hazard_kind ==
    {"near_forest": "NATURAL_TERRAIN", "wolf_den": "NATURAL_TERRAIN"}`, `tags == {"near_forest":
    ["forest"], "wolf_den": ["forest"]}`, `type == {"near_forest": "wilderness", "wolf_den":
    "wilderness"}` for the resolved contribution — a fast, targeted duplicate of part of test #1's
    assertion, kept separate so a future terrain-only edit failure doesn't also mask a field-drift
    failure (or vice versa) under one giant assertion.
   - Where: same file as test #1 (can be merged into test #1 if Plan prefers one assertion-dense
     test over two narrow ones — either is acceptable, this is a style choice not an architectural
     one).

## Scoped Pytest Commands

```
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/integration/content/test_strict_world_matrix.py \
       tests/integration/content/test_resource_region_coverage_corpus.py \
       tests/integration/content/test_swamp_border_pack.py \
       tests/unit/worldbuilding/ \
       tests/certification/test_world_compile_determinism.py \
       -v -m "not slow"
```

Never run the bare `pytest tests/`. This scope covers: the module-pipeline tests that must stay
unmodified (AC #4), the compiler-mechanism unit tests (regression surface for the already-implemented
noise-fill logic this ticket exercises for the first time with real content), the two other real-world
composition test files that include `wolf_den_near_forest`, and the certification determinism suite
(belt-and-suspenders for AC #3, though not sufficient alone per the anti-drift guard below).

## Anti-Drift Test Guards

- **`test_hazard_kind_survives_module_pipeline` must not be edited** to accommodate this migration —
  if it needs editing, that is a signal the migration broke `hazard_kind` preservation, not that the
  test is wrong. Treat any need to touch this test as a scope-violation alarm, not a green light.
- **No test in this plan should assert `state_hash` equality as sufficient proof of correct terrain
  content** — per `TCK-20260821-COMPILER-NOISE-FILL`'s investigation, `state_hash` cannot detect a
  terrain-painting regression at all (it structurally excludes `state.terrain`). Test #4's hash
  assertion is supplementary only; the dict-content assertion is load-bearing.
- **Test #3 (overlap-box resolution) is the specific guard against silent paint-order drift** — if a
  future content edit reorders `near_forest`/`wolf_den` in the YAML (accidentally or otherwise), this
  test must fail, since Decision 3 explicitly ties correctness to "wolf_den declared second."
- **No test should assert on `TERRAIN_COST`-derived movement cost for `swamp`/`forest` tiles** — the
  casing bug (`src/core/state.py` uppercase keys vs. lowercase real content) means any such assertion
  would either trivially pass on the broken `1.0` default (asserting nothing meaningful) or require
  fixing the casing bug, which is explicitly out of scope. A test asserting real cost differentiation
  here would be testing a bug fix this ticket does not make.
- **No test should assert `allow_overlapping_regions` gets set to `true`** anywhere in this
  migration's world compositions — Decision 3 explicitly keeps the region declaration order as the
  resolution mechanism, not a validation-spec opt-in; this ticket does not touch `ValidationSpec` at
  all, and `test_worldspec_schema.py:51`'s default-`False` assertion must remain accurate.
