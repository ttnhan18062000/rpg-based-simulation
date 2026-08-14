---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP
artifact_type: test_plan
tags: [simulation-quality, world, faction, corpus, calibration]
---

# test_plan.md — TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP

## Regression Surface (existing tests that must pass)

No production code or corpus content changed (the draft world was reverted before commit) —
`tests/simulation_quality/test_grade_regression.py -m "not slow"` must show identical results to
before this ticket (65/66, 1 pre-existing unrelated failure), confirming the revert left no trace.

## New Tests Required (per AC)

None — no new world/code shipped.

## Scoped Pytest Commands

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

## Anti-Drift Test Guards

None new.
