# TCK-20260418-RESOURCE-KERNEL-M4

## Title
Milestone 4: Deterministic Scheduler and Work Model

## Status
DONE

## Request Summary
Replace naive execution with an explicit deterministic scheduler that classifies and bounds work items.

## Scope
- Define `SchedulerContract` for deterministic work selection.
- Implement `WorkClass` model (Critical, Periodic, Opportunistic, Deferred).
- Implement `Bounded Work Debt` for deferred tasks.
- Implement the `Deterministic Scheduler` core with explicit tie-breaking.
- Pin with scheduler contract tests in `tests_v2/`.

## Out of Scope
- Resource governor implementation (pressure response).
- Concurrency/Worker pool implementation.
- Observability dashboards.
- Adaptive performance degradation.

## Acceptance Criteria
- [x] Explicit deterministic work selection path.
- [x] Work classified into Critical/Periodic/Opportunistic/Deferred.
- [x] Deferred work has explicit bounds and accumulation/drain rules.
- [x] 100% test pass in `tests_v2/` for scheduling semantics.
- [x] Documentation pack (Contract, Work Model Matrix, Test Matrix) finalized.

## Related Tickets
- TCK-20260418-RESOURCE-KERNEL-M3 (DONE)

## Related Docs
- `resource_implementation_milestone_4.md`

## Related Code Areas
- `src_v2/engine/`
- `src_v2/core/`
- `tests_v2/`

## Assumptions / Open Questions
- We will integrate the `Scheduler` into the `Kernel.tick_once()` orchestration.
- Tie-breaking will primarily use `entity_id` and a secondary `priority_hint`.

## Implementation Notes
- Follow the Step 5 strategy: Docs -> Types -> Tests -> Implementation.

## Test Summary
- 35 tests passed in `tests_v2/`.
- `test_readiness_driven_selection` confirmed correct entity action timing.
- `test_deterministic_tiebreak` verified stable sort order by EntityID.
- `test_bucket_prioritization` verified Critical > Periodic > Deferred ranking.
- `test_deferred_drain_order` verified authoritative debt reduction.

## Files Changed
- `src_v2/core/` (work, state, updates)
- `src_v2/engine/` (scheduler, kernel, apply)
- `tests_v2/` (new scheduler and work class tests)
- `docs/engine/` (M4 specs)

## Completion Summary
Milestone 4 finalized. The engine now uses a formal deterministic scheduler. Work is explicitly classified into Critical, Periodic, and Deferred classes with stable, cross-class execution rules. Authoritative Work Debt and Periodic Cadence are now stored in the simulation state, ensuring perfect consistency across runs.
