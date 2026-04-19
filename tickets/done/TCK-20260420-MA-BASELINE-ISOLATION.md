# TCK-20260420-MA-BASELINE-ISOLATION

## Title
Isolate Milestone A Baseline from Concurrency Plumbing

## Status
DONE

## Request Summary
The Milestone A baseline is currently entangled with `WorkerPacket` and `WorkerManager`, preventing it from being an isolated "semantic source of truth." This ticket decouples the kernel execution phase into local and concurrent paths.

## Scope
- Define `IWorkExecutor` interface.
- Implement `LocalSequentialExecutor`.
- Implement `ConcurrentExecutionAdapter`.
- Refactor `Kernel._phase_collection` to delegate to the executor.
- Isolate `AuthoritativeState` snapshots.

## Out of Scope
- Real signal source hardening (Milestone B).
- Lifecycle de-simulation (Milestone C).
- Combat/domain expansion.

## Acceptance Criteria
- [x] `Kernel` can run without using `WorkerPacket` or `WorkerManager` in its baseline path. (MA)
- [x] `LocalSequentialExecutor` produces bit-identical results to a single-threaded concurrent run. (MA)
- [x] `Kernel._phase_collection` is reduced in complexity (refactor). (MA)
- [x] Hardened real-time signal sourcing in `WorkerManager`. (MB)
- [x] Real-time peak accounting is thread-safe and accurate. (MB)
- [x] `DRAIN_DEBT` logic is de-simulated and processed via authoritative results. (MC)
- [x] All Milestone A, B, and C tests pass. (ALL)

## Related Tickets
- TCK-20260420-RESOURCE-SUBSTRATE-HARDENING (Parent)

## Related Docs
- resource_implementation_v3_updated.md
- docs/superpowers/specs/2026-04-20-resource-engine-substrate-hardening.md

## Related Code Areas
- src_v2/engine/kernel.py
- src_v2/engine/executor.py (NEW)

## Implementation Notes
- Use `Protocol` for `IWorkExecutor` for flexiblity.
- Ensure `Logic` is shared between `LocalExecutor` and `WorkerLogic`.

## Test Summary
- `tests_v2/engine/test_milestone_a_closure.py`: Isolation & contract purity (PASSED)
- `tests_v2/engine/test_determinism_suite.py`: Bit-identical outcome equivalence (PASSED)
- `tests_v2/engine/test_signal_hardening.py`: Peak-utilization & queue depth accuracy (PASSED)
- `tests_v2/engine/test_milestone_c_desimulation.py`: Authoritative debt drainage (PASSED)

## Files Changed
- `src_v2/engine/kernel.py`
- `src_v2/engine/executor.py`
- `src_v2/engine/worker_manager.py`
- `src_v2/engine/domain_logic.py`
- `src_v2/core/worker_protocol.py`
- `src_v2/core/protocol_validator.py`
- `src_v2/core/updates.py`
- `src_v2/engine/apply.py`
