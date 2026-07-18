---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260510-REFACTOR-PIPELINE-DECOMPOSITION-DETAILED
phase: done
date: 2026-05-10
tags: [refactor, pipeline, decomposition, detailed]
---

# TCK-20260510-REFACTOR-PIPELINE-DECOMPOSITION

## Title
Decompose AuthoritativeApplyPipeline into dedicated phases

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Split `src/engine/pipeline.py` into multiple modules under `src/engine/pipeline_phases/` to improve maintainability while preserving the existing public API via static wrappers.

## Scope
- Create `src/engine/pipeline_phases/` package.
- Extract Trust Boundary logic to `trust.py`.
- Extract Actor Validity logic to `actor_validity.py`.
- Extract Contract Lifecycle logic to `contracts.py`.
- Extract Action Routing logic to `actions.py`.
- Maintain all existing static methods in `AuthoritativeApplyPipeline` as wrappers.

## Out of Scope
- Changing any gameplay logic.
- Removing any existing static method signatures from `AuthoritativeApplyPipeline`.

## Acceptance Criteria
- [ ] `src/engine/pipeline_phases/` exists with `__init__.py`.
- [ ] `TrustBoundaryPhase`, `ActorValidityPhase`, `ContractLifecyclePhase`, and `ActionRoutingPhase` classes implemented in their respective modules.
- [ ] `AuthoritativeApplyPipeline` methods updated to delegate to the new phase classes.
- [ ] `pytest tests/integration/pipeline -q` passes.

## Related Tickets
- [TCK-20260510-REFACTOR-SUBSYSTEM-TEST-MIGRATION](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260510-REFACTOR-SUBSYSTEM-TEST-MIGRATION.md)

## Related Docs
- [refactor_implementation_plan.md](file:///home/vboxuser/Work/rpg-based-simulation/refactor_implementation_plan.md)

## Related Code Areas
- `src/engine/pipeline.py`
- `src/engine/pipeline_phases/`

## Implementation Notes
- Follow the skeletons provided in the implementation plan exactly.
- Use `from __future__ import annotations` and type hints.
- Be extremely careful with circular imports; use local imports in wrappers if necessary.

## Test Summary
- `pytest tests/integration/pipeline -q`

## Files Changed
- TBD

## Completion Summary
- TBD
