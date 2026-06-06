# TCK-20260419-MB-TASK3-GOVERNOR-HARDENING

## Title
Harden Governor Transitions and Policy Integration

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Transition the `ResourceGovernor` from rough heuristics to a hardened control layer. This involves implementing profile-driven recovery, monotonicity in de-escalation, and a "Confidence Window" to prevent thrashing.

## Scope
- [ ] Refactor `ResourceGovernor` to use `RuntimeProfile` operational constants.
- [ ] Implement `Confidence Window` check in `_can_recover`.
- [ ] Ensure `_get_indicated_mode` uses Lawson-pinned thresholds.
- [ ] Implement strict one-level-at-a-time recovery.
- [ ] Add explicit policy coupling for selective work shedding in SURVIVAL mode.

## Out of Scope
- Implementing the real accounting (Done in Task 2).
- Final Milestone B test suite (Task 5).

## Acceptance Criteria
- [ ] Governor adheres to `dwell_time_ticks` and `confidence_window_ticks` from profile.
- [ ] Recovery thresholds use `recovery_watermark` consistently.
- [ ] System never oscillates between modes in a single tick.
- [ ] Mode changes are monotonic during recovery.

## Related Tickets
- `TCK-20260419-MB-TASK2-REAL-SIGNALS` (Done)

## Related Docs
- `docs/engine/runtime_signals_contract_mb.md`

## Related Code Areas
- `src/engine/governor.py`
- `src/engine/runtime_status.py`

## Assumptions / Open Questions
- Assume `recovery_watermark` is a multiplier for ALL thresholds (RAM, CPU, Workers).

## Implementation Notes
- Follow the "One Level at a Time" recovery rule in the contract.
- Use `RuntimeStatus.signal_history` for confidence window logic.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
