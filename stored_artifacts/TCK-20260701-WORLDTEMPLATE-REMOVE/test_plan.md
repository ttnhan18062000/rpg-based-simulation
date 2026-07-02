---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-WORLDTEMPLATE-REMOVE
artifact_type: test_plan
tags: [world, worldtemplate, schema, deprecation, cli, refactor]
---

# Test Plan — TCK-20260701-WORLDTEMPLATE-REMOVE

## Regression Surface
Removing `worldtemplate.v1` touches five production files
(`src/worldbuilding/cli.py`, `src/worldbuilding/recipe.py`, `src/worldbuilding/repository.py`,
`src/worldbuilding/__init__.py`, `src/cli/entry.py`). The regression surface is:

1. **`worldcomposition.v1` path must be fully unaffected** — `handle_resolve`, `handle_compile`
   (composition branch), `WorldAssemblyResolver.assemble()`, `WorldModuleSpec`
   (`RegionRecipeSpec`/`PopulationRecipeSpec`/`ResourceRecipeSpec`/`BuildingRecipeSpec` reuse).
2. **`worldspec.v1` direct-load path must be fully unaffected** — `handle_validate`/
   `handle_compile`/`handle_inspect`'s `else` branches, `WorldRepository.load_world()`.
3. **CLI argument parsing** — `create-template` subparser must still parse two positional args
   and produce a file the repository can index.
4. **`WorldRepository.rebuild_index()`** — index status classification (`VALIDATED` /
   `COMPOSITION` / `BROKEN`) must not regress for the two remaining schema types once the
   `TEMPLATE` branch is removed.
5. **`src/cli/entry.py::_run_cli()`** — the real simulation entrypoint must still load and
   compile `worldspec.v1` and `worldcomposition.v1` (via resolved artifacts) worlds correctly
   after its `worldtemplate.v1` branch is simplified away.
6. **No import errors** — `src/worldbuilding/__init__.py` must not export removed names;
   nothing else in the repo imports `WorldTemplateSpec`/`WorldTemplateExpander` from the
   package root (confirmed via grep — only `cli.py`, `test_world_recipes.py`, `recipe.py`
   itself, `repository.py`, `cli/entry.py` reference these names; all are being edited/removed
   in this ticket).

## New/Updated Tests Required

| File | Action | Reason |
|---|---|---|
| `tests/unit/worldbuilding/test_world_recipes.py` | **Delete entire file** | Every test in it (`test_population_recipe_expands_to_expected_count`, `test_resource_recipe_expands_to_expected_node_count`, `test_building_recipe_expands_to_expected_building_count`, `test_recipe_expansion_is_deterministic_by_seed`, `test_recipe_cannot_create_objects_outside_topology`, `test_recipe_ids_are_stable_and_traceable`, `test_recipe_expansion_does_not_bypass_validation`) exercises `WorldTemplateSpec`/`WorldTemplateExpander`, which are being deleted. No behavior remains to test. |
| `tests/cli/test_world_cli.py::test_cli_create_template_bootstraps_correctly` (L226-259) | **Rewrite** | Currently asserts `raw["schema_version"] == "worldtemplate.v1"` and `len(raw["regions"]) == 2` (template-shaped). Must assert the repointed output is a valid minimal `worldcomposition.v1` file instead: `schema_version == "worldcomposition.v1"`, presence of `world_id`/`name`/`module_refs` (or `modules`) keys, and that it round-trips through `WorldCompositionSpec.model_validate()` without error. The trailing "verify bootstrapped file validates via `validate` subcommand" assertion (L255-259) should be kept in spirit — validate the new file via `WorldCompositionSpec.model_validate(raw)` directly (not `handle_validate`, since `handle_validate` for compositions expects `resolve` to have run first — confirm this at implementation time by reading `handle_validate`'s `else` branch behavior for `worldcomposition.v1` raw data, since `repo.load_world()` for a composition requires a `resolved/` dir that a fresh bootstrap won't have). |
| `tests/cli/test_world_cli.py` | **Add** new test: `test_cli_create_template_rejects_existing_world` | Verify the existing-file guard (L390-392 in `cli.py`) still works after the rewrite — regression-prone since the function body changes. |
| `tests/unit/worldbuilding/test_world_repository.py` | **Add** test(s) for `rebuild_index()` | No existing test covers the `TEMPLATE`/`COMPOSITION`/`VALIDATED`/`BROKEN` status branch in `rebuild_index()` (confirmed via grep — zero `TEMPLATE` references in this file today). Add a regression guard: a `worldcomposition.v1` world still indexes as `COMPOSITION` and a `worldspec.v1` world still indexes as `VALIDATED` after the `worldtemplate` branch is deleted from `repository.py:194-198`. |
| `tests/cli/test_entry_parity.py` | **Inspect, likely no change needed** | Confirmed zero `worldtemplate` references today — but since `src/cli/entry.py::_run_cli()`'s branch is being simplified, re-run this file to confirm no incidental coverage breaks. |

## Scoped Pytest Commands
Do not run the full suite. Scope to the touched domains:

```bash
# Worldbuilding unit tests (recipe/repository/cli-adjacent schema logic)
pytest tests/unit/worldbuilding/ -v

# World CLI integration tests
pytest tests/cli/test_world_cli.py -v

# CLI entry parity (src/cli/entry.py touched)
pytest tests/cli/test_entry_parity.py -v

# World assembly / module tests — regression guard that shared RegionRecipeSpec/
# PopulationRecipeSpec/ResourceRecipeSpec/BuildingRecipeSpec classes still work
pytest tests/unit/worldassembly/ tests/integration/worldassembly/ -v

# World modules tests — regression guard for WorldModuleSpec's use of the shared Recipe classes
pytest tests/unit/worldmodules/ -v 2>/dev/null || echo "confirm path exists at implementation time"
```

## Anti-Drift Test Guards
- After deleting `tests/unit/worldbuilding/test_world_recipes.py`, run
  `grep -rn "WorldTemplateSpec\|WorldTemplateExpander" tests/ src/` (excluding `reviews/`) and
  confirm **zero** remaining hits — this is the acceptance-criteria-equivalent check for "No
  dead imports or unused functions left behind."
- Before deleting anything from `recipe.py`, run
  `pytest tests/unit/worldassembly/test_assembly.py tests/unit/worldassembly/test_archetype_preservation.py tests/integration/worldassembly/test_real_content_world_compositions.py -v`
  as a BEFORE baseline, then again AFTER the `recipe.py` edit — these tests construct
  `RegionRecipeSpec`/`PopulationRecipeSpec` directly and are the fastest signal if the shared
  classes were accidentally broken or removed.
- Confirm `python3 -m src.worldbuilding.cli list` (or the equivalent test coverage in
  `test_cli_list_worlds`) still runs cleanly against the real `data/worlds/` tree after the
  `repository.py` edit — this exercises `rebuild_index()` against all 10 real world
  directories, which is a stronger integration signal than the unit test fixtures alone.
- Do not run `pytest tests/` (full suite) per project testing rule — scope as listed above.
