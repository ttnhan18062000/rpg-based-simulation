---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261008-LIGHT-BALANCE-PASS-HUMAN-HUNGER-IS-LOW-DECISION-33
artifact_type: test_plan
tags: []
---

# Test plan

Biological-needs unit tests; resolve all worlds; 5000-tick pinned 5x3.

## Proof Plan

- level: unit
- proof kind: value
- oracle source: owner decision 33, Bible 01 section 4 and Bible 05 section 1 (2400 ticks per day)
- expected effect: a human builds hunger at 0.05 per tick, a goblin at 0.1
- selected commands: `pytest tests/unit/engine/test_biological_needs.py tests/unit/world/test_recovery_class_hall.py`
