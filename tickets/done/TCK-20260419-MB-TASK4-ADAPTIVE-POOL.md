# TCK-20260419-MB-TASK4-ADAPTIVE-POOL

## Title
Implement Adaptive Saturated-Pool Strategy

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Transition the worker pool from a static-only resource to an elastic resource governed by operational policy. This implements Principle 8 (Elastic Concurrency) from the handbook.

## Scope
- [ ] Add `concurrency_limit` (float) to `GovernorPolicy`.
- [ ] Implement Policy Waterfall for concurrency limits in different modes (e.g. DEGRADED: 0.5, SURVIVAL: 0.25).
- [ ] Refactor `WorkerManager.execute_batch` to respect the effective concurrency cap.
- [ ] Instrument `WorkerManager` to report "Virtual Saturation" (truthfully reporting when it was capped by policy vs hardware).

## Out of Scope
- Dynamic pool resizing (process spawn/kill mid-tick). We will cap the *usage* of the existing pool.

## Acceptance Criteria
- [ ] In DEGRADED mode, the number of active workers never exceeds `max_workers * 0.5`.
- [ ] Worker utilization signals reflect the *effective* limit, not just the hardware limit.
- [ ] No regression in single-tick determinism.

## Related Tickets
- `TCK-20260419-MB-TASK3-GOVERNOR-HARDENING` (Done)

## Related Docs
- `resource_handbook.md` (Principle 8)

## Related Code Areas
- `src/engine/policy.py`
- `src/engine/worker_manager.py`
- `src/engine/kernel.py`

## Assumptions / Open Questions
- If `concurrency_limit` is less than 1, excess work packets remain in the `queued` count and are reported as such.

## Implementation Notes
- Use `math.ceil(self._max_workers * concurrency_limit)` for the effective cap.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
