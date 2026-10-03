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
INPROGRESS

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
- Remove the separate `pip install mypy` step of the `typecheck` job (`mypy` is already in the `dev` group since TCK-20261002-UV-DECLARE-AND-LOCK), without changing what the mypy step runs or whether it blocks
- Update `test_every_new_job_still_installs_with_pip_until_the_uv_migration` in `tests/tools/test_ci_split_tools_jobs.py` so it pins the uv install for `tools-a-e`, `tools-f-z` and `api-cli-engine` instead of pip
- Move `ruff` and `complexipy` out of `dev` into their own dependency group `lint`, and add `[tool.uv] default-groups = ["dev", "lint"]` so a plain local `uv sync` and the `uv export` command install exactly what they do today. In CI, only the jobs that collect tests invoking those tools sync the `lint` group; every other job passes `--no-group lint`
- Change the `pip install -r requirements.txt` line in `make.bat` the same way as the `install-py` recipe, or record in the ticket why it stays
- Replace the comment above the `simulation-quality` install step, which says the other jobs stay on pip
- Add `pyproject.toml` and `uv.lock` to the `PERF_RE` and `MIG_RE` path filters in `test.yml` (they list only `requirements.txt` today; `tools/test_architecture/scenario_lane_paths.py` already lists all three), and update any test that pins those expressions
- Update `docs/guides/delivery_process.md`, `docs/testing/migration_ci_lanes.md` and `docs/guidelines/agent_working_environment.md` wherever they give pip install instructions for CI or local setup
- Keep `requirements.txt` as a generated export (planner decision 2026-10-03, see Assumptions): it must still contain `ruff` and `complexipy`, and regenerating it with the documented `uv export` command must reproduce the committed file

## Out of Scope
- Any change to what a job tests, its triggers (other than the dependency path filters above), or its reporting steps
- Making mypy blocking or otherwise changing the mypy gate (roadmap M4; pinned by INFRA-TYPE-001 and `tests/static/test_typecheck_gate_configured.py`)
- `requirements-knowledge.txt` and the `.venv-knowledge` setup
- The `frontend` job and any Node tooling
- Adding new code-health tools or changing the pinned versions of ruff and complexipy (moving the two between dependency groups is in scope)
- Removing `requirements.txt`
- Adding a CI job that runs `make code-health` (roadmap M4)
- Any file under src/, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Weakening any assertion in the edited tests beyond the install and cache lines they pin

## Acceptance Criteria
- [ ] No Python job in `.github/workflows/test.yml` runs `pip install -r requirements.txt` (`grep -c` returns 0), and every Python job installs with `uv sync`
- [ ] The `migration-lanes` and `slow` jobs differ from their previous YAML only in the install and cache lines, and `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` passes against the updated expected YAML
- [ ] `make install-py` installs through uv, and `tests/tools/test_dashboard_makefile_targets.py` passes with its pinned recipe string updated to match
- [ ] `tests/tools/test_ci_split_tools_jobs.py` passes with its install pin changed from pip to uv for the three split jobs
- [ ] `ruff` and `complexipy` are declared only in the `lint` group; `uv lock --check` passes; `uv export --frozen --no-hashes --no-emit-project` reproduces the committed `requirements.txt`, which still lists both tools
- [ ] On the PR run, the install log of a job that passes `--no-group lint` shows neither ruff nor complexipy, and no test in any job fails or is skipped because one of the two tools is missing (the tests in `tests/tools/test_code_health_*.py` and `tests/tools/test_codebase_health_snapshot_craft.py` still run and pass)
- [ ] `PERF_RE` and `MIG_RE` match `pyproject.toml` and `uv.lock`, and `pytest tests/static/test_ci_narrow_path_filtered_jobs.py` passes
- [ ] The `typecheck` job has no separate `pip install mypy` step, `test.yml` still has a step named mypy that runs `mypy src/`, and `pytest tests/static/test_typecheck_gate_configured.py` passes
- [ ] No job's install log shows torch or sentence-transformers, and `pytest tests/static/test_ci_requirements_no_ml_stack.py` passes or is updated with a recorded reason if `requirements.txt` is removed
- [ ] `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py` passes; every edit to an existing test file is listed in the ticket with the reason
- [ ] Every job is green on a real PR run, and the run link is recorded in the ticket
- [ ] The three docs named in Scope no longer instruct `pip install -r requirements.txt` for CI or first-time setup, or state plainly that the file is a generated export; `docs/guidelines/agent_working_environment.md` no longer says CI installs with pip and describes the `lint` group; the dependency path list in `docs/testing/migration_ci_lanes.md` matches the new `MIG_RE`
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
- From the review of `TCK-20261002-CODE-HEALTH-TOOL-CONFIG` (2026-10-02): `ruff` and `complexipy` are in the `dev` group, so every job that syncs or pip-installs the export installs them although only one future job needs them. When jobs move to uv, put the code-health tools in their own dependency group (for example `lint`) that test jobs do not sync, and regenerate the export accordingly.
- **Planner re-check 2026-10-03, after PR #288 merged** (search tooling was degraded: no `knowledge-search` MCP, no knowledge index or graph in the worktree; facts below come from direct reads of the files named):
  - The job list above is out of date. `api-tools` was split by TCK-20261003-CI-SPLIT-API-TOOLS-JOB. `test.yml` now has 15 jobs with `pip install -r requirements.txt` (unit-core-world, unit-gameplay, unit-infra, integration, tools-a-e, tools-f-z, api-cli-engine, agent-orchestration, arch-docs, perf-cert-arena, scenario-lane, migration-lanes, typecheck, simq-grade-drift, slow) and one already on uv (simulation-quality). `changed-files` and `frontend` install no Python dependencies and are not touched
  - The setup to copy is the one `simulation-quality` uses: `astral-sh/setup-uv@v10.2.0` with `version: "0.11.2"`, `python-version: "3.13"`, `activate-environment: true`, `enable-cache: true`, then `uv sync --locked --no-install-project`
  - Several jobs run a "Base branch test collection" step with `cd /tmp/base-checkout && pytest ...`. Confirm on the PR run that the activated environment is still found from that directory in every such job
  - Pins found beyond the two this ticket named: `tests/tools/test_ci_split_tools_jobs.py` line 103 (asserts the pip line, must change); `tests/tools/test_delivery_ci_triage_classifier.py` line 39 (a workflow fixture string, expected to stay); `tests/unit/tools/test_scenario_lane_paths.py` (already covers the uv files). The implementer's Investigate phase must still search for others
  - `requirements.txt` stays: `tests/static/test_ci_requirements_no_ml_stack.py` and `tests/tools/test_evidence_cache_identity_contract.py` read it, `make.bat` installs from it, and other domains' worktrees build their environments from it. The export keeps the `lint` tools because a pip-built environment runs the code-health tests too
  - The tests that invoke ruff or complexipy are `tests/tools/test_code_health_*.py` and `tests/tools/test_codebase_health_snapshot_craft.py`, which fall in `tools-a-e`. Investigate must confirm whether `slow` or any other job also collects them before choosing which jobs pass `--no-group lint`
  - Branch: this ticket goes on a fresh branch cut from `main` with its own PR. `python-code-craft` was squash-merged as PR #288 and must not be pushed to again
  - The testing planner (`test-architecture-reviewer`) still has to be told about the edits to tests in its domain before this lands; it was not reachable for the previous batch

## Implementation Notes
- `lint` dependency group (`ruff==0.16.10`, `complexipy==8.0.1`) split out of `dev`; `[tool.uv] default-groups = ["dev", "lint"]` keeps plain `uv sync` and the `uv export` output unchanged. `uv.lock` diff is the group move only (no package version changed); the export reproduces `requirements.txt` byte-for-byte (only the header comment's output path differed in a scratch export).
- All 15 pip jobs now use the `simulation-quality` setup (setup-uv@v10.2.0, uv 0.11.2, `uv sync --locked --no-install-project`). Only `tools-a-e` syncs `lint`; every other job, including the already-migrated `simulation-quality`, passes `--no-group lint`. Only `tests/tools/test_code_health_*.py` and `test_codebase_health_snapshot*.py` need the tools; none is marked `slow`, so `slow` does not collect them.
- `typecheck`: `pip install mypy` step deleted (mypy is in `dev`); the `mypy` step is untouched.
- `PERF_RE` and `MIG_RE` gain `pyproject.toml` and `uv.lock`. Consequence accepted by the planner: any `pyproject.toml` edit, including ruff configuration, now runs `perf-cert-arena` and `migration-lanes` (stated in `docs/testing/migration_ci_lanes.md`). `tests/static/test_ci_narrow_path_filtered_jobs.py` does not pin the expressions' literal text, only derived coverage; a test was added, no existing assertion edited.
- `make install-py` and `make.bat` run plain `uv sync` (no `--system-certs`; `UV_SYSTEM_CERTS=1` documented for TLS-intercepted machines). It now also installs the project editable, which pip did not; documented.
- Negative control (scratch env built with `uv sync --locked --no-install-project --no-group lint`; neither tool installed): the 9 code-health tests that scan **fail** with `ToolUnavailableError: complexipy not found: install the project environment (uv sync)`; none skips. So a misplaced `--no-group lint` cannot pass silently.

## Test Summary

## Files Changed
Config and CI: `pyproject.toml`, `uv.lock`, `.github/workflows/test.yml` (15 install steps; `simulation-quality` is an edit to the already-migrated job, flag `--no-group lint` only; mypy step; PERF_RE/MIG_RE; comment), `Makefile` (`install-py`), `make.bat`. `requirements.txt` unchanged (regenerated, identical).

Edits to existing tests (for forwarding to `test-architecture-reviewer`; install and cache lines only, no assertion weakened):
- `tests/static/test_ci_step_summary_reporting.py`: `_EXPECTED_MIGRATION_LANES_YAML` and `_EXPECTED_SLOW_YAML` setup-python/pip lines replaced by the setup-uv/`uv sync --locked --no-install-project --no-group lint` lines, because those two jobs moved to uv.
- `tests/tools/test_ci_split_tools_jobs.py`: `test_every_new_job_still_installs_with_pip_until_the_uv_migration` renamed `test_every_new_job_installs_with_uv_from_the_lockfile`; pins the uv sync line (with or without `--no-group lint`), the setup-uv step and absence of pip, because the three split jobs moved to uv.
- `tests/tools/test_dashboard_makefile_targets.py`: `install-py` recipe snapshot `pip install -r requirements.txt` -> `uv sync`, because the recipe changed.

Additive tests: `tests/static/test_ci_uv_install.py` (new), one test appended to each of `tests/static/test_ci_narrow_path_filtered_jobs.py` (PERF_RE/MIG_RE match pyproject.toml, uv.lock) and `tests/static/test_typecheck_gate_configured.py` (no `pip install mypy`).

Docs: `docs/guidelines/agent_working_environment.md`, `docs/guides/delivery_process.md`, `docs/testing/migration_ci_lanes.md`.

## Completion Summary
