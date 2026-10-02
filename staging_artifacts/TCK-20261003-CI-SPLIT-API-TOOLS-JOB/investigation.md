---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CI-SPLIT-API-TOOLS-JOB
artifact_type: investigation
tags: [delivery, testing]
---

# Investigation — TCK-20261003-CI-SPLIT-API-TOOLS-JOB

## Context scan
- `search_docs` and `graphify query` (CI job split, coverage parser): `tools/gate_checks/ci_workflow_test_coverage.py` and the three static CI tests are the only machinery that names the job. Prior tickets `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` and `TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS` explain the per-directory steps being kept.
- Draft by `codebase-planner` from JUnit timings of runs 37032971448 and 36997263937; not investigated by a workflow. Owner decision 2026-10-03 ("yes, do it in this PR"), relayed by codebase-planner, covers the workflow change and the job-name edits in the tests that pin CI.

## Findings
1. **Parser (the ticket's first check).** `_extract_pytest_paths` drops words starting `--ignore=` and then collects words starting `tests/`. A word `--ignore-glob='tests/tools/test_[f-z]*.py'` starts with `--`, so it is not collected: both tools jobs read as exactly `{tests/tools}`. The separate-word form (`--ignore-glob 'tests/...'`) would be collected as a bogus path, so the workflow uses the `=` form, and a test pins both the real jobs and a synthetic job. No parser change was needed.
2. **Equivalence (the ticket's second check), measured on the real tree** with `pytest ... -m "not slow and not extra_slow" --collect-only -q`: the old job's seven paths collect 4,040 IDs (4,069 minus 29 deselected). `tools-a-e` collects 1,469, `tools-f-z` 2,110 (28 deselected), `api-cli-engine` 461 (1 deselected). The three sum to 4,040, the union equals the old set exactly (0 missing, 0 extra), and no ID is collected by two jobs.
3. **Head/base parity** (`_assert_head_base_path_parity`) tokenizes words starting `tests/`, so an `--ignore-glob=` word is invisible to it and the base-branch collection step carries the same ignore glob as its `Run` step without any assertion change.
4. **Pins that name the old job:** `_OUT_OF_SCOPE_JOBS` and `_EXPECTED_SLOW_NEEDS` in `test_ci_narrow_path_filtered_jobs.py`; `_FASTLANE_JOBS` and the expected `needs` block in `test_ci_step_summary_reporting.py` (the job-set test follows `_FASTLANE_JOBS`); one assertion in `test_ci_workflow_test_coverage.py`. JUnit paths stay unique per step because each job uses its own file names.
5. **Live references** outside the workflow: two tool docstrings (`junit_cost_report.py`, `core_rpg_report.py`), two lines in `docs/plans/test_architecture/roadmap.md` and one table in `docs/plans/test_architecture/reference/current_test_system_overview.md`. `tests/unit/tools/test_core_rpg_report.py` asserts the literal `api-tools` appears in the report limits, so the new wording says "the three jobs split from the former `api-tools` job", which is accurate and needs no test edit.
6. **Left alone as historical:** done tickets, stored artifacts, parity-ledger evidence text, `docs/plans/archive/`, the audit in `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md`, the decision record `docs/architecture/visual_asset_foundation_adr.md` D7, and one comment in `tests/tools/test_parity_index.py` (editing a test comment is outside "job names and lists").
7. **File names:** every file in `tests/tools` matching `test_*.py` starts `test_` plus a lowercase letter, so none falls outside the two globs today; a file that did would run in both jobs (tested on a scratch directory with `test_9digits.py` and `test_Upper.py`).
