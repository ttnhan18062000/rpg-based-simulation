---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-FIRST-CI-JOB
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261002-UV-FIRST-CI-JOB

No new test. The workflow is covered by existing static tests; the real proof is the PR run.

## Proof Plan

- level: static plus a live CI run
- proof kind: existing static tests locally; GitHub Actions run for the migrated job
- oracle source: the existing `tests/static/` CI pins and the job's own green run
- expected effect: `simulation-quality` installs from `uv.lock`, runs the same pytest step, and passes; every other job is unchanged
- selected commands:

| Check | Command | Expected |
|---|---|---|
| Static CI pins and Makefile pin | `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py` from an environment built with `uv sync --locked --no-install-project` | pass |
| Job's own suite | `pytest tests/simulation_quality -m "not slow and not extra_slow"` from that environment | pass |
| One uv job | `grep -c "uv sync" .github/workflows/test.yml` | 1 |
| Others unchanged | `grep -c "pip install -r requirements.txt" .github/workflows/test.yml` | 13 (was 14) |
| No ML stack, no editable install | import check from a neutral directory | torch absent; project not installed |
| Diff scope | `git diff --stat 7dfd1349` | no `src/`, `.claude/`, `CLAUDE.md`, Makefile |
| Real run | open a PR; read the `Simulation quality` job and its install step | green; no torch or sentence-transformers in the log |
