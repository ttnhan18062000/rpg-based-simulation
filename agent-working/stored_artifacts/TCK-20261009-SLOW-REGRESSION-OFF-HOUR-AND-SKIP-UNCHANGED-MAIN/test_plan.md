---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN
phase: done
date: 2026-10-11
tags: [testing]
---

# Test plan

## Proof Plan
- level: unit plus static workflow shape plus live scheduled runs
- proof kind: decision-table unit tests for the gate and the watchdog; shape pins on the workflow; live run ids for `run` and `skip`
- oracle source: the 24 h rerun rule and the "actually tested" definition in the gate module docstring
- expected effect: an untested or day-old head runs the suite, a head tested under 24 h ago skips it and leaves issue #390 untouched
- selected commands: `pytest tests/unit/tools/test_slow_regression_gate.py tests/unit/tools/test_slow_regression_watchdog.py tests/static/test_ci_slow_workflow_shape.py`
