---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-REMAINING-CI-JOBS
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261002-UV-REMAINING-CI-JOBS

## Static and unit (run locally)
- `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_ci_split_tools_jobs.py tests/unit/tools/test_scenario_lane_paths.py tests/tools/test_delivery_ci_triage_classifier.py`
- Additive tests: no `pip install` in any job; `lint` synced only by `tools-a-e`, `--no-group lint` elsewhere; `PERF_RE`/`MIG_RE` match `pyproject.toml` and `uv.lock` and still do not match an unrelated path (negative case).
- Failure mode: assert the `typecheck` job has no `pip install mypy` but still has a step named `mypy` running `mypy src/`.

## Dependency evidence
- `uv lock --check --system-certs`; `uv export ...` diffed against committed `requirements.txt` (must be identical, contains ruff and complexipy).
- `uv sync --locked --no-install-project --no-group lint` into a scratch env: `pip list`/`uv pip list` shows neither ruff nor complexipy, no torch / sentence-transformers.

## Does anything outside tools-a-e need lint?
- In the scratch no-lint env run `pytest tests/tools -k "not code_health and not codebase_health"`-style scope for `tools-f-z` (`--ignore-glob='tests/tools/test_[a-e]*.py'`) and confirm no failure or skip names ruff/complexipy. Run `tests/tools/test_code_health_*.py tests/tools/test_codebase_health_snapshot*.py` in that env as a negative control (expected to fail with "not found").
- Same env, `pytest tests/static tests/architecture` as a cheap proxy for arch-docs.
- Full-lane runs of the heavy jobs are left to the PR run; the install step is the only difference between those jobs and today's.

## PR run (after owner authorizes push)
- Every job green; install logs for a `--no-group lint` job show no ruff/complexipy; "Base branch test collection" works from `/tmp/base-checkout` in every job that has it; link recorded in the ticket.
