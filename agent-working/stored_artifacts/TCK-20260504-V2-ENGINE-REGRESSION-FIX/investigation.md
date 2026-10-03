---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260504-V2-ENGINE-REGRESSION-FIX
artifact_type: investigation
tags: [v2, engine, regression, fix]
---

# Investigation - TCK-20260504-V2-ENGINE-REGRESSION-FIX

## Root Cause Analysis
The 39 test failures are caused by `TypeError` when instantiating `EntityState`.
In the V2 engine, `EntityState` was converted to a frozen dataclass with a more complex component structure. Specifically:
- `position` is now a property, not a field. The initialization goes through `position_init` (InitVar) or the `navigation` component.
- The `EntityGenerator.spawn_...` methods are still using the legacy keyword arguments like `position=pos`, which no longer exist on the `EntityState` constructor.

## Impact Surface
- `src/systems/generator.py`: Used for almost all entity spawning in tests and world dynamics.
- `tests/engine/*.py`: Many tests manually construct entities for specific edge cases.

## Recommended Solution
Complete the migration to `V2EntityBuilder` which is designed to handle these mappings correctly and produce valid V2 `EntityState` objects.
