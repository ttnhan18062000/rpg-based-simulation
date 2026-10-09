---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-UBUNTU-26-RUNNER-PRECHECK
phase: open
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
