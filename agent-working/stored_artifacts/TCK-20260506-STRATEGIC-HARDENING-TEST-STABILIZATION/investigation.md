---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260506-STRATEGIC-HARDENING-TEST-STABILIZATION
artifact_type: investigation
tags: [strategic, hardening, test, stabilization]
---

# Investigation - Strategic Hardening Test Failures

## Observations

Initial test run of `tests/strategic/` shows 37 failures.
- All are `TypeError: EntityState.__init__() got an unexpected keyword argument 'position'`.

## Root Cause

- Legacy tests are using direct `EntityState` constructors which are no longer compatible with the V2 engine's component-based `__init__`.
