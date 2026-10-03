---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-SCHEMA
artifact_type: test_plan
tags: [world, schema]
---

# Test Plan — TCK-20260821-NOISE-FILL-SCHEMA

## Regression Surface

Existing tests that must keep passing, unchanged, since this ticket must produce zero behavior
change for all 20 real world modules and zero compiler consumption:

**Integration (the ticket's own named acceptance-criteria target):**
- `tests/integration/worldassembly/test_real_content_world_modules.py` — all of
  `test_real_world_modules_load_from_data_content`, `test_real_world_modules_normalize`,
  `test_real_world_modules_preserve_count_maps`, `test_real_world_modules_resolve_contributions`,
  `test_hazard_kind_survives_module_pipeline`, `test_real_world_modules_reference_graph_edges_exist`
  — full `MODULE_MATRIX` (20 real modules), explicitly named in the ticket's own Acceptance
  Criteria.

**Determinism (also explicitly named in Acceptance Criteria):**
- `tests/certification/test_world_compile_determinism.py::test_compiler_seeding_determinism` —
  must pass unchanged; confirms `compiler.py` truly untouched (this test only asserts `state_hash`
  equality across two same-seed compiles of existing content, so it will catch any accidental
  compiler-side leak of the new field).

**Unit — worldassembly (direct `RegionRecipeSpec`/`RegionSpec`/resolver construction, several
call sites touch the exact code this ticket edits):**
- `tests/unit/worldassembly/test_assembly.py` — full file. Contains direct `RegionRecipeSpec(...)`
  construction at lines 364, 373, 949, and the `WorldModuleSpec(...)` + `resolve_module_contribution()`
  pattern (`test_id_collision_prevention`, `test_resolved_bundle_includes_compile_context_and_preserves_profiles`)
  this ticket's new declared-value test will mirror.
- `tests/unit/worldassembly/test_archetype_preservation.py` — full file. Contains direct
  `RegionRecipeSpec(...)` construction at lines 85, 119-120.

**Unit — worldbuilding (schema-level, not directly touched but adjacent):**
- `tests/unit/worldbuilding/test_worldspec_schema.py`
- `tests/unit/worldbuilding/test_world_compiler.py` (confirms compiler behavior unchanged — no
  test in this file currently asserts anything about terrain *shape*, per direct read of the
  epic's plan doc, so this is a pure non-regression check, not new coverage)
- `tests/unit/worldbuilding/test_world_validator.py`, `test_world_validation_rules.py` (exercise
  the `ValidationContext.MODULE`/`WORLD` dummy_spec builder paths, confirmed unaffected)

## New Tests Required

1. **`test_terrain_variants_survive_module_pipeline`**
   - Category: integration (real pipeline)
   - Verifies: mirrors `test_hazard_kind_survives_module_pipeline`'s exact shape and covers both
     AC bullets 3 and 4 in one test, matching the precedent test's own combined structure:
     - **Declared-value case**: since no real module YAML may author `terrain_variants` (that's
       `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s job, out of scope here), construct a synthetic
       `WorldModuleSpec` directly in Python — mirroring `test_id_collision_prevention`'s pattern
       (`tests/unit/worldassembly/test_assembly.py:358-375`) — with one `RegionRecipeSpec` using
       the real catalog-registered region id `"hometown"` and an explicit
       `terrain_variants=[TerrainVariantSpec(terrain="FOREST", weight=2.0), TerrainVariantSpec(terrain="GRASS", weight=1.0)]`.
       Run it through `WorldModuleAuthoringNormalizer.normalize()` then
       `WorldAssemblyResolver.resolve_module_contribution()`, and assert the resolved
       `RegionSpec.terrain_variants` equals the declared list exactly (proving explicit forwarding,
       not a silent drop — the exact failure mode `hazard_kind` originally hit).
     - **Default/backward-compat case**: reuse an existing real `MODULE_MATRIX` module (e.g.
       `frontier_village_core`, matching the precedent test's own default-case module), run through
       the same normalize -> resolve pipeline, and assert every resolved region's
       `terrain_variants is None`.
   - Location: `tests/integration/worldassembly/test_real_content_world_modules.py`, placed
     immediately after `test_hazard_kind_survives_module_pipeline` (matches ticket's explicit
     instruction to extend this file, alongside its named template).

2. **`test_region_recipe_spec_accepts_terrain_variants_and_defaults_to_none`**
   - Category: unit
   - Verifies: AC bullets 1 and 2 directly, at the schema level rather than through the full
     pipeline (cheap, fast, isolates the pydantic-model-level guarantee from the pipeline-level
     one covered by test 1 above):
     - `RegionRecipeSpec(id=..., type=..., grid_bounds=...)` with no `terrain_variants` kwarg
       succeeds and `.terrain_variants is None`.
     - `RegionRecipeSpec(id=..., type=..., grid_bounds=..., terrain_variants=[TerrainVariantSpec(terrain="FOREST")])`
       succeeds and round-trips the declared list.
     - `model_config` still has `extra="forbid"` — assert constructing with a genuinely unknown
       kwarg (e.g. `bogus_field=1`) still raises `pydantic.ValidationError`, proving the field
       addition didn't accidentally weaken/replace the `extra="forbid"` policy whose absence was
       the original `HAZARD-KIND-RESOLVER-GAP` failure mode.
   - Location: `tests/unit/worldassembly/test_assembly.py`, placed near the existing
     `RegionRecipeSpec(...)` construction sites (~line 949) for locality with related tests.

3. **`test_region_spec_terrain_variants_default_none`** (optional, small — may be folded into test 2
   if the planner prefers fewer new test functions)
   - Category: unit
   - Verifies: `RegionSpec(...)` (the resolved-side schema) also accepts `terrain_variants` and
     defaults to `None`, independent of `RegionRecipeSpec` — since the two are separately defined
     pydantic models even if `TerrainVariantSpec` itself is shared (see investigation.md's
     `QuestDefinition`-precedent recommendation), each parent model's own field wiring must be
     checked independently.
   - Location: `tests/unit/worldbuilding/test_worldspec_schema.py`.

## Scoped Pytest Commands

```
pytest tests/integration/worldassembly/test_real_content_world_modules.py -v
pytest tests/certification/test_world_compile_determinism.py::test_compiler_seeding_determinism -v
pytest tests/unit/worldassembly/ -v
pytest tests/unit/worldbuilding/ -v
```

Never `pytest tests/`. These four scoped invocations cover: the ticket's explicitly named
acceptance-criteria test target, the explicitly named determinism regression guard, and the two
unit directories containing every direct `RegionRecipeSpec`/`RegionSpec`/resolver construction
call site this ticket's edits touch.

## Anti-Drift Test Guards

- `test_compiler_seeding_determinism` passing unchanged is itself the strongest guard against
  scope creep into `WorldCompiler` — any accidental read/consumption of `terrain_variants` in
  `compiler.py` that changed RNG draw sequencing or output shape for existing content would flip
  this test's `state_hash` comparison.
- The full `MODULE_MATRIX` sweep in `test_real_content_world_modules.py` (20 real modules) is the
  guard against silently breaking any real module's load/normalize/resolve path — since none of
  the 20 declare `terrain_variants`, every one of them must resolve to `terrain_variants=None`
  identically to today's behavior post-change.
- `test_region_recipe_spec_accepts_terrain_variants_and_defaults_to_none`'s `extra="forbid"`
  sub-assertion is the guard against the specific class of gap `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`
  hit — a genuinely-new field silently weakening validation strictness rather than being properly
  wired.
- No test in this plan touches or constructs anything under `data/content/world_modules/*.yaml` —
  a new test that modifies real module YAML content would silently reach into
  `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s scope and should be treated as a scope violation if
  seen in review.
