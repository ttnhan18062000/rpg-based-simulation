---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260506-STRATEGY-TEST-STABILIZATION
artifact_type: investigation
tags: [strategy, test, stabilization]
---

# Investigation - Strategy Test Failures

## Observations

Initial test run of `tests/strategy/` shows 13 failures and 2 errors.
- Majority are `TypeError: EntityState.__init__() got an unexpected keyword argument 'position'`.
- `test_strategic_memory_v2.py` shows `TypeError: EntityState.__init__() got an unexpected keyword argument 'active'`.

## Root Cause

- Legacy tests are using direct `EntityState` constructors which are no longer compatible with the V2 engine's component-based `__init__`.
- The `active` field is part of the `LifecycleComponent` and should be set via the builder or through the component directly if using manual state construction (not recommended for tests).
