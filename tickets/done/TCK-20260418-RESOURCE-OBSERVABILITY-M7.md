# TCK-20260418-RESOURCE-OBSERVABILITY-M7

## Title
Milestone 7: Observability and Operational Controls

## Status
DONE

## Request Summary
Establish the engine's first runtime-visibility and operational-control surfaces. Implement strict startup validation, stable runtime signals (with memory trends), and formal graceful shutdown sequences.

## Scope
- Define `ObservabilityContract` and `OperationalControlsMatrix`.
- Implement `ProfileValidator` for startup configuration checks.
- Implement `SignalCollector` for periodic platform sampling and bounded trends.
- Implement `RuntimeSnapshot` as a stable, typed surfaced state.
- Harden `Kernel.shutdown()` with hard timeouts and final authoritative hash emission.
- Implement operational flag boundaries.

## Out of Scope
- Concurrency observability (M8+).
- Final performance certification (M9).

## Acceptance Criteria
- [x] Engine rejects unsafe profiles before the first tick.
- [x] Memory and compute trends are bounded (O(1) space).
- [x] RSS sampling is periodic ($N$ ticks).
- [x] Shutdown emits final authoritative hash and flushes non-authoritative buffers.
- [x] Unsupported mode-override flags are rejected.
- [x] 100% test pass for visibility and control matrix.

## Related Tickets
- TCK-20260418-RESOURCE-PERSISTENCE-M6 (DONE)

## Related Docs
- `observability_contract_m7.md`
- `m7_operational_controls_matrix.md`
- `m7_test_matrix.md`

## Related Code Areas
- `src/config/validator.py`
- `src/engine/observability.py`
- `src/engine/kernel.py`
- `src/engine/replay_manager.py`

## Assumptions / Open Questions
- Hardware realism is surfaced as a warning in M7, with formal rejection deferred to M9 certification.

## Implementation Notes
- Used `__slots__` in `Kernel` to maintain resource safety while adding the `_collector` attribute.
- Hardened `ReplayManager.finalize()` with try/except to ensure shutdown never hangs on IO failure.

## Test Summary
- 11 new tests added across 4 test modules.
- Verified budget-exhaustion rejection, trend bounding, and graceful shutdown sequencing.

## Files Changed
- `src/config/validator.py`
- `src/engine/observability.py`
- `src/engine/kernel.py`
- `src/engine/replay_manager.py`
- `src/engine/runtime_status.py`

## Completion Summary
Milestone 7 finalized. The engine now has a formal operational control surface. It rejects unsafe configurations at startup, provides stable and bounded runtime visibility via trends and snapshots, and performs deterministic graceful shutdowns that preserve authoritative integrity.
