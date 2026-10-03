---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260624-FIX-MOCK-SERIAL
phase: done
date: 2026-06-24
tags: [mock, kernel, json-serialization, thread-leak, rng]
---

# TCK-20260624-FIX-MOCK-SERIAL

## Title
Fix MagicMock RNG serialization failure in 7 kernel tests (cascades into 5 teardown thread-leak errors)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
7 kernel/core tests pass `rng=MagicMock(spec=DeterministicRNG)` to `Kernel(...)`. During `tick_once()`, `kernel.py:646` calls `self._rng.get_state()` which returns a `MagicMock` object, stores it in `AuthoritativeState.rng_checkpoint` via the apply path. When `CanonicalStateHasher.to_canonical_json()` serializes state, `json.dumps` raises `TypeError: Object of type MagicMock is not JSON serializable`. The failing Kernel never reaches `shutdown()`, leaving 5 `QueueDrainWorker` threads alive — which then fire the session-scoped conftest sentinel and produce 5 spurious teardown ERRORs on unrelated tests.

## Scope
- Add `rng.get_state.return_value = None` (or a real serializable checkpoint dict) to every test that passes a `MagicMock(spec=DeterministicRNG)` to `Kernel`
- Ensure each such test's Kernel is shut down after the test (via `try/finally` or `yield` fixture)
- The 5 "teardown ERROR" tests listed below are NOT the cause — they will clear automatically once the 7 MagicMock tests stop leaking threads

## Out of Scope
- Changing `CanonicalStateHasher` serialization logic
- Changing how `rng_checkpoint` is stored in `AuthoritativeState`

## Acceptance Criteria
- All 7 listed tests pass without `TypeError`
- No `QueueDrainWorker thread leak detected` errors in the test session when these 7 tests run together
- The 5 previously-spurious teardown ERRORs also clear

## Related Tickets
- TCK-20260610-KERNEL-TEST-TEARDOWN (prior thread-leak fix for 11 other files)
- TCK-20260623-FIX-ARENA (harness kernel shutdown fix)

## Related Docs
- docs/engine/kernel.md (6-phase loop)
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None

## Related Code Areas
- `src/engine/kernel.py:646` — `self._rng.get_state()` stores into `rng_checkpoint`
- `src/engine/checkpoint.py` — `CanonicalStateHasher.to_canonical_json()` serializes `rng_checkpoint`
- `tests/unit/core/test_operational_flags.py`
- `tests/unit/core/test_signal_truth.py`
- `tests/unit/kernel/test_replay_contract.py`
- `tests/integration/kernel/test_authoritative_outcome_truth.py`
- `tests/integration/kernel/test_kernel_boundaries.py` (2 tests)
- `tests/integration/kernel/test_simulation_kernel_contract.py`

## Assumptions / Open Questions
- `rng.get_state.return_value = None` is the minimal fix; if the hasher explicitly checks for `None` and raises, a serializable dict `{"seed": 0, "counter": 0}` is the alternative
- Confirm that `DeterministicRNG.get_state()` is the only MagicMock method that returns a non-serializable value in these tests

## Implementation Notes
For each test:
1. Found each `MagicMock(spec=DeterministicRNG)` or `MagicMock()` used as rng
2. Added `rng.get_state.return_value = None` immediately after construction — None serializes as JSON null; checkpoint.py has no non-null assertion
3. Added `try/finally: kernel.shutdown(timeout_s=1.0)` in all tests that were missing teardown
4. In `test_authoritative_outcome_truth.py` `mock_deps` fixture: also added `replay.finalize.return_value = LifecycleOutcome.SUCCESS` and `replay.replay_metrics.return_value = {"pending_replay_flushes": 0}` to prevent MagicMock comparison TypeError in kernel.shutdown(); also raised `max_tick_budget_ms` from 100 to 10000 to prevent mid-tick throttle from dropping the resolution work before REFINED_UPDATE is emitted
5. In `test_replay_contract.py`: converted inline `rng=MagicMock()` to a named variable to allow the stub to be set

Spurious teardown errors cleared:
- `tests/unit/resource/test_transaction_grouping.py::test_group_failure_rollback`
- `tests/unit/certification/test_catalog_scenario_state_builder.py::test_tick_zero_entities_alive`
- `tests/unit/runtime/test_registry_bootstrap_modes.py::test_content_source_report_is_frozen`
- `tests/docs/test_doc_integrity.py::test_link_integrity`
- `tests/integration/perf/test_phase10_graceful_degradation.py::test_recovery_from_degraded_to_normal_when_pressure_drops`

## Test Summary
Run: `pytest tests/unit/core/test_operational_flags.py::test_flags_cannot_alter_authoritative_semantics tests/unit/core/test_signal_truth.py::test_signal_truth_dropped_work tests/unit/kernel/test_replay_contract.py::test_replay_is_non_authoritative tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update tests/integration/kernel/test_kernel_boundaries.py tests/integration/kernel/test_simulation_kernel_contract.py::test_kernel_tick_execution_order -v`

## Files Changed
- tests/unit/core/test_operational_flags.py — added rng.get_state.return_value = None
- tests/unit/core/test_signal_truth.py — added rng.get_state.return_value = None to all 4 rng-using tests
- tests/unit/kernel/test_replay_contract.py — named rng variable + added get_state stub
- tests/integration/kernel/test_authoritative_outcome_truth.py — named rng + get_state stub; replay.finalize/replay_metrics stubs; raised max_tick_budget_ms; try/finally shutdown
- tests/integration/kernel/test_kernel_boundaries.py — get_state stub in mock_rng fixture; try/finally shutdown in both tests
- tests/integration/kernel/test_simulation_kernel_contract.py — get_state stub + try/finally shutdown

## Completion Summary
All 7 target tests now pass. Added `rng.get_state.return_value = None` to 6 test files (covering all 7 failing tests), and added `kernel.shutdown(timeout_s=1.0)` in try/finally blocks wherever Kernel was constructed without teardown. The 5 spurious cascade teardown ERRORs (QueueDrainWorker thread leaks) also cleared. Total: 7 primary + 5 cascade = 12 tests now green. No production source files modified.
