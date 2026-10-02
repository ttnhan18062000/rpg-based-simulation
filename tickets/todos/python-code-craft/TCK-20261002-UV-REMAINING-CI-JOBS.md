---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261002-UV-REMAINING-CI-JOBS
phase: open
date: 2026-10-02
tags: [delivery]
---

# TCK-20261002-UV-REMAINING-CI-JOBS

## Title
M2c: Migrate the remaining CI jobs and the Makefile install recipe to uv sync

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Third part of finishing the uv adoption. After TCK-20261002-UV-FIRST-CI-JOB has one job green on `uv sync`, move every other Python job in `.github/workflows/test.yml` and the `install-py` Makefile recipe to uv, so dependencies are installed one way everywhere. This ticket was not produced by the scoping run: it was written by hand on 2026-10-02 after the owner decided that tickets in this batch may edit the existing tests that pin CI and the Makefile (roadmap decision 8.11). It has had less investigation than its siblings; the implementer's Investigate phase must confirm the facts below.

## Scope
- Switch the install step of every remaining Python job in `.github/workflows/test.yml` from `pip install -r requirements.txt` to `uv sync` against the committed `uv.lock`, using the same setup the first migrated job settled on (action version, `--no-install-project` choice, cache settings)
- Include the `migration-lanes` and `slow` jobs, and update the expected YAML that `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` in `tests/static/test_ci_step_summary_reporting.py` pins for them, changing only the install and cache lines
- Change the `install-py` Makefile recipe to the uv equivalent and update the pinned recipe string in `tests/tools/test_dashboard_makefile_targets.py`
- Fold the separate `pip install mypy` step of the `typecheck` job into the dev dependency group, without changing what the mypy step runs or whether it blocks
- Review the `PERF_RE` / `MIG_RE` path filters in `test.yml`, which trigger on `requirements.txt` but not on `pyproject.toml` or `uv.lock`, and extend them if a dependency change could otherwise skip those jobs
- Update `docs/guides/delivery_process.md`, `docs/testing/migration_ci_lanes.md` and `docs/guidelines/agent_working_environment.md` wherever they give pip install instructions for CI or local setup
- Decide and record whether `requirements.txt` stays as a generated export or is removed; removal is allowed only if nothing in the repo still reads it

## Out of Scope
- Any change to what a job tests, its triggers (other than the dependency path filters above), or its reporting steps
- Making mypy blocking or otherwise changing the mypy gate (roadmap M4; pinned by INFRA-TYPE-001 and `tests/static/test_typecheck_gate_configured.py`)
- `requirements-knowledge.txt` and the `.venv-knowledge` setup
- The `frontend` job and any Node tooling
- Adding ruff, complexipy or other M3 tools (TCK-20261002-CODE-HEALTH-TOOL-CONFIG)
- Any file under src/, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Weakening any assertion in the edited tests beyond the install and cache lines they pin

## Acceptance Criteria
- [ ] No Python job in `.github/workflows/test.yml` runs `pip install -r requirements.txt` (`grep -c` returns 0), and every Python job installs with `uv sync`
- [ ] The `migration-lanes` and `slow` jobs differ from their previous YAML only in the install and cache lines, and `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` passes against the updated expected YAML
- [ ] `make install-py` installs through uv, and `tests/tools/test_dashboard_makefile_targets.py` passes with its pinned recipe string updated to match
- [ ] The `typecheck` job has no separate `pip install mypy` step, `test.yml` still has a step named mypy that runs `mypy src/`, and `pytest tests/static/test_typecheck_gate_configured.py` passes
- [ ] No job's install log shows torch or sentence-transformers, and `pytest tests/static/test_ci_requirements_no_ml_stack.py` passes or is updated with a recorded reason if `requirements.txt` is removed
- [ ] `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py` passes; every edit to an existing test file is listed in the ticket with the reason
- [ ] Every job is green on a real PR run, and the run link is recorded in the ticket
- [ ] The three docs named in Scope no longer instruct `pip install -r requirements.txt` for CI or first-time setup, or state plainly that the file is a generated export
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, no path under .claude/ and not CLAUDE.md

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-UV-DECLARE-AND-LOCK
- TCK-20261002-UV-FIRST-CI-JOB
- TCK-20260702-CI-REQUIREMENTS-SPLIT
- TCK-20260823-CI-STEP-SUMMARY-REPORTING
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
- TCK-20260623-TYPE-CHECKER

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/agent_working_environment.md
- docs/guides/delivery_process.md
- docs/testing/migration_ci_lanes.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- Makefile
- uv.lock
- pyproject.toml
- requirements.txt
- tests/static/test_ci_step_summary_reporting.py
- tests/static/test_ci_narrow_path_filtered_jobs.py
- tests/static/test_ci_requirements_no_ml_stack.py
- tests/static/test_typecheck_gate_configured.py
- tests/tools/test_dashboard_makefile_targets.py
- tests/tools/test_ci_workflow_test_coverage.py

## Assumptions / Open Questions
- Depends on TCK-20261002-UV-FIRST-CI-JOB being closed with a green PR run; this ticket must not start before that
- Measured 2026-10-02: `test.yml` has 14 occurrences of `pip install -r requirements.txt` across its Python jobs (job list: unit-core-world, unit-gameplay, unit-infra, integration, api-tools, agent-orchestration, simulation-quality, arch-docs, changed-files, perf-cert-arena, scenario-lane, migration-lanes, typecheck, simq-grade-drift, slow); which jobs hold which occurrence was not mapped
- `tests/tools/test_dashboard_makefile_targets.py` line 22 pins `install-py` as `pip install -r requirements.txt`; `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` compares the two jobs against `_EXPECTED_MIGRATION_LANES_YAML` and `_EXPECTED_SLOW_YAML`. Other tests that pin install lines may exist and were not searched for
- The tests edited here belong to the `testing` domain. The owner approved the edits for this batch; the testing planner (`test-architecture-reviewer`) should be told before the change lands
- Whether `docs/guides/delivery_process.md` and `docs/testing/migration_ci_lanes.md` contain pip install instructions was not confirmed (a quick search found none in the first and did not check the second fully)
- Other domains' worktrees build their environments from `requirements.txt` today; removing the file would affect them, which is why keeping it as a generated export is the default
- A green run requires a push and PR, which the user drives; this ticket cannot close on local evidence alone
- Layer `testing` and tag `delivery` follow the sibling ticket TCK-20261002-UV-FIRST-CI-JOB

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
