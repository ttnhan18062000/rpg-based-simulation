---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME
artifact_type: test_plan
tags: [content, combat, social]
---

# Test Plan — TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME

## Renamed test files (file + contents)
- `tests/unit/combat/test_species_relations_legality_wiring.py`
- `tests/unit/combat/test_species_relations_tactical_wiring.py`
- `tests/unit/content/test_species_relations_catalog.py`
- `tests/unit/content/test_species_relations_coverage.py`
- `tests/unit/content_semantics/test_relation_species_projection.py`
- `tests/integration/lab/test_species_relations_metamorphic_validation.py` (`@pytest.mark.slow`
  `@pytest.mark.resource_budget_large` — not run this session, matching child 1's established
  practice of deselecting slow/resource-heavy tests under this session's concurrent-multi-session
  memory pressure; content fully rewritten and reviewed, not executed)

## Other files fixed
- `tests/integration/combat/test_relation_combat_integration.py` (broken `get_race_id_str` import
  + `RelationContext(target_race=...)` kwargs, found via full-sweep collection error)

## Result
- Scoped run: `pytest tests/unit/combat/test_species_relations_legality_wiring.py tests/unit/combat/
  test_species_relations_tactical_wiring.py tests/unit/content/test_species_relations_catalog.py
  tests/unit/content/test_species_relations_coverage.py tests/unit/content_semantics/ -m "not slow"`
  → **34 passed**.
- `tests/unit/content/ tests/unit/combat/ tests/unit/engine/` → **539 passed, 1 skipped, 3
  deselected**.
- `tests/unit/world/ tests/unit/strategic/ tests/integration/combat/` → **625 passed**.
- `tests/unit/lab/ tests/integration/lab/` (`-m "not slow"`) → **129 passed, 1 deselected**.
- `docs/mechanics/content_usage_matrix.md`'s `social/race_relations` row regenerated to
  `social/species_relations` via its own generator test (`test_content_usage_matrix.py`, 24 passed).
- Full repo sweep: `tests/unit/ tests/integration/` (`-m "not slow"`) → **6008 passed, 9 skipped, 84
  deselected, 2 failed**. Both failures
  (`tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`,
  `tests/integration/world/test_long_run_stability.py::test_long_run_stability`) are the identical
  `tests/conftest.py:68` resource-time-limit `TimeoutError` diagnosed as environment-load noise in
  child 1's own test_plan.md — neither test touches species/race identity logic, and both are
  long-tick real-simulation timing tests sensitive to this session's confirmed severe concurrent
  memory/CPU pressure (swap exhausted). Not rename regressions.
- Full repo-wide grep confirms zero remaining `race_relations`/`RaceRelationRecord`/
  `get_race_id_str`/`source_race`/`target_race` references outside historical TCK-ID citations and
  unrelated concurrency "race" terminology.
