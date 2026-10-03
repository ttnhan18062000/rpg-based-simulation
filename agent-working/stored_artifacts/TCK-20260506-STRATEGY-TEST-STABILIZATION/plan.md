---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260506-STRATEGY-TEST-STABILIZATION
artifact_type: plan
tags: [strategy, test, stabilization]
---

# Implementation Plan - Strategy Test Stabilization

Migrate `tests/strategy/` to `V2EntityBuilder` to resolve `TypeError` regressions.

## Proposed Changes

### Tests Migration

#### [MODIFY] [test_cognition_capacity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategy/test_cognition_capacity.py)
#### [MODIFY] [test_leads.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategy/test_leads.py)
#### [MODIFY] [test_project_continuity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategy/test_project_continuity.py)
#### [MODIFY] [test_strategic_memory_v2.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategy/test_strategic_memory_v2.py)
#### [MODIFY] [test_strategic_reprioritization.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/strategy/test_strategic_reprioritization.py)

## Verification Plan

### Automated Tests
- `pytest tests/strategy -vv --tb=short`
