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
INPROGRESS

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
- Reseed (development reseed on this branch; planner condition B: it is re-run as the last step before the batch push, after merging origin/main, and both reseeds' counts are recorded here). Reseed 1 counts, before and after: ruff 2892 -> 2892, line_count 283 -> 283, complexipy 384 -> 384, jscpd 58 -> 58; total 3617 -> 3617. Check on the old registry first: 9 rows WORSE (line_count in `src/observability/event_extractor.py` and `event_shapers.py`, from src changes merged since the first seed), 3608 unchanged. After `seed --force`: `validate` valid (0 problems), `check` exit 0 (3617 unchanged). Review data: all 3617 keys persist and all 3617 `added_date` values are kept; no row was `reviewed` yet, so none was lost (carry-over is also unit-tested in `test_code_health_ratchet_registry.py::test_reseed_carries_over_review_data_...`). The diff of `registries/code_health_exceptions.jsonl` is 9 changed lines (the 9 ceilings).
- `tools/code_health` gains `ratchet.format_summary` and `check --summary-for/--summary-out/--annotate` (exit codes unchanged). A pass is one Markdown line; on a failure NEW/WORSE entries in files the PR changed are listed first, then the rest, each capped. With `--annotate`, a failing check also prints one `::warning::code-health: N new/worse violations (advisory); see job summary` line (planner condition A), so a green job still surfaces the result in the PR checks view.
- CI job `code-health` ("Code health (advisory)") in test.yml: checkout with `fetch-depth: 0`, setup-uv + `uv sync --locked --no-install-project` (lint kept), `actions/setup-node@v4` node 20, a step writing the PR's changed paths (`git diff --name-only base...head`), then the check step. **The step-level `continue-on-error` carries the behaviour**: a ratchet exit of 1 or 2 leaves the job green and the result lands in the job summary and the warning annotation. The job-level `continue-on-error: true` is only a backstop for setup failures (a job-level setting alone would still show a red check on every PR during the soak, which CI-triage agents would read as "CI failing"). There is no job-level `if` and no `needs`, so the job also runs on push to main, on the nightly schedule and on workflow_dispatch (a free trend point).
- Node version (planner condition C): 20, the same as the `frontend` job; jscpd 5.4.0 declares `engines: node >=18`, so 20 satisfies it.
- Wall time: `python3 -m tools.code_health check` end to end takes 9 s locally (scan 12 s measured separately, under load average about 10) at a 2 GB memory cap. In CI add `uv sync` and the first `npx` fetch of jscpd; the authoritative number comes from the PR run (Integration, about 324 s, is the longest existing PR job).
- Docs (planner condition D): `docs/guidelines/python_code_standard.md` now says "advisory in CI (soak)" for configured tools; the Makefile `code-health` help text, the `tools/code_health/__main__.py` and `ratchet.py` docstrings, and `docs/guidelines/agent_working_environment.md` follow.
- Soak start is marked "date of batch PR merge" in the epic, roadmap Section 7 and the flip ticket; the closure commit writes the real dates (start, and end = start + 14 days).

## Test Summary

## Files Changed
Code: `tools/code_health/ratchet.py`, `tools/code_health/__main__.py`. Registry: `registries/code_health_exceptions.jsonl` (reseed). CI: `.github/workflows/test.yml` (new `code-health` job). Docs and tickets: `docs/guidelines/python_code_standard.md`, `docs/guidelines/agent_working_environment.md`, `Makefile` (help text), `docs/plans/codebase_health/python_code_craft_roadmap.md`, the epic and the flip ticket (soak placeholders).

Edits to existing tests (for the testing planner; no assertion weakened):
- `tests/static/test_ci_step_summary_reporting.py`: `code-health` added to `expected_job_names`, and the assertion message reworded (it said "this ticket must not add a new CI job", which belonged to an earlier ticket). Reason: the job set is pinned exactly and a job was added.
- `tests/static/test_ci_uv_install.py`: `_LINT_JOBS` now `{"tools-a-e", "code-health"}`. Reason: the new job runs the ratchet itself and must sync `lint`.
Added tests: `tests/tools/test_code_health_ci_summary.py` (new: summary format, cap, ordering, CLI flags, exit codes unchanged, warning only on failure, summary appended not overwritten) and `test_code_health_job_is_advisory_and_keeps_the_ratchet_step_non_blocking` in `tests/static/test_ci_uv_install.py`. `test_ci_narrow_path_filtered_jobs.py` and `test_ci_workflow_test_coverage.py` needed no change (the new job runs no pytest and is not in the gated-job lists).

## Completion Summary
