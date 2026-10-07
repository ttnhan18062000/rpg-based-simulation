---
status: historical
layer: testing
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX
phase: done
date: 2026-10-06
tags: [testing, investigation]
---

# Test Plan — TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX

No code or test is changed by this ticket, so no new test is written. The proof is observational:

- **Before:** run 37403688489, 8 step-6 failures (job 112078415756).
- **After:** scheduled run 37551894246 (head bc4f7553c): issue #390's failing set has 5 step-6 tests, every one mapped to an owned ticket in `slow_known_reds.yaml`, none UNOWNED; the report step concluded success.
- **Regression guard going forward:** the `Slow regression` reporter comments NEW/FIXED on #390 when the set changes and fails the run on an UNOWNED or EXPIRED red (pinned by `tests/unit/tools/test_slow_regression_report.py` and `tests/static/test_ci_slow_workflow_shape.py`, owned by the SIMQ-GRADE-ANCHORS ticket).

## Proof Plan
- **Level:** CI, the `Slow regression` workflow on `main` (no unit level: nothing changed).
- **Proof kind:** observational, before/after live runs.
- **Oracle source:** the rolling issue #390 failing set, written by `tools/test_architecture/slow_regression_report.py` from the run's JUnit XML.
- **Expected effect:** every step-6 red is either absent (fixed) or mapped to an owned, in-date entry; no UNOWNED red.
- **Selected commands:** `gh issue view 390 --json body`; `gh api repos/ttnhan18062000/rpg-based-simulation/actions/runs/37551894246/jobs`.
