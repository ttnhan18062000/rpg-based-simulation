---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP
artifact_type: test_plan
---

# Test Plan — TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP

## New regression tests

`tests/tools/test_generate_registry.py::TestFolderClosedDoneWalk` (new class, 4 tests):
- a folder-closed epic ticket is indexed
- `SEQUENCE.md` excluded from the `done/` folder walk (mirrors the existing `todos/` precedent test)
- the `done/` folder walk is one level only, not recursive (a ticket two levels deep is NOT indexed)
- flat `done/` and folder-closed `done/` entries both combine correctly

`tests/tools/test_done_checker_static.py` (4 new tests):
- `test_migration_complete_epic_is_na` — epic tier gets `NA`, same shape as the existing hotfix test
- `test_ticket_finalized_passes_for_folder_closed_epic` — the core fix, PASS for a nested path
- `test_ticket_finalized_prefers_flat_path_over_nested_if_both_exist` — deterministic tie-break
- `test_ticket_finalized_still_fails_when_folder_nested_but_also_in_inprogress` — the inprogress
  check still works when combined with a nested done path

## Real acceptance check (per ticket AC, not just the synthetic fixture tests above)

```
python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC --tier epic --part finalize
python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC --tier epic --part finalize
```
Both: RESULT PASS. Confirmed both ticket IDs present in the regenerated `docs/REGISTRY.yaml`.

## Scoped test run

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_generate_registry.py \
  tests/tools/test_done_checker_static.py \
  tests/tools/test_done_checker_audit.py \
  tests/tools/test_registry_query.py \
  tests/tools/test_premise_staleness_check.py \
  tests/integrity/test_registry_merge_driver.py \
  tests/tools/test_status_drift_check.py \
  tests/tools/test_codebase_health_baseline.py -q
```
Result: 273 passed (200 across the two primary files, 73 across the adjacent registry-consuming
test files checked for regressions). One transient failure seen mid-implementation
(`test_check_flag_detects_no_drift_against_real_registry`, drift against the live
`docs/REGISTRY.yaml` because this ticket's own file was still mid-move — resolved by the routine
`make docs-registry` regeneration at Finalize, not a real regression).

## Other verification

- `make docs-registry-check` — in sync, 2651 entries (confirms the fix doesn't desync the
  committed `docs/REGISTRY.yaml` from a fresh regeneration).
- `graphify update .` — run after the code/test changes, no topology changes detected.
