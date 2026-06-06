# TCK-20260513-PERF-CADENCE-CORE

## Title
Implement System Cadence Infrastructure

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Create the core cadence module to support staggered execution of engine subsystems.

## Scope
- Create `src/engine/cadence.py`.
- Define `SystemCadence` dataclass.
- Implement `should_run` helper.
- Implement `tests/unit/core/test_system_cadence.py`.

## Acceptance Criteria
- `should_run` correctly staggers execution based on `entity_id`.
- `should_run` returns `True` every `cadence` ticks for global systems (entity_id=None).
- `should_run` always returns `True` for `cadence=1`.

## Related Tickets
- TCK-20260513-PERF-CADENCE-INTEGRATION

## Related Code Areas
- `src/engine/cadence.py`
