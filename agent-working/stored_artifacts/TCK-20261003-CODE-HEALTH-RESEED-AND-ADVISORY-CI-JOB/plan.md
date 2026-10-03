---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB

Branch `python-code-craft-gates` (one PR for the five-ticket batch). No `src/`, `.claude/`, `CLAUDE.md` edits.

1. **Reseed** (`registries/code_health_exceptions.jsonl`): record per-tool counts before (ruff 2892, line_count 283, complexipy 384, jscpd 58 = 3617). Run `python3 -m tools.code_health scan` once under the memory cap with the main `.venv` on PATH, then `seed --from <scan dir> --force`. Record counts after; spot-check that `reviewed`, `retiring_ticket` and `added_date` persist for keys present in both (test below). Confirm `validate` passes and `check --from <scan dir>` exits 0.
2. **Changed-files-first summary** in `tools/code_health/` (not src/): `ratchet.format_summary(result, changed_files)` returns Markdown: on pass one line; on failure NEW/WORSE entries in changed files first, then the rest (capped, reusing `DEFAULT_REPORT_LIMIT`). `check` gains `--summary-for FILE` (a list of changed paths, one per line) and `--summary-out PATH` (default stdout); exit codes unchanged. No new dependency.
3. **CI job** `code-health` in `.github/workflows/test.yml`, name "Code health (advisory)": `actions/checkout@v5`; `astral-sh/setup-uv@v10.2.0` (same inputs) and `uv sync --locked --no-install-project` (lint group kept); `actions/setup-node@v4` node 20 (no npm cache); a step that fetches the PR base and writes `git diff --name-only origin/<base>...HEAD` to `/tmp/changed.txt` (PR only; empty file otherwise); the check step `python3 -m tools.code_health check --summary-for /tmp/changed.txt --summary-out "$GITHUB_STEP_SUMMARY"` with `continue-on-error: true` on the step and on the job, so a failing check, a missing tool or an `npx` failure never fails the workflow. Runs on PRs and on push to main; no `needs`, not behind the path-filter gate (the ratchet reads all of src/).
4. **Tests**: add `code-health` to `expected_job_names` in `test_ci_step_summary_reporting.py`; add it to `_LINT_JOBS` in `test_ci_uv_install.py`; run `test_ci_narrow_path_filtered_jobs.py` and `test_ci_workflow_test_coverage.py` and adjust only if they enumerate jobs. New tests: `format_summary` (pass is one line; changed files listed first; cap respected; empty changed list), CLI flags (`--summary-for/--summary-out`, exit code unchanged), registry reseed carry-over of review fields (fixture), and a static test that the job exists, is advisory (`continue-on-error` on job and check step) and syncs `lint`. Every edit to an existing test is listed in the ticket with its reason.
5. **Docs**: `docs/guidelines/python_code_standard.md` / `agent_working_environment.md` wherever they say the ratchet is "on demand; not run in CI" (also the module docstring in `tools/code_health/__main__.py` and `ratchet.py`, and the Makefile `code-health` help text).
6. **Soak start**: mark "date of batch PR merge" in the epic, roadmap Section 7 and the flip ticket now (planner instruction); the closure commit writes the real date and the end date (start + 14 days).
7. **Measure** `check` wall time once the machine is quiet; record it. If it exceeds the longest PR job (Integration, ~324 s), propose a split in the ticket instead of shipping silently.
8. **Close** with the batch: one closure commit after the green PR run (run link recorded), pushed to the same PR before the owner merges.

## Scope guards
No check becomes required or blocking. No registry row is fixed or reviewed. jscpd stays report-only and unlocked. The reseed is the only registry edit.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| Reseed, validate, counts, review fields preserved | 1, 4 |
| `check` exits 0 on the reseed commit | 1 |
| test.yml job syncs lint, cannot fail workflow, writes summary, wall time recorded | 2, 3, 7 |
| Job-enumerating tests pass, edits listed | 4 |
| Soak start/end recorded | 6, 8 |
| Green PR run link | 8 |
| No src/.claude/CLAUDE.md in diff | scope guards |
