---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
phase: done
date: 2026-10-10
tags: [testing, regression]
---

# Test plan

## Proof Plan
- level: unit plus static workflow shape
- proof kind: golden-output equality for the refactor; unit tests for the new module; shape test for the workflow invocation
- oracle source: the slow report's own pre-refactor output (`tests/fixtures/slow_report_golden/expected.json`) and the epic's rules (first match wins, shadowing rejected, expiry, stale mapping, state per entry)
- expected effect: identical slow report output; both registry files lint clean; the gate registry is empty
- selected commands: `pytest tests/unit/tools/test_known_reds.py tests/unit/tools/test_slow_regression_report.py tests/unit/tools/test_slow_regression_report_golden.py tests/static/test_ci_slow_workflow_shape.py`

Cases: match, first-wins, shadowing (within and across states), expiry boundary, classify (unowned/expired, per state), stale mapping (per state), required fields for both kinds, kind and state values, ISO dates and order, bracket ban, strict vs tolerant unknown fields, an extension spec, loader edge cases, re-exported names.
