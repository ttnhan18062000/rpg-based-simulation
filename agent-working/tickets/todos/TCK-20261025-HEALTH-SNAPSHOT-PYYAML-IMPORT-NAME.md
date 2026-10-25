---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261025-HEALTH-SNAPSHOT-PYYAML-IMPORT-NAME
phase: open
date: 2026-10-25
tags: []
---

# TCK-20261025-HEALTH-SNAPSHOT-PYYAML-IMPORT-NAME

## Title
The codebase-health snapshot maps pyyaml to its import name `yaml`, so it no longer lists pyyaml as an unused core dependency

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Finding from lead-planner, owner approval logged on #715 (issuecomment-6398266862). The fix is codebase's.

`codebase/reports/codebase_health_baseline.py` derives each core dependency's import name from its distribution name. `_dependency_import_name()` uses `CORE_DEPENDENCY_IMPORT_OVERRIDES` first. If the name isn't there, it replaces `-` with `_`. The override map has one entry, `"python-json-logger": "pythonjsonlogger"`, so `pyyaml>=6.0` maps to `pyyaml`. But the package is imported as `yaml`: 28 files under src/ do `import yaml`, plus tools and tests. The latest `codebase_health_history.jsonl` row therefore lists pyyaml under `unused_core_dependencies` (`['xxhash', 'sse_starlette', 'pythonjsonlogger', 'pyyaml']`), and that entry is false.

codebase-planner checked every other entry in `[project].dependencies` on origin/main 0613ed19a. None has the same problem: `typing-extensions`, `prometheus-client` and `sse-starlette` all reach their import names through the default `-`→`_` rule, and `uvicorn[standard]` loses its extra. pyyaml is the only distribution whose import name the default rule can't reach.

## Scope
- Add `"pyyaml": "yaml"` to `CORE_DEPENDENCY_IMPORT_OVERRIDES` in `codebase/reports/codebase_health_baseline.py`.
- Add `assert chb._dependency_import_name("pyyaml>=6.0") == "yaml"` to `test_dependency_import_name_override` in `tests/codebase/test_codebase_health_baseline.py`.
- Add a regression test in the same file's `find_unused_core_dependencies` tmp-repo style. A repo declaring `pyyaml>=6.0` with a file that does `import yaml` reports `unused == []`.

## Out of Scope
- pyproject.toml / uv.lock. lead-planner's separate hotfix drops `python-json-logger` and `sse-starlette`, and #743 already dropped `xxhash`. This ticket doesn't depend on either.
- Rewriting or back-filling past rows of `codebase_health_history.jsonl`. History stays as recorded; the next snapshot reads right.
- Replacing the override map with `importlib.metadata` top-level discovery. That's a possible later improvement, not needed for one entry.

## Acceptance Criteria
1. `_dependency_import_name("pyyaml>=6.0") == "yaml"`. The existing assertions for python-json-logger, sse-starlette and uvicorn[standard] still pass.
2. A tmp-repo test with `pyyaml>=6.0` declared and `import yaml` used gets `find_unused_core_dependencies() == []`. The same test must fail against the unpatched map: the implementer confirms this once by reverting the one-line change locally and running it.
3. Run against the real repo at the branch head, `find_unused_core_dependencies(repo_root)` doesn't include `pyyaml`. Record the actual list in Test Summary. It depends on whether lead-planner's hotfix has merged: before it, the list is `['sse_starlette', 'pythonjsonlogger']`; after it, `[]`.
4. `pytest tests/codebase/test_codebase_health_baseline.py` passes, and `make code-health` reports 0 new and 0 worse. No baseline is raised.
5. Hand-closed per CLAUDE.md, with `record_hand_orchestrated_closure.py` (`--tier hotfix --path-reason small_change`).

## Related Tickets
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET (introduced the snapshot and the override map)
- TCK-20261025-DROP-UNUSED-XXHASH-DEPENDENCY (#743)
- lead-planner's python-json-logger / sse-starlette drop hotfix (separate, independent)

## Related Docs
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
- none

## Related Code Areas
- codebase/reports/codebase_health_baseline.py (`CORE_DEPENDENCY_IMPORT_OVERRIDES`, `_dependency_import_name`, `find_unused_core_dependencies`)
- tests/codebase/test_codebase_health_baseline.py

## Assumptions / Open Questions
- None blocking. The import-name fact can be checked with `grep -rl '^import yaml\|^from yaml' src/`.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
