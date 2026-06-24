---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260624-FIX-WORLDASSEMBLY-TESTS
phase: done
date: 2026-06-24
tags: [worldassembly, test-data, quest-schema, world-modules, integration]
---

# TCK-20260624-FIX-WORLDASSEMBLY-TESTS

## Title
Fix WorldAssembly / worldbuilding integration test failures — test data gaps

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Three WorldAssembly/worldbuilding tests fail due to test data problems (not implementation bugs):

1. `test_cli_resolve_and_compile_integration` — the test references world modules `plains_layout` and `standard_villagers` that do not exist in `data/worldmodules/`. The CLI's `handle_resolve()` returns exit code 1 (unresolvable modules) → test asserts exit code 0 → `assert 1 == 0`.

2. `test_compiled_world_ticks_stability` and `test_compiled_world_quest_warning_validation` — `WorldSpec.model_validate()` fails because `QuestDefinition` has a required `type` field (literal: `escort|hunt|fetch|explore|defend|investigate`) but `create_base_integration_spec()` in the test creates quest dicts without a `type` key.

3. `test_long_run_stability` — likely a cascade from the WorldSpec validation failure above; confirm separately.

## Scope
- `test_cli_resolve_and_compile_integration`: either (a) create minimal `plains_layout` and `standard_villagers` module fixtures in the test setup or in `data/worldmodules/`, or (b) change the test to reference module IDs that actually exist
- `test_compiled_world_ticks_stability` / `test_compiled_world_quest_warning_validation`: add `type: "fetch"` (or appropriate value) to all quest definition dicts in `create_base_integration_spec()`
- Confirm `test_long_run_stability` independently — if it's a cascade, it clears with fix #2

## Out of Scope
- Changing `WorldSpec`, `QuestDefinition`, or any production schema
- Changing `handle_resolve()` CLI behavior

## Acceptance Criteria
- All 4 listed tests pass (or 3 if `test_long_run_stability` has an independent cause — confirm)
- No regression in other worldbuilding tests

## Related Tickets
- Worldgen-module epic (prior epic that built the module system — see MEMORY)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts
None

## Related Code Areas
- `tests/unit/worldassembly/test_assembly.py::test_cli_resolve_and_compile_integration`
- `tests/integration/worldbuilding/test_world_compile_to_state.py` — `create_base_integration_spec()`
- `tests/integration/world/test_long_run_stability.py`
- `src/worldbuilding/schema.py:99` — `QuestDefinition.type` (Literal field)
- `data/worldmodules/` — check existing module IDs

## Assumptions / Open Questions
- For fix #1: check if `plains_layout` / `standard_villagers` should be created as real module files or just as test fixtures that skip the real data directory. Using real data avoids test brittleness.
- For fix #2: confirm `create_base_integration_spec()` is shared across multiple tests in the file — a single fixture change fixes all of them.
- `test_long_run_stability`: run with `--tb=long` first to confirm it's a WorldSpec cascade, not an independent failure.

## Implementation Notes
Fix #2 (quest type field) — locate `create_base_integration_spec()` in `test_world_compile_to_state.py` and add `"type": "fetch"` to each quest dict:
```python
{"id": "q1", "type": "fetch", "title": "...", ...}
```

Fix #1 (CLI module resolution) — easiest approach: change the test to use module IDs that are known to exist in `data/worldmodules/`. Run `ls data/worldmodules/` to get valid IDs. Do not create fake module files in the data directory.

## Test Summary
Run: `pytest tests/unit/worldassembly/test_assembly.py::test_cli_resolve_and_compile_integration tests/integration/worldbuilding/test_world_compile_to_state.py tests/integration/world/test_long_run_stability.py --tb=short -v`

## Files Changed
- `tests/unit/worldassembly/test_assembly.py` — `test_cli_resolve_and_compile_integration`: replaced `plains_layout`/`standard_villagers` module refs (only in `data/world_modules/`, not `data/content/world_modules/`) with `frontier_village_core`/`scalable_bandit_camp` which exist in `data/content/world_modules/` and fit within 100x100 topology
- `tests/integration/worldbuilding/test_world_compile_to_state.py` — added `"type": "fetch"` to `create_base_integration_spec()` quest dict; rewrote `test_compiled_world_quest_warning_validation` invalid quest to use `required_location_tags` with 4 nonexistent tags (actual compiler warning mechanism) instead of nonexistent `target_*` fields that the compiler never validates

## Completion Summary
3 targeted tests now pass (50/50 in worldassembly/worldbuilding suites, no regressions). `test_long_run_stability` is an independent pre-existing performance timeout (tick compute 225ms+ vs 20ms budget on persistence phase) — not related to quest type field.
