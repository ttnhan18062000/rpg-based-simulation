---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-REMAINING-CI-JOBS
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261002-UV-REMAINING-CI-JOBS

Branch `uv-remaining-ci-jobs`, cut from main at 42a432c5. Push and PR only on the owner's word.

1. **`pyproject.toml`**: move `ruff==0.16.10` and `complexipy==8.0.1` from `dev` to a new `lint` group (comment kept). Add `[tool.uv] default-groups = ["dev", "lint"]`. Update the comments that say "pinned in the dev group" and the header comment. Then `uv lock --system-certs`; `uv lock --check` must pass.
2. **`requirements.txt`**: regenerate with the documented `uv export --frozen --no-hashes --no-emit-project -o requirements.txt`. Expected result: byte-identical (default-groups keeps both tools in the export). If it differs, stop and report.
3. **`.github/workflows/test.yml`**
   - The 15 pip jobs get the `simulation-quality` setup verbatim: `astral-sh/setup-uv@v10.2.0` with `{ version: "0.11.2", python-version: "3.13", activate-environment: true, enable-cache: true }`, then `uv sync --locked --no-install-project`.
   - Every job except `tools-a-e` adds `--no-group lint` (including `simulation-quality`, whose plain sync would now pull lint through default-groups). `tools-a-e` is the only job that syncs `lint`.
   - `typecheck`: delete `pip install mypy`; the `mypy` step is untouched.
   - Replace the "other jobs stay on pip" comment above the `simulation-quality` install.
   - `PERF_RE` and `MIG_RE` gain `pyproject\.toml$|uv\.lock$` next to `requirements\.txt$`.
4. **Makefile / `make.bat`**: `install-py` becomes `uv sync` (default groups, so dev and lint, same as `pip install -r requirements.txt` today). `make.bat` line 66 gets the same change. No `--system-certs` in either (machine-specific, documented in the working-environment guide).
5. **Edited tests** (install and cache lines only; each edit listed in the ticket with its reason):
   - `tests/static/test_ci_step_summary_reporting.py`: both expected YAML blocks.
   - `tests/tools/test_ci_split_tools_jobs.py`: the pip pin becomes a uv pin for the 3 split jobs (setup-uv step present, `uv sync --locked --no-install-project` with the right group flag, no pip install).
   - `tests/tools/test_dashboard_makefile_targets.py`: `install-py` string.
   - New assertions (additive): no `pip install` remains in `test.yml`; only `tools-a-e` syncs `lint`; `PERF_RE`/`MIG_RE` match `pyproject.toml` and `uv.lock`. Put in the existing test file nearest each concern.
6. **Docs**: `agent_working_environment.md` (CI now uses uv; describe `lint` group, `default-groups`, `--no-group lint`; `requirements.txt` is a generated export that still lists the lint tools), `delivery_process.md:254`, `migration_ci_lanes.md` path list. Then `make knowledge-index-update`.
7. **Verify locally** (see test_plan.md), then ticket commit, send the diff to codebase-planner.
8. **After the owner authorizes push/PR**: record the PR run link and per-job install-log evidence in the ticket, then close (move to done, delete the todos source, working log via the closure tool with `--agent implementer`, move artifacts to `stored_artifacts/`).
9. **Epic close (planner condition E)**: once the green PR run is recorded, close `TCK-20261002-PYTHON-CODE-CRAFT-EPIC` on the same branch and move the whole `tickets/todos/python-code-craft/` folder to `tickets/done/python-code-craft/` (keeps SEQUENCE.md).

## Planner conditions folded in (2026-10-03)
A. `uv.lock` diff after `uv lock` must be the group move only; any version change = stop and report. B. Closure with default agent / `implementer`, never the session name; before the first push run `monitoring_anomaly_validator.py` and the full `tests/tools` lane (both halves); an "unrecognized agent" warning = stop. C. `pyproject.toml` in PERF_RE/MIG_RE means any pyproject edit now runs perf-cert-arena and migration-lanes: state in ticket Implementation Notes and `migration_ci_lanes.md`. D. Record the no-lint negative control outcome (fail vs skip, message); if any skips, tell the planner before the commit. Docs: mention `UV_SYSTEM_CERTS=1` for TLS interception and that `make install-py` now also installs the project editable.

## Scope guards
No path under `src/`, `.claude/`, `CLAUDE.md`. No change to what any job tests, to triggers other than the two path regexes, or to the mypy gate. `requirements.txt` stays. Pinned versions of ruff and complexipy unchanged. No assertion weakened beyond install/cache lines.

## Open points for the planner
- `make install-py` and `make.bat` without `--system-certs`: acceptable?
- `simulation-quality` also gets `--no-group lint` (it tests only SimQ). It is an edit to the already-migrated job, a one-flag change.
- The `test-architecture-reviewer` must be told about the test edits before the change lands; I cannot reach it from here.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| No `pip install -r requirements.txt` in test.yml; every Python job on `uv sync` | 3 |
| migration-lanes/slow differ only in install/cache lines | 3, 5 |
| `make install-py` via uv, test updated | 4, 5 |
| split-jobs pin updated | 5 |
| lint group only; lock check; export reproduces | 1, 2 |
| `--no-group lint` logs show no ruff/complexipy; no tool-missing failures | 3; PR run |
| PERF_RE/MIG_RE match new paths | 3 |
| typecheck has no pip mypy; mypy step intact | 3 |
| No ML stack | 2 (export unchanged) |
| static + makefile + coverage tests pass | 7 |
| Green PR run | 8 |
| Docs | 6 |
| Diff has no src/.claude/CLAUDE.md | 7 |
