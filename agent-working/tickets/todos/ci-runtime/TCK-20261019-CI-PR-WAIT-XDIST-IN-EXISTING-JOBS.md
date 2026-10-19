---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS

## Title
The three critical-path test.yml jobs (Integration, Tools f–z, API/CLI/engine) run their tests in parallel with pytest-xdist inside the job, after an audit shows the tests are safe to parallelise. No jobs are added.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of TCK-20261019-CI-RUNTIME-EPIC. The median PR wall time is 9.5 min. It is set by Integration (8.4 min median, p90 9.5), Tools f–z (6.7 min) and API/CLI/engine (6.3 min), each a single pytest process on a 4-vCPU `ubuntu-latest` runner. The baseline is in the epic's investigation.md.

Splitting jobs is not an option: Tests already starts 21 jobs against the free plan's 20-concurrent-job limit, so more jobs would queue (lead-planner-u24, 2026-10-19). Parallelising inside a job costs no concurrency.

## Scope
1. **Shared-state audit first** (investigation.md, before any workflow change). For every test in the three jobs, find shared mutable state. At minimum this covers:
   - `data/runs/` and `reports/` (including `reports/release_proof/`);
   - `data/calibration/`;
   - fixed tmp paths, ports, env vars and `os.chdir`;
   - module-level caches and registries;
   - the determinism and replay tests (two runs compared within one process, golden files).
   Each finding is fixed, or the test is grouped onto one worker (`xdist_group` with `--dist loadgroup`), or it stays serial in a separate step of the same job. Nothing is skipped or deselected.
2. Add `pytest-xdist` to the dev dependencies (pinned in `uv.lock`). Run the three jobs with `-n auto --dist loadgroup` (or a measured fixed `-n`).
3. **Before touching Tools f–z, send agent-working-planner an fyi.** The tests under `tests/tools/` are mostly their code, and #647 (agent-working-implementer, open) changes how tools tests are isolated. If #647 is still open, rebase onto it once it lands, or do Integration and API first and Tools f–z after.
4. The JUnit XML, the job summary and the base-branch collect-only diff step keep working under xdist. Check that `ci_junit_summary.py` reads the merged XML.
5. Optional, only if it keeps the net job count at or below today's: merge two tiny lanes (each under 1 min, for example Simulation quality and Agent orchestration). Record the choice either way.

## Out of Scope
- New jobs, or splitting a job into several.
- Changing which tests run, or any marker or deselection.
- The slow-regression lane, the SimQ drift job, and other workflows.

## Acceptance Criteria
- [ ] AC1: investigation.md lists the shared-state audit per job, with each finding and how it was handled (fixed, grouped or serial).
- [ ] AC2: the collected-test count per job is identical before and after, from `--collect-only -q` counts quoted in the Test Summary. No test is skipped, xfailed or deselected by this change.
- [ ] AC3: each of the three jobs passes 3 consecutive CI runs on the PR. Use re-runs to show there is no order-dependent flake, and quote the run ids.
- [ ] AC4: the median wall time of the three jobs over those runs is reported against the baseline (8.4 / 6.7 / 6.3 min). Target: the slowest of them at or below 5 min. A shortfall is reported, not hidden.
- [ ] AC5: the job count in test.yml does not grow.
- [ ] AC6: agent-working-planner's fyi was sent before the Tools f–z change, with its reply or "no reply" recorded.
- [ ] AC7: **lead-planner-u24 reviews the PR by comment**, in addition to testing-planner, before the user merges. Record the comment link.

## Related Tickets
- TCK-20261019-CI-RUNTIME-EPIC (parent)
- TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT (the base-branch collection step)

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-CI-RUNTIME-EPIC/investigation.md (baseline)

## Related Code Areas
- .github/workflows/test.yml (jobs `integration`, `tools-f-z`, `api-cli-engine`)
- pyproject.toml, uv.lock
- tests/conftest.py (resource budget, run-dir creation)
- tools/ci_junit_summary.py

## Assumptions / Open Questions
- The runner is 4 vCPU (ubuntu-latest, public repo). `-n auto` is the starting point; if memory pressure shows, use a measured `-n`.
- The local resource budget in conftest (60 s/8 GB) applies per test and must still apply per worker.

- **agent-working-planner's scan of tests/tools, 2026-10-19 (input to the audit, not a substitute for it):**
  - There are no raw `os.chdir` calls and no `os.environ` writes; env changes go through monkeypatch or a subprocess env.
  - The fixed `/tmp` strings are never written to.
  - `test_disk_warning.py` uses cwd=tmp_path, so it is isolated. `test_generate_registry.py` only reads the real REGISTRY.
  - To look at: modules loaded via sys.path insertion plus module-level `_REPO_ROOT` / tools/agent-monitoring path constants. These are safe under process workers but matter for any in-process cache reset.
  - Rebase Tools f–z onto #647.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
