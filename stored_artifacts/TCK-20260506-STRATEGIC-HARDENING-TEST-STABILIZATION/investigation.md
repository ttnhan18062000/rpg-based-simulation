# Investigation - Strategic Hardening Test Failures

## Observations

Initial test run of `tests/strategic/` shows 37 failures.
- All are `TypeError: EntityState.__init__() got an unexpected keyword argument 'position'`.

## Root Cause

- Legacy tests are using direct `EntityState` constructors which are no longer compatible with the V2 engine's component-based `__init__`.
