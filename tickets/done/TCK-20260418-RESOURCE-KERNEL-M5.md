# TCK-20260418-RESOURCE-KERNEL-M5

## Title
Milestone 5: Resource Governor and Degradation State Machine

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement an authoritative resource governor to protect the simulation envelope via deterministic degradation modes.

## Scope
- Define `GovernorContract` for pressure detection and mode transitions.
- Implement `RuntimeMode` state machine (`NORMAL`, `CONSTRAINED`, `DEGRADED`, `SURVIVAL`).
- Track pressure signals (Memory, Tick Budget, Debt, Queue).
- Implement explicit degradation order for non-authoritative work (Diagnostics, Metrics, Opportunistic).
- Pin with governor and degradation tests in `tests/`.

## Out of Scope
- Replay persistence.
- Real-world OS/Container resource monitoring (using simulated/mocked signals for this milestone).
- Adaptive performance tuning (M5 is about *protection*, not fine-tuning).

## Acceptance Criteria
- [x] Explicit mode transition path (NORMAL -> SURVIVAL) based on profile thresholds.
- [x] Deterministic recovery logic (with stabilization/hysteresis).
- [x] Authoritative work preserved in all modes.
- [x] Optional work shed in exact declared order during pressure.
- [x] 100% test pass for governor and degradation semantics.

## Related Tickets
- TCK-20260418-RESOURCE-KERNEL-M4 (DONE)

## Related Docs
- `resource_implementation_milestone_5.md`

## Related Code Areas
- `src/engine/`
- `src/core/`
- `tests/`

## Assumptions / Open Questions
- Pressure signals will be mockable for tests.
- We will integrate the `Governor` output into the `Scheduler` selection logic.
- "Replay richness" is currently a placeholder for future milestones but must be degradable.

## Implementation Notes
- Follow the M5 strategy: Protect Authoritative first, Shed Optional second.

## Test Summary
- 43 tests passed in `tests/`.
- `test_escalation` verified immediate response to tick-budget and debt pressure.
- `test_anti_thrashing` confirmed that recovery is gated by low-watermark and dwell time.
- `test_degradation_order` proved that only optional work is shed (Waterfall policy).
- `test_governance_isolation` verified that `AuthoritativeState` hash is invariant to mode changes.

## Files Changed
- `src/core/governance.py`
- `src/engine/` (governor, policy, runtime_status, kernel, scheduler)
- `tests/` (governor, anti-thrashing, degradation, isolation)
- `docs/engine/` (M5 specs)

## Completion Summary
Milestone 5 finalized. The engine now has a formal, authoritative resource-protection layer. Operational state is strictly isolated from simulation truth, ensuring that determinism is never compromised by runtime pressure. The system now supports deterministic mode transitions (NORMAL/CONSTRAINED/DEGRADED/SURVIVAL) and protects authoritative semantics while shedding optional cost.
