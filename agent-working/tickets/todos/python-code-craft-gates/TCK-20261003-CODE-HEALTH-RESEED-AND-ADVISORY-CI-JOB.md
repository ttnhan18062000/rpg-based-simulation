---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB

## Title
M4a: Reseed the code-health registry on main and start the soak with an advisory CI job

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The ratchet (`python3 -m tools.code_health check`, `make code-health`) runs only on demand, and its registry was seeded on the python-code-craft branch, so src/ changes merged since then appear as new violations. Reseed the registry on current main (roadmap 6.3 reseed rule) and add an advisory CI job that runs the ratchet on every PR, starting the two-week soak (decision 8.10).

## Scope
- Reseed registries/code_health_exceptions.jsonl on main with `seed --force`, carrying over `reviewed`, `retiring_ticket` and `added_date` for persisting keys; record per-tool row counts before and after in the ticket
- Add a CI job `code-health` named "... (advisory)" that installs with the standard setup-uv step syncing the `lint` group, sets up Node for jscpd (version pinned via the Makefile's JSCPD_VERSION), runs `python3 -m tools.code_health check`, and never fails the PR (`continue-on-error: true`)
- Job summary: new or worse violations, those in files the PR changed listed first; silent-ish on pass (one line)
- Update tests that enumerate CI jobs (e.g. `tests/static/test_ci_uv_install.py` `_LINT_JOBS`, `tests/tools/test_ci_workflow_test_coverage.py`) and list each edit with its reason
- Record the soak start date (this PR's merge date) in the epic and roadmap Section 7
- File TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING's soak end date (start + 14 days) in that ticket

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- Changed-line annotations (TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK)
- Fixing or reviewing registry rows
- A Node lockfile for jscpd (owner decision: jscpd stays report-only)

## Acceptance Criteria
- [ ] Registry reseeded on main; `python3 -m tools.code_health validate` passes; row counts before/after per tool recorded; review fields preserved for persisting keys (test or recorded spot-check)
- [ ] `python3 -m tools.code_health check` exits 0 on the reseed commit
- [ ] test.yml has a `code-health` job that syncs `lint`, cannot fail the workflow, and writes a job summary; the job's wall time on the PR run is recorded and is not above the longest existing PR job, or a split is proposed
- [ ] Tests that enumerate CI jobs pass with the new job included; every edit to an existing test listed with its reason
- [ ] Soak start date recorded in the epic and roadmap; flip ticket carries the end date
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
- TCK-20261002-UV-REMAINING-CI-JOBS
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/agent_working_environment.md
- docs/guides/delivery_process.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY/

## Related Code Areas
- .github/workflows/test.yml
- tools/code_health/
- registries/code_health_exceptions.jsonl
- Makefile (`code-health`, `JSCPD_VERSION`)
- tests/static/test_ci_uv_install.py
- tests/tools/test_ci_workflow_test_coverage.py

## Assumptions / Open Questions
- Ratchet wall time in CI is unknown; Investigate measures `make code-health` locally under a memory cap first (Integration, ~324 s, is the current longest PR job)
- The reseed lands in the same PR as the job so the soak starts from a clean baseline; other sessions merging src/ changes during the soak will add rows only through a later reseed or `tighten`, which is expected advisory noise to review at soak end
- Tests edited here belong to the testing domain; tell its planner before the change lands

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
