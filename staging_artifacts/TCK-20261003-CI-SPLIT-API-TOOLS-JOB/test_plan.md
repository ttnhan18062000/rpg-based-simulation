---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CI-SPLIT-API-TOOLS-JOB
artifact_type: test_plan
tags: [delivery, testing]
---

# Test Plan — TCK-20261003-CI-SPLIT-API-TOOLS-JOB

## Proof Plan
- level: static workflow checks, a collect-only equivalence run, and a real CI run
- proof kind: new structural tests; measured ID-set comparison; GitHub Actions run of the three jobs
- oracle source: the old job's collected test IDs and its reporting steps
- expected effect: same 4,040 tests run, split across three parallel jobs; each reports like the old one
- selected commands:

| Check | Command | Expected |
|---|---|---|
| Equivalence | `pytest <old seven paths> -m "not slow and not extra_slow" --collect-only -q` versus the three new commands | union equals old; no overlap |
| New structural tests | `pytest tests/tools/test_ci_split_tools_jobs.py` | pass (13) |
| Pinned CI tests | `pytest tests/static tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_dashboard_makefile_targets.py` | pass |
| Docstring consumer | `pytest tests/unit/tools/test_core_rpg_report.py tests/docs` | pass |
| Coverage gate | `python3 tools/gate_checks/ci_workflow_test_coverage.py` | exit 0, no uncovered directory |
| Real run | open PR #288 run: the three jobs, their Job summary and JUnit artifacts, durations | all green; recorded in the ticket |
