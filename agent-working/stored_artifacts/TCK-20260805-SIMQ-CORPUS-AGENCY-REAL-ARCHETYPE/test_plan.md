---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE
artifact_type: test_plan
tags: [simulation-quality, world, adventure, corpus, calibration]
---

# test_plan.md — TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE

## Regression Surface (existing tests that must pass)

No production code, corpus content, or anchors changed — `tests/simulation_quality/
test_grade_regression.py -m "not slow"` must be unaffected (68/69, 1 pre-existing unrelated
failure, per this session's last-verified state).

## New Tests Required (per AC)

None — no new world/code shipped, doc correction only.

## Scoped Pytest Commands

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
```

## Anti-Drift Test Guards

None new.
