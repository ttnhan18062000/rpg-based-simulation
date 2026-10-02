---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261002-UV-FIRST-CI-JOB
phase: open
date: 2026-10-02
tags: [delivery]
---

# TCK-20261002-UV-FIRST-CI-JOB

## Title
M2b: Migrate exactly one CI job to uv sync

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Second half of finishing the uv adoption: CI installs with pip install -r requirements.txt in every job today. The author wants exactly one CI job migrated to uv sync first, with the rest following only after it is green, so a uv problem cannot break CI for the many sessions working in src/ (roadmap decision 8.9). It must satisfy the CI static tests under tests/static/, keep the knowledge-search stack out of CI (TCK-20260702-CI-REQUIREMENTS-SPLIT), and keep tests/static/test_no_hardcoded_venv_interpreter_path.py passing. The shared constraints apply: no src/ edits, no simulation behaviour change, no tests/ changes beyond tests for new tooling, no edits to governing files or the agent-working domain.

## Scope
- Pick one Python job in .github/workflows/test.yml that is not the migration-lanes or slow job and switch its install step from 'pip install -r requirements.txt' to 'uv sync' against the committed uv.lock
- Obtain uv in that job with the astral-sh/setup-uv action, pinned to a version, and add that action to the _PRE_EXISTING_USES allowlist in tests/static/test_ci_step_summary_reporting.py (owner decision 2026-10-02: tickets in this batch may edit existing tests that pin CI and the Makefile; no other assertion in that test is weakened)
- Ensure the migrated job's uv sync never selects the knowledge extra or group, and decide and record whether it uses --no-install-project
- Leave every other job on 'pip install -r requirements.txt'
- Record the green PR run of the migrated job in the ticket

## Out of Scope
- Migrating any second CI job; the remaining jobs follow in TCK-20261002-UV-REMAINING-CI-JOBS only after this one is green
- The migration-lanes and slow jobs (pinned verbatim by test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket; moved by TCK-20261002-UV-REMAINING-CI-JOBS)
- Adding any new 'uses:' action other than astral-sh/setup-uv
- Changing the PERF_RE / MIG_RE path filters in test.yml
- Changing the Makefile install-py recipe or the mypy step (M4)
- Removing requirements.txt
- Any file under src/, any existing test file under tests/ other than the allowlist entry in tests/static/test_ci_step_summary_reporting.py, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/

## Acceptance Criteria
- [ ] Exactly one job in .github/workflows/test.yml installs via 'uv sync' (grep -c 'uv sync' returns 1) and every other Python job still runs 'pip install -r requirements.txt'
- [ ] The migrated job is green on a real PR run, and the run link is recorded in the ticket, before any follow-up ticket migrates another job
- [ ] The only new 'uses:' entry in test.yml is astral-sh/setup-uv, pinned to a version and present only in the migrated job; _PRE_EXISTING_USES gains exactly that one entry; the migration-lanes and slow job YAML is byte-identical to before
- [ ] The migrated job's install step does not select the knowledge extra or group: no torch or sentence-transformers install appears in its log
- [ ] 'pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py' passes, and the only edit to an existing test file is the one allowlist entry in tests/static/test_ci_step_summary_reporting.py
- [ ] test.yml still has a step named mypy and 'pytest tests/static/test_typecheck_gate_configured.py tests/static/test_no_hardcoded_venv_interpreter_path.py' passes
- [ ] 'git diff --stat <base>...HEAD' lists no path under src/, no path under .claude/ and not CLAUDE.md

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-UV-DECLARE-AND-LOCK
- TCK-20261002-UV-REMAINING-CI-JOBS
- TCK-20260702-CI-REQUIREMENTS-SPLIT
- TCK-20260823-CI-STEP-SUMMARY-REPORTING
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS
- TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH
- TCK-20260817-HOTFIX-MAKEFILE-PYTHON-DISCOVERY-BROKEN-ON-CI
- TCK-20260619-P0-CI-AUTOMATION
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
- uv.lock
- pyproject.toml
- requirements.txt
- Makefile
- tests/static/test_ci_step_summary_reporting.py
- tests/static/test_ci_narrow_path_filtered_jobs.py
- tests/static/test_ci_requirements_no_ml_stack.py
- tests/static/test_typecheck_gate_configured.py
- tests/static/test_no_hardcoded_venv_interpreter_path.py
- tests/tools/test_ci_workflow_test_coverage.py
- tests/tools/test_dashboard_makefile_targets.py
- docs/guides/delivery_process.md
- docs/testing/migration_ci_lanes.md

## Assumptions / Open Questions
- Depends on TCK-20261002-UV-DECLARE-AND-LOCK: uv sync from today's pyproject.toml would fail on import
- Owner decision 2026-10-02 (roadmap decision 8.11): tickets in this batch may edit existing tests that pin CI and the Makefile. This ticket was scoped before that decision with 'pip install uv'; it now uses astral-sh/setup-uv and extends the allowlist. The current version of that action and its caching inputs were not checked during scoping
- 'uv sync' installs the project as editable by default while CI today has no editable install (pytest uses pythonpath='.'); whether to pass --no-install-project is an open choice to settle in the plan
- Which job goes first is not fixed by the brief; any job other than migration-lanes and slow qualifies
- The 'rest of the jobs' migration is TCK-20261002-UV-REMAINING-CI-JOBS: migration-lanes and slow are pinned verbatim, including 'cache: pip' and the pip install line, and that ticket updates the pinning tests
- A green run requires a push and PR, which the user drives; this ticket cannot close on local evidence alone
- Layer `testing` chosen (CI workflow / test infrastructure); no registered layer names CI or build tooling specifically
- Tag relevance: `delivery` — registered note centres on the git/PR/CI delivery lane and tools/delivery/; this ticket changes a CI job's install step in .github/workflows/test.yml, which is the CI part of that lane but not tools/delivery/

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
