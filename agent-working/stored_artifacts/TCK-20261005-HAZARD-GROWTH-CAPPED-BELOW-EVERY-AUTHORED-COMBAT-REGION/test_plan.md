---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION
phase: done
date: 2026-10-05
tags: [world]
---

# test_plan — TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION

`tests/unit/engine/test_hazard_growth_open_ended.py` (10 tests): growth for authored 0.0, 0.5, 0.99, 1.0, 2.0, 3.0, 4.0; not capped at 1.0; none at or below the threshold; trauma proposed this tick counts. On the old code, 6 fail (every value >= 1.0 and the over-1.0 cases) and the 4 below-1.0 cases pass: the below-1.0 cases are the positive control.

## Proof Plan
- level: unit, then full CI lane set
- proof kind: behavioural test failing on the old code; paired deterministic world run
- oracle source: owner decision 12; Bible 05
- expected effect: hazard grows for every region above trauma 50, with no ceiling
- selected commands: `pytest tests/unit/engine/test_hazard_growth_open_ended.py`; the CI lane set
