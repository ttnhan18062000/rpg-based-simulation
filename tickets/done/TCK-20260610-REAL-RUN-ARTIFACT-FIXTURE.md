---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE
phase: done
date: 2026-06-10
tags: [real, run, artifact, fixture]
---

# TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE

## Title
Add golden run fixture and real-run registration test proving engine artifact compatibility

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Phase 40 E2E tests use synthetically hand-written run artifacts. At least one test must verify that `RegisterSimulationResultWorkflow` accepts a real engine-produced artifact structure.

## Scope
- Create `tests/fixtures/lab_runs/minimal_completed_run/` with schema-valid content
- Add integration tests using the golden fixture
- Preserve existing synthetic manual-run tests

## Out of Scope
- Adding a nightly real-run production test
- Changing the workflow implementation

## Acceptance Criteria
- [x] `tests/fixtures/lab_runs/minimal_completed_run/` exists with schema-valid content
- [x] Fixture schema matches actual `LabRunManifest` output structure
- [x] One test registers the golden fixture successfully
- [x] Corrupt or missing fixture test still blocks correctly
- [x] Existing synthetic tests remain passing and unmodified
- [x] Test is marked with `e2e_golden` marker (registered in pyproject.toml)

## Related Tickets
- TCK-20260524-LAB-KNOWLEDGE (prior work — workflow implementation)

## Related Docs
- Engine contract: `docs/engine/kernel.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-REAL-RUN-ARTIFACT-FIXTURE/`

## Related Code Areas
- `tests/integration/lab_agent/test_golden_run_fixture.py` (new)
- `tests/fixtures/lab_runs/minimal_completed_run/` (new)
- `src/lab/` — LabRunManifest schema

## Assumptions / Open Questions
- `artifact_root` in manifest must be absolute path; tests patch the sentinel `__REPLACED_AT_TEST_TIME__` at runtime when copying fixture to tmp_path.
- `tests/fixtures/` did not exist — created with `__init__.py`.

## Implementation Notes
- Golden fixture: `lab_run_manifest.json` with all LabRunManifest required fields, status=COMPLETED, run_count=1.
- One child run: `runs/run-seed-42/run_report.json` with health_score, anomaly, rule_execution fields.
- `e2e_golden` marker registered in `pyproject.toml`.
- Four tests: registers successfully, manifest parses via LabRunManifest, missing run → BLOCKED, corrupt manifest → BLOCKED.

## Test Summary
`pytest tests/integration/lab_agent/test_golden_run_fixture.py -v`
4/4 passed.

## Files Changed
- `tests/fixtures/__init__.py` (new)
- `tests/fixtures/lab_runs/minimal_completed_run/lab_run_manifest.json` (new)
- `tests/fixtures/lab_runs/minimal_completed_run/runs/run-seed-42/run_report.json` (new)
- `tests/integration/lab_agent/test_golden_run_fixture.py` (new)
- `pyproject.toml` (e2e_golden marker registered)

## Completion Summary
Golden run fixture added. RegisterSimulationResultWorkflow verified to accept it. Missing and corrupt fixture cases correctly block. Marker registered.
