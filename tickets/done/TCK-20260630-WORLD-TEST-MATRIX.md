---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260630-WORLD-TEST-MATRIX
phase: done
date: 2026-06-30
tags: [world, testing, modules, integration]
---

# TCK-20260630-WORLD-TEST-MATRIX

## Title
Add 5 missing modules to integration test MODULE_MATRIX

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`tests/integration/worldassembly/test_real_content_world_modules.py` has a hard-coded
`MODULE_MATRIX` of 15 modules. There are 20 modules in `data/content/world_modules/`.
Five modules are not in the matrix and thus never tested for schema validity or
normalization correctness:

Missing from MODULE_MATRIX:
- `hero_adventurers` — population module, no regions or quests; unusual shape
- `orc_clan_territory` — conflict module used by frontier_extended
- `forest_warden_grove` — ecology/conflict module with two regions
- `sunken_swamp_border` — danger_zone module, 0 quests
- `survivor_camp_shelter` — settlement/shelter module, 0 quests

If any of these have schema drift or normalization failures, no test catches it.

## Scope
1. Add all 5 missing module IDs to `MODULE_MATRIX` in
   `tests/integration/worldassembly/test_real_content_world_modules.py`
2. Verify all 5 load, normalize, and pass existing test assertions
3. If any module fails the current assertions, investigate: either fix the module data
   or add a separate test that captures the intentional deviation (e.g., `hero_adventurers`
   legitimately has no regions — that should not be a test failure)
4. Ensure the test file's comment stays accurate: update "TCK-20260614-WORLDDAT-NEWMODS" /
   "TCK-20260619-E13B-MODULE-TYPES" references with this ticket's ID for the new 5

## Out of Scope
- Adding new integration tests beyond the existing load/normalize pattern
- Changing module schemas or data

## Acceptance Criteria
- [x] `MODULE_MATRIX` contains all 20 module IDs
- [x] `pytest tests/integration/worldassembly/test_real_content_world_modules.py` passes
- [x] No module silently skipped or ignored

## Related Tickets
- TCK-20260630-WORLD-DEPLOY-MODULES (modules must exist before being tested)

## Related Docs
- None specific

## Related Code Areas
- `tests/integration/worldassembly/test_real_content_world_modules.py:19` — MODULE_MATRIX
- `data/content/world_modules/hero_adventurers.yaml`
- `data/content/world_modules/orc_clan_territory.yaml`
- `data/content/world_modules/forest_warden_grove.yaml`
- `data/content/world_modules/sunken_swamp_border.yaml`
- `data/content/world_modules/survivor_camp_shelter.yaml`

## Assumptions / Open Questions
- `hero_adventurers` has no `regions` field — the `test_real_world_modules_normalize`
  test should not require regions. Confirm this before adding (likely fine, normalization
  just defaults to empty list).

## Implementation Notes
- Add to the list starting at line 19 of the test file, after the last existing entry.
- Group with a comment: `# TCK-20260630-WORLD-TEST-MATRIX: previously untested modules`
- Run test with just these 5 first: `pytest -k "hero_adventurers or orc_clan"` to confirm
  before running the full matrix.

## Test Summary
- `pytest tests/integration/worldassembly/test_real_content_world_modules.py` — all pass

## Files Changed
- `tests/integration/worldassembly/test_real_content_world_modules.py` — added 5 modules to MODULE_MATRIX (lines 29-33)

## Completion Summary
Added hero_adventurers, orc_clan_territory, forest_warden_grove, sunken_swamp_border, survivor_camp_shelter to MODULE_MATRIX. hero_adventurers has no regions field — verified test assertions handle empty list correctly (0 == 0). All 5 tests pass (5/5). MODULE_MATRIX now covers all 20 modules.
