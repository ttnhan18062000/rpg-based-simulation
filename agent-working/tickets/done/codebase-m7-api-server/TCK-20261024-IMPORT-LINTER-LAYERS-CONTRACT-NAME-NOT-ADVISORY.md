---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261024-IMPORT-LINTER-LAYERS-CONTRACT-NAME-NOT-ADVISORY
phase: done
date: 2026-10-24
tags: [architecture, delivery]
---

# TCK-20261024-IMPORT-LINTER-LAYERS-CONTRACT-NAME-NOT-ADVISORY

## Title
The generated import-linter layers contract drops "(advisory)" from its name, because it has been blocking since #671

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Issue #704 item 2, a stale-statement finding from lead-planner-u24. `codebase/structure/importlinter.toml` names the generated `layers` contract "Registry layer order (advisory)". Import-linter has been blocking since #671 (`TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT`), so the name is wrong. Fix it at its generator.

The user chose to fold this into the M7 batch PR; the same approval comment covers it: https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6384147652.

## Scope
1. In `render_block` (`codebase/structure/import_contracts.py:70`), change the name to "Registry layer order".
2. Regenerate `codebase/structure/importlinter.toml` with the module's own generator, not by hand. The diff is that one line.
3. Update the tests that pin the name:
   - the recorded `lint-imports` output near line 377 of `tests/codebase/test_import_contracts.py`;
   - any other hit from `grep -rn "layer order (advisory)" tests codebase docs`.
4. Update docs that quote the contract name, in codebase-owned files only. List any other owner's files for codebase-planner.

## Out of Scope
- The contract's content (`id`, layers, ignore list), or any other contract.
- The comment in `pyproject.toml`: that is #704 item 1, owned by lead-planner and already handled in #710.

## Acceptance Criteria
- `grep -rn "Registry layer order (advisory)"` finds nothing outside the `agent-working/` history and `docs/archive/`.
- `lint-imports` passes, and so does the generator's freshness check in `tests/codebase/test_import_contracts.py`.
- `tests/codebase` passes.

## Related Tickets
- `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT`, `TCK-20261004-IMPORT-LINTER-ADOPTION`

## Related Docs
- `docs/plans/codebase_health/python_code_craft_roadmap.md` (M5)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT/`

## Related Code Areas
- `codebase/structure/import_contracts.py`, `codebase/structure/importlinter.toml`, `tests/codebase/test_import_contracts.py`

## Assumptions / Open Questions
- Assumed: nothing parses the contract by its display name, only by `id = "layers"`. Verify with grep before the change.

## Implementation Notes
render_block names the layers contract 'Registry layer order'; importlinter.toml regenerated with the module's own helper; the recorded lint-imports output in the test updated.

## Test Summary
tests/codebase/test_import_contracts.py 34 passed; lint-imports 17 kept, 0 broken.

## Files Changed
codebase/structure/import_contracts.py, codebase/structure/importlinter.toml, tests/codebase/test_import_contracts.py

## Completion Summary
The generated contract name no longer says advisory.
