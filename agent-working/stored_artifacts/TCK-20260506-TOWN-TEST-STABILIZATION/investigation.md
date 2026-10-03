---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260506-TOWN-TEST-STABILIZATION
artifact_type: investigation
tags: [town, test, stabilization]
---

# Investigation - Town Test Failures

## Observations

Initial test run of `tests/town/` shows 21 failures.
- All are `TypeError: EntityState.__init__() got an unexpected keyword argument 'position'`.

## Root Cause

- Legacy tests are using direct `EntityState` constructors which are no longer compatible with the V2 engine's component-based `__init__`.
