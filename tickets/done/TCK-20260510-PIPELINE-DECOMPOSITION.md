---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260510-PIPELINE-DECOMPOSITION
phase: done
date: 2026-05-10
tags: [pipeline, decomposition]
---

# TCK-20260510-PIPELINE-DECOMPOSITION

## Title
Modularize AuthoritativeApplyPipeline into Domain-Driven Phases

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Refactor the monolithic `AuthoritativeApplyPipeline` class in `src/engine/pipeline.py` into smaller, maintainable phase modules under `src/engine/pipeline_phases/`.

## Scope
- Extract Trust Boundary logic
- Extract Actor Validity logic
- Extract Contract Lifecycle logic
- Extract Action Routing logic (with sliding state)
- Extract Near-Death Hardening logic
- Extract Quest Reward logic
- Extract Resource Transaction logic
- Extract Movement and Position Swap logic
- Extract Occupancy Conflict logic
- Maintain static wrappers for backward compatibility

## Out of Scope
- Modifying `DomainLogic` (Milestone 3)
- Modifying Systems (Milestone 4)
- Changing `EntityState` or `AuthoritativeState` models

## Acceptance Criteria
- [x] All 9 phases extracted to `src/engine/pipeline_phases/`
- [x] `AuthoritativeApplyPipeline` uses delegation wrappers
- [x] 100% test pass rate in `tests/integration/pipeline`
- [x] 100% test pass rate in combat, movement, resource, and quest unit tests
- [x] Phase order is strictly preserved in `refine()`

## Related Tickets
- None

## Related Docs
- [refactor_implementation_plan.md](file:///home/vboxuser/Work/rpg-based-simulation/refactor_implementation_plan.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/pipeline.py`
- `src/engine/pipeline_phases/`

## Implementation Notes
- Used `from __future__ import annotations` and `TYPE_CHECKING` to avoid circular imports.
- Preserved the sliding state logic in `ActionRoutingPhase` to ensure deterministic execution.
- Verified that `_mark_position_swap_contract_fulfilled` correctly prevents infinite swap loops.

## Test Summary
- `pytest tests/integration/pipeline` - 73 passed
- `pytest tests/unit/combat` - 54 passed
- `pytest tests/unit/movement` - 31 passed
- `pytest tests/unit/resource` - 62 passed
- `pytest tests/unit/quest` - 30 passed
- `pytest -q -k "subsystem_order"` - Passed (verified manually via `test_phase_order.py`)

## Files Changed
- `src/engine/pipeline.py`
- `src/engine/pipeline_phases/__init__.py` [NEW]
- `src/engine/pipeline_phases/trust.py` [NEW]
- `src/engine/pipeline_phases/actor_validity.py` [NEW]
- `src/engine/pipeline_phases/contracts.py` [NEW]
- `src/engine/pipeline_phases/actions.py` [NEW]
- `src/engine/pipeline_phases/hardening.py` [NEW]
- `src/engine/pipeline_phases/quests.py` [NEW]
- `src/engine/pipeline_phases/resources.py` [NEW]
- `src/engine/pipeline_phases/movement.py` [NEW]
- `src/engine/pipeline_phases/occupancy.py` [NEW]

## Completion Summary
Completed the full decomposition of the authoritative pipeline. The codebase now has a clean separation between the orchestration layer (`pipeline.py`) and the individual domain phases. This paves the way for further modularization of the domain logic in Milestone 3.
