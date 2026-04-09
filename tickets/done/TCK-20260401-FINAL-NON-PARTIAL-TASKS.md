# TCK-20260401-FINAL-NON-PARTIAL-TASKS: Address "Truly Open" Implementation Tasks

## Goal
To complete specific tasks from `final_implementation_plan_2.md` that are marked as "Still open" or "Still not done" in the review comments, specifically focusing on those not yet even partially implemented.

## Scope
- Refactoring `src/ai/states/town.py` handlers to use typed `IntentUpdate` models.
- Addressing Mind-state structural invariants (e.g., `MindAspect` typing).
- Phase-boundary enforcement for snapshot usage.
- Addressing potential side-effects in AI decision generation.

## Acceptance Criteria
- [ ] `ActionProposal.updates` is populated for town/interaction handlers instead of `intent_metadata`.
- [ ] `MindAspect` sub-models (Perception, Navigation, etc.) use typed structures instead of `Any`.
- [ ] No direct mutations of snapshot entities in AI handlers.
- [ ] 100% pass rate in E2E tests.

## Related Tickets
- `TCK-20260401-FINAL-CONVERGENCE`

## Status: INPROGRESS
