---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST

## Title
Unit tests that write fixed data/runs dirs fail under pytest-xdist because another worker removes the dir underneath them

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
rpg-implementer-2 found this on 2026-10-20 while checking rpg-pre-v1-fixes. It already exists on origin/main e52719485: 3 repeats of `-n 2 --dist loadgroup` on 4 files, on main and on the branch.
- `tests/unit/engine/test_run_manifest_signal_contract.py::test_a_live_run_and_an_audit_run_say_so` fails every time. The log shows `QualityPersistence.write_report: failed to write ... data/runs/sc_manifest_live/quality_report.json.tmp: No such file`. The test uses the fixed run ids `sc_manifest_canonical`, `sc_manifest_live` and `sc_manifest_audit` under the shared `data/runs`.
- Setup ERRORs that move between runs: `tests/unit/worldmodules/test_schema_unified.py::test_worldmodulespec_accepts_any_schema_version_string` on the branch, and the rpg_gate_harness hash test on main.
- The testing-owned `tests/unit/tools/test_rpg_gate_harness.py` globs `data/runs/rpg-gate-sandbox_world-s1-*`. It is routed to testing-planner and is out of scope here.
All of these pass when run serially, and CI's unit-infra lane passes.

## Scope
- Find which test removes the shared `data/runs` dirs while another worker is using them.
- Give the rpg-owned tests a per-test run root (a tmp_path or a worker-unique run id) or an xdist_group, so the full unit suite passes under `-n 2`.
- Explain the `test_schema_unified` setup error, or fix it.
- Extension (rpg-planner, same bug class, CI integration lane runs `-n auto --dist loadgroup`): the integration tests with two or more tests sharing one fixed run id or dir whose teardown removes it. Fixed: `tests/integration/observability/test_metric_windows_flow.py` (CI failure `Manifest not found for run_id: test_run_metrics_integration_123`, runs 39384347217 and 39384515890), `test_event_recorder_live_publish.py`, `test_cognition_snapshot_artifact.py`. Surveyed and left alone because only one test uses the id/dir (no sibling to race): test_run_artifact_flow, test_phase23/24/25/26 artifact tests, test_cognition_diff_events, test_decision_trace_determinism, the V4/gate-validity/starving-merchant real-kernel tests (per-test ids), test_export_flow and test_analysis_pipeline_flow (tmp paths). tests/api and tests/regression have no `rmtree` of shared ids.

## Out of Scope
- tests/unit/tools/test_rpg_gate_harness.py (testing-planner).
- Changing CI lane parallelism.

## Acceptance Criteria
- `pytest tests/unit -n 2` gives 0 failures and 0 errors on 3 repeats.
- No test writes a fixed id under the shared data/runs without isolation.

## Related Tickets
- TCK-20261020-CI-LANES-RUN-TRAILING-BACKSLASH-AND-XDIST (agent-working)

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/engine/test_run_manifest_signal_contract.py
- tests/unit/worldmodules/test_schema_unified.py
- src/observability quality persistence (`QualityPersistence.write_report`)

## Assumptions / Open Questions
- Which test does the removing is still a guess (another worker's data/runs cleanup).

 Not a blocker.

2026-10-20 testing-implementer ran a full `pytest tests/unit -n 2 --dist loadgroup -m "not slow and not extra_slow"` on main: 8347 passed, 5 skipped, 1 failed. The failure was test_run_manifest_signal_contract.py::test_a_canonical_run_records_its_contract_and_work_model, `FileNotFoundError: Manifest not found for run_id: sc_manifest_canonical`, the same fixed-id race. The harness-hash setup ERROR did not reproduce in 16 runs. Testing reads the moving setup ERROR (harness-hash on main, schema_unified on the branch) as worker-level and has given it to this ticket. Testing's half is fixed in #676 (test-only).

## Test Summary
Reproduction (4 files, `-n 2 --dist loadgroup`, 3 repeats): 3 of 3 failed on origin/main (manifest test + one sentinel ERROR); after the fix 3 of 3 passed (25 passed). `pytest tests/unit -n 2 -m "not slow and not extra_slow"` x3: 8348 passed, 5 skipped, 0 failures, 0 errors each time; no `sc_manifest*`/`prov_load*` dirs left in data/runs. (The full suite also passed before the fix on one try: the race is timing-dependent, hence the targeted reproduction.)

Integration: `test_metric_windows_flow.py test_event_recorder_live_publish.py test_cognition_snapshot_artifact.py` under `-n 4 --dist loadgroup`, 3 repeats: 9 passed each time. Kernel shutdown in `finally` in the two metric-window kernel tests.

## Files Changed
tests/unit/engine/test_run_manifest_signal_contract.py, tests/unit/engine/test_kernel_provenance_manifest_load.py, tests/integration/observability/test_metric_windows_flow.py, test_event_recorder_live_publish.py, test_cognition_snapshot_artifact.py

## Completion Summary
Tests-only: fixed run ids shared between xdist workers are now unique per test and process.
