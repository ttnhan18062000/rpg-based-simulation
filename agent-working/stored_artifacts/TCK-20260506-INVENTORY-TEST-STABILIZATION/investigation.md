---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260506-INVENTORY-TEST-STABILIZATION
artifact_type: investigation
tags: [inventory, test, stabilization]
---

# Investigation - Inventory Test Failures

## Observations

Initial test run of `tests/inventory/` shows 15 failures, all due to:
`TypeError: EntityState.__init__() got an unexpected keyword argument 'position'`

This confirms that the `EntityState` dataclass no longer accepts `position` as a direct keyword argument in its `__init__`, as part of the V2 engine hardening. The `V2EntityBuilder` must be used instead.

## Root Cause

Legacy tests are using the `EntityState` constructor directly, which was broken by the introduction of component-based architecture where `position` is encapsulated within `NavigationComponent`.
