---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-FIRST-CI-JOB
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261002-UV-FIRST-CI-JOB

## Context scan

- `search_docs` ("CI workflow test.yml job install step uses allowlist"): `TCK-20260702-CI-REQUIREMENTS-SPLIT` and the D18 CI audit. No earlier uv-in-CI ticket.
- `graphify query`: `tests/static/test_ci_step_summary_reporting.py` (`_jobs()`, `_pytest_steps()`) is the test that pins the workflow's `uses:` set and the migration-lanes and slow jobs.

## Findings

1. **`test.yml` has 14 Python jobs**, all installing with `pip install -r requirements.txt` after `actions/setup-python@v6` with `cache: pip`. Pinned verbatim by `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`: `migration-lanes` and `slow`.
2. **The allowlist** `_PRE_EXISTING_USES` (`tests/static/test_ci_step_summary_reporting.py`) is a set of exact `uses:` strings, so the new action must be added with its exact version string.
3. **`astral-sh/setup-uv`**: latest release v10.2.0 (2026-09-21, via `gh api`). Inputs confirmed from its `action.yml`: `version`, `python-version`, `activate-environment`, `enable-cache`, `cache-dependency-glob`, `working-directory`. Without `version`, uv is "latest", so the job pins uv too.
4. **Which job.** `simulation-quality` is chosen: a single `pytest` step (`tests/simulation_quality`), no `needs`, no path-filter gate, not one of the two pinned jobs, and it passes locally in about 25 seconds (504 passed, 64 skipped, 27 deselected from a `uv sync --locked --no-install-project` environment). Jobs that run `python3 -m src` servers or `make` targets were avoided for the first migration.
5. **`--no-install-project`.** CI today has no editable install; pytest resolves `src` through `pythonpath = ["."]`. Decision: pass `--no-install-project`. Verified from a neutral directory that the project is not installed in the resulting environment and the job's tests still pass.
6. **Environment shape.** `activate-environment: true` makes `setup-uv` create `.venv` and export it to later steps; `uv sync` then fills that same `.venv`, so the existing `pytest` and `python3 tools/ci_junit_summary.py` steps are unchanged.
7. **ML stack.** `uv sync` without `--extra` or `--group` installs the default dependencies plus the default `dev` group only. Verified locally: torch is not installed.
8. **`--locked`** makes the job fail if `uv.lock` is out of date with `pyproject.toml`, which is the guard that keeps the two migrations honest.
9. **Path filters.** `PERF_RE` and `MIG_RE` trigger on `requirements.txt` but not `uv.lock` or `pyproject.toml`; unchanged here, as scoped.

## Not verifiable locally

Whether `setup-uv@v10.2.0` behaves as read from its `action.yml` (activation, caching with `uv.lock` as the cache key, Python 3.13 provisioning on the runner), and whether the job is green on a runner. That is the real-PR-run criterion.
