# Test Plan — TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE

## Regression Surface (existing tests that must pass or be intentionally updated)

| Test | File | Expected outcome |
|---|---|---|
| `test_grade_regression.py` (4 sandbox_world anchor keys) | `tests/simulation_quality/test_grade_regression.py` | WILL initially fail after migration — must be fixed by regenerating `grade_anchors.json` from fresh calibration runs, not left broken |
| `test_quest_definition.py` (`quests: []` reference) | `tests/unit/worldbuilding/test_quest_definition.py:222` | References sandbox_world generically, not by region name — should pass unaffected; verify |
| `test_entity_differentiation.py` | `tests/integration/scenarios/test_entity_differentiation.py:44` | Explicitly avoids sandbox_world ("too few heroes") — unaffected, confirm no accidental dependency |
| `test_world_recipes.py` | `tests/unit/worldbuilding/test_world_recipes.py` | Contains "woods" string — check if it's testing sandbox_world specifically or a generic recipe fixture; if the latter, unaffected |
| Full `tests/unit/worldbuilding/` and `tests/integration/worldassembly/` suites | — | Should be unaffected (compiler/resolver code unchanged) but run to confirm no fixture assumes `worldtemplate.v1` is the only/default schema anywhere unexpected |

## New Tests Required

- None strictly required by the ticket's Acceptance Criteria (this is a content migration,
  not new engine logic). If a regression test asserting "sandbox_world compiles as
  worldcomposition.v1 with non-flat monster stats" is easy to add, it's a reasonable low-cost
  addition but not mandatory — prefer the existing `MODULE_MATRIX` integration test pattern
  (`tests/integration/worldassembly/test_real_content_world_modules.py`) if extending
  coverage, since `frontier_village_core` and `wolf_den_near_forest` should already appear in
  that matrix (added by `TCK-20260630-WORLD-TEST-MATRIX`) — confirm sandbox_world's new
  module pair is exercised there rather than duplicating a new test file.

## Scoped Pytest Commands

```
pytest tests/simulation_quality/test_grade_regression.py -k sandbox_world -m "not slow" -v
pytest tests/unit/worldbuilding/ -v
pytest tests/integration/worldassembly/ -k "sandbox or module_matrix" -v
pytest tests/unit/worldbuilding/test_quest_definition.py -v
```

## Anti-Drift Test Guards

- Do not silence or delete the sandbox_world grade regression tests to make them "pass" —
  regenerate the anchor data properly per the documented procedure in
  `test_grade_regression.py`'s module docstring.
- Do not weaken the ±1-band tolerance to accommodate a bad migration result — if grades shift
  by more than one band, investigate whether the module pair choice was actually reasonable
  before assuming the tolerance itself is wrong.
