---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-UBUNTU-26-RUNNER-PRECHECK
phase: done
date: 2026-10-09
tags: [architecture, delivery]
---

# investigation — TCK-20261009-UBUNTU-26-RUNNER-PRECHECK

Findings so far (2026-10-09):
- `.github/workflows/`: 5 files, 26 `ubuntu-latest` entries (`test.yml` 21, `slow-regression.yml` 2, `deploy-docs.yml`, `pr-body-lint.yml`, `slow-regression-watchdog.yml` 1 each).
- Static tests that name `ubuntu-latest`: `tests/static/test_ci_slow_workflow_shape.py:187` (slow workflow, which the probe does not change), plus inline sample workflows in `test_ci_step_summary_reporting.py` and `test_delivery_ci_triage_classifier.py` (not reading `test.yml`).
- origin/main `0c3a5654b` (#471) does not touch `.github`; main's `test.yml` run 37955084870 on it is green (earlier green run 37947573079 on `20af2959a`).
- Prior evidence: PR #331 ran `Code health` and `Type check` on `ubuntu-26.04`, both passed.
Probe results are added here when the run exists.

Probe results (run 37959405085, 2026-10-09): 18 success, 2 skipped, 1 failure (static test pinning `runs-on: ubuntu-latest`, a probe artifact). Image `ubuntu-26.04` 20260927.149 against main's `ubuntu-24.04` 20261002.596. New on 26.04: 9 `setup-uv` cache-save race warnings (OS version is in the cache key; cold cache). `Integration` 540/534 s against 363 s on main (main's range 349 to 521 s). `Code health SARIF` is PR-only (skipped on main's push run), `SimQ grade-anchor drift` is push-only. Full table in `docs/plans/codebase_health/ubuntu_26_runner_precheck.md`.
