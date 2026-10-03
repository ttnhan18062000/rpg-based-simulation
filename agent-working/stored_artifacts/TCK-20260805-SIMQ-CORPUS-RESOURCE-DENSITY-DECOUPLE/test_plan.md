---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE
artifact_type: test_plan
tags: [simulation-quality, world, economy, corpus, calibration]
---

# test_plan.md — TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE

## Regression Surface (existing tests that must pass)

No production code or corpus content changed — `tests/simulation_quality/test_grade_regression.py
-m "not slow"` must be unaffected (65/66, 1 pre-existing unrelated failure).

## New Tests Required (per AC)

None — no new world/code shipped, doc correction only.

## Scoped Pytest Commands

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

## Anti-Drift Test Guards

None new.
