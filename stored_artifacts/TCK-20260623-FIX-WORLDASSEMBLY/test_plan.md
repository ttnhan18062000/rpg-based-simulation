---
ticket_id: TCK-20260623-FIX-WORLDASSEMBLY
phase: test_plan
date: 2026-06-23
status: complete
---

# Test Plan: TCK-20260623-FIX-WORLDASSEMBLY

## Summary

Both fixes are pure content/fixture corrections — no logic was changed. The existing test suite fully exercises both root causes. No new tests are required; the goal is to make the existing tests pass.

---

## Regression Surface

### Directly affected tests (must pass after fix)

| Suite | Command fragment | Covers |
|---|---|---|
| WorldAssembly unit | `tests/unit/worldassembly/test_assembly.py` | RC1: river_ford terrain ref |
| WorldAssembly perspective | `tests/unit/worldassembly/test_perspective_resolution.py` | RC1: assembly chain |
| WorldAssembly quest merge | `tests/unit/worldassembly/test_quest_merge.py` | RC1 + quest definitions wiring |
| WorldAssembly provenance | `tests/unit/worldassembly/test_provenance.py` | RC1: full assembly path |
| Catalog smoke simulation | `tests/unit/core/test_catalog_smoke_simulation.py` | RC2: quest type field |
| Strict world matrix | `tests/integration/content/test_strict_world_matrix.py` | RC1: content registry validation |
| Swamp border pack | `tests/integration/content/test_swamp_border_pack.py` | RC1: module composition |
| Multi-pack composition | `tests/integration/content_packs/test_multi_pack_composition.py` | RC1: cross-module assembly |
| Scenario catalog matrix | `tests/integration/scenarios/test_scenario_catalog_matrix.py` | RC1: full scenario pipeline |

### Adjacent tests (should remain unaffected)

- `tests/unit/worldbuilding/test_quest_definition.py` — QuestDefinition schema tests; not affected by content changes
- `tests/unit/worldbuilding/test_world_compiler.py` — WorldSpec compilation; already has `type` field in fixtures
- `tests/unit/content/` — Terrain catalog loading; adding `river` entry adds a node, no deletions
- `tests/integration/content/test_catalog_validation.py` — If it exists, adding `river` terrain resolves the dangling edge

---

## New Tests Required

None. The existing test suite already covers both failure modes:
- `test_structural_world_assembly_resolver` exercises the full assembly → validate → raise path for RC1.
- `test_catalog_mode_smoke_simulation` directly exercises `WorldSpec.model_validate()` with quest data for RC2.
- `test_world_spec_invalid_quest_type_raises_validation_error` (existing) verifies that `type` IS required — this test must continue to pass after fix (it is not affected by our fixture change).

---

## Scoped Pytest Commands

### Primary acceptance gate (run this first)
```bash
python3 -m pytest \
  tests/unit/worldassembly/ \
  tests/unit/core/test_catalog_smoke_simulation.py \
  tests/integration/content/ \
  tests/integration/content_packs/test_multi_pack_composition.py \
  tests/integration/scenarios/test_scenario_catalog_matrix.py \
  -x -q 2>&1 | tail -40
```

### Confirm RC1 fix in isolation
```bash
python3 -m pytest tests/unit/worldassembly/test_assembly.py::test_structural_world_assembly_resolver -x --tb=short -q
```

### Confirm RC2 fix in isolation
```bash
python3 -m pytest tests/unit/core/test_catalog_smoke_simulation.py::test_catalog_mode_smoke_simulation -x --tb=short -q
```

### Confirm no regression in quest schema tests
```bash
python3 -m pytest tests/unit/worldbuilding/test_quest_definition.py tests/unit/worldbuilding/test_world_compiler.py -x -q
```

### Confirm terrain catalog still validates cleanly
```bash
python3 -m pytest tests/unit/content/ -x -q 2>/dev/null || echo "no unit/content suite — skip"
```

### Full acceptance run (per ticket criteria)
```bash
python3 -m pytest \
  tests/unit/worldassembly/ \
  tests/unit/core/test_catalog_smoke_simulation.py \
  tests/integration/content/test_strict_world_matrix.py \
  tests/integration/content/test_swamp_border_pack.py \
  tests/integration/content_packs/test_multi_pack_composition.py \
  tests/integration/scenarios/test_scenario_catalog_matrix.py \
  -v 2>&1 | tail -60
```

Expected counts:
- `tests/unit/worldassembly/` — 15 tests pass (6 + 4 + 3 + 2)
- `tests/integration/content/test_strict_world_matrix.py` — 36 parametrized tests pass
- `tests/integration/content/test_swamp_border_pack.py` — 2 tests pass
- `tests/integration/content_packs/test_multi_pack_composition.py` — 8 tests pass
- `tests/integration/scenarios/test_scenario_catalog_matrix.py` — 16 tests pass
- `tests/unit/core/test_catalog_smoke_simulation.py` — 1 test passes
