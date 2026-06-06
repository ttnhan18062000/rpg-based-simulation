# TCK-20260419-MB-TASK2-REAL-SIGNALS

## Title
Replace weak signals with real bounded accounting

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Transition runtime signals from estimates to truthful facts. This involves implementing peak-accounting for workers, windowed math for trends, and profile-bound sampling cadences.

## Scope
- [ ] Implement Peak Inflight/Depth tracking in `WorkerManager`.
- [ ] Implement Sliding Window logic in `RuntimeStatus`.
- [ ] Refactor `SignalCollector` to use `RuntimeProfile` sampling cadence.
- [ ] Implement Windowed Memory Trend calculation.
- [ ] Audit `ReplayManager` for truthful backlog accounting.

## Out of Scope
- Hardening governor logic (Task 3).
- Full Milestone B test suite (Task 5).

## Acceptance Criteria
- [ ] `worker_utilization` reflects the highest pressure observed during the tick.
- [ ] Memory trends are calculated over a 5-sample window, not single-delta.
- [ ] Compute averages reflect a 5-tick rolling window.
- [ ] RSS sampling occurs at the interval defined in the profile.

## Related Tickets
- `TCK-20260419-MB-TASK1-FREEZE-LAW` (Done)

## Related Docs
- `docs/engine/runtime_signals_contract_mb.md`

## Related Code Areas
- `src/engine/worker_manager.py`
- `src/engine/runtime_status.py`
- `src/engine/observability.py`

## Assumptions / Open Questions
- Assume 5-tick/5-sample window is sufficient for "Stable Law."

## Implementation Notes
- Use `deque` for history to maintain bounded memory.
- Ensure all math is protected against zero-division (e.g., empty queues).

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
