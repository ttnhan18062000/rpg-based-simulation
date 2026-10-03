---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-REMAINING-CI-JOBS
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261002-UV-REMAINING-CI-JOBS

Context scan: `search_docs` (no relevant hit beyond older CI tickets) and `graphify query` (no CI-workflow nodes) first; the facts below come from the follow-up reads.

## Install lines in `test.yml`
- 15 jobs run `actions/setup-python@v6` (`cache: pip`) + `pip install -r requirements.txt`: unit-core-world, unit-gameplay, unit-infra, integration, tools-a-e, tools-f-z, api-cli-engine, agent-orchestration, arch-docs, perf-cert-arena, scenario-lane, migration-lanes, typecheck, simq-grade-drift, slow. `typecheck` also has `pip install mypy`.
- `simulation-quality` is already on uv; its setup is the template. `frontend` and `changed-files` install no Python dependencies.
- `PERF_RE` and `MIG_RE` (lines 753-754) list `requirements.txt` but not `pyproject.toml` / `uv.lock`; `tools/test_architecture/scenario_lane_paths.py` already lists all three.

## Pins that name an install line
| File | What it pins | Action |
|---|---|---|
| `tests/static/test_ci_step_summary_reporting.py` | `_EXPECTED_MIGRATION_LANES_YAML`, `_EXPECTED_SLOW_YAML` (setup-python + pip lines) | change install/cache lines only |
| `tests/tools/test_ci_split_tools_jobs.py:100-103` | pip line for the 3 split jobs | change to uv pin |
| `tests/tools/test_dashboard_makefile_targets.py:22` | `install-py` recipe string | change to uv recipe |
| `tests/tools/test_delivery_ci_triage_classifier.py:39` | a workflow fixture string | stays (fixture, not the real workflow) |
| `tests/unit/tools/test_scenario_lane_paths.py` | `requirements.txt` trigger path | stays |
| `tests/static/test_ci_requirements_no_ml_stack.py`, `tests/tools/test_evidence_cache_identity_contract.py` | read `requirements.txt` | stay (file kept) |
No other test under `tests/` names `pip install`.

## Who needs ruff / complexipy
`tools/code_health/scan.py` raises `ToolUnavailableError` when either is missing. The tests that reach it: `tests/tools/test_code_health_*.py`, `test_codebase_health_snapshot.py`, `test_codebase_health_snapshot_craft.py` (all `c*`, so `tools-a-e`). `test_pr_impact_report.py` (`p*`, in `tools-f-z`) only imports `code_health_impact`. None of these carry a `slow` marker, so `slow` does not collect them. To be confirmed empirically: run every job's scope in a `--no-group lint` environment where feasible (at least tools-a-e must fail there and pass with lint; tools-f-z must pass without).

## Other places
- `make.bat:66` `pip install -r requirements.txt` (the Makefile `install-py` equivalent).
- Docs with pip instructions: `docs/guidelines/agent_working_environment.md` (lines 23, 96-97, 135), `docs/guides/delivery_process.md:254` ("CI runs in ... `pip install -r requirements.txt`"), `docs/testing/migration_ci_lanes.md` (path list ~line 96).
- "Base branch test collection" steps `cd /tmp/base-checkout && pytest ...`: `simulation-quality` already does this under `activate-environment: true`; PR run confirms for the rest.
