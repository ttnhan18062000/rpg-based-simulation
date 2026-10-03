---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY

## Normal flow
- `tests/unit/content_semantics/test_personality.py` (9 tests, new): the extracted shared
  module's own public API — `get_bravery_bias`, `get_action_style_for_bravery`,
  `build_personality_for_entity` (determinism, race-correlation, `None`-faction safety), plus the
  2 config-loading tests moved from `test_world_compiler.py`.
- `tests/unit/entities/test_archetype_entity_factory.py` (4 new tests): `build_entity()` now
  produces real non-zero personality, `ActionStyle` correlates with bravery, determinism given a
  seed, and the default-seed backward-compatibility case.
- `tests/unit/worldassembly/test_entity_spawner_legacy_guard.py` (4 tests, new): the same 4
  properties, verified directly against `_spawn_legacy_guard()` (the second, separate real
  construction branch).
- `tests/integration/worldassembly/test_world_entity_spawner.py` (4 new tests): real,
  fixture-driven (real `CatalogRepository`/`WorldModuleRepository`/`WorldAssemblyResolver`)
  confirmation that every spawned entity gets real personality, determinism given a seed, and
  that different seeds produce different results (confirms the seed is actually threaded through,
  not silently ignored).

## Real end-to-end verification (not unit-test-only)
Direct live run of `CatalogScenarioStateBuilder.build()` against the real `wolf_territory_pressure`
scenario (`frontier_living_world` composition, `wolf_den_near_forest` module) — the same fixture
`test_catalog_scenario_state_builder.py` already uses. Result: 15/15 real entities get non-zero
personality; the 3 real `wild_beast_pack` wolf/spider entities show bravery 0.617-0.989 (correctly
biased high) with 2/3 landing `AGGRESSIVE` ActionStyle — confirms the fix works through the real,
full pipeline (`ScenarioSetupResolver` → `WorldEntitySpawner` → `AuthoritativeState`), not just at
the unit level.

## Failure modes / regression-prone paths
- Real regression caught and fixed during this ticket's own Test phase: extracting the shared
  helpers out of `compiler.py` broke 2 existing tests that referenced
  `compiler._load_personality_bias_config` directly — moved those 2 tests to
  `test_personality.py` (the real, new owner of that logic) rather than reverting the extraction.
- Real regression caught and fixed: `src/content/matrix.py`'s own `social/personality_bias`
  content-usage-matrix entry still pointed its `evidence_tests` field at the old, now-moved test
  location — `tests/unit/content/test_content_usage_evidence.py::
  test_all_matrix_evidence_paths_exist` caught this; updated the matrix entry to the real, new
  location and regenerated `docs/mechanics/content_usage_matrix.md`.
- `tests/unit/entities/test_archetype_entity_factory.py::test_factory_does_not_import_catalog_repository`
  (a real, pre-existing architecture guard) re-verified passing — confirms the new
  `content_semantics.personality` import doesn't leak a `CatalogRepository` dependency into
  `archetype_factory.py`.

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/entities/ tests/unit/worldassembly/ \
  tests/unit/content_semantics/ tests/unit/worldbuilding/ tests/unit/scenarios/ \
  tests/integration/entities/ tests/integration/worldassembly/ tests/unit/certification/ \
  tests/integration/certification/ tests/unit/combat/ tests/unit/core/ tests/unit/tactical/ \
  tests/unit/movement/ tests/unit/strategic/ tests/unit/content/ -q -m "not slow"
```
Result: 1185 passed, 2 pre-existing failures already confirmed unrelated to this or any prior
ticket this session (`test_module_family_anchored` — missing world data directory;
`test_normal_move_triggers_oa` — pre-existing, confirmed back in
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`). Zero new regressions after the
2 real fixes above landed.
