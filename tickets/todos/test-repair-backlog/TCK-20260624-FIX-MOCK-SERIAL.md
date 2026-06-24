---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260624-FIX-MOCK-SERIAL
phase: open
date: 2026-06-24
tags: [mock, kernel, json-serialization, thread-leak, rng]
---

# TCK-20260624-FIX-MOCK-SERIAL

## Title
Fix MagicMock RNG serialization failure in 7 kernel tests (cascades into 5 teardown thread-leak errors)

## Status
OPEN

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
1. Find the `MagicMock(spec=DeterministicRNG)` instantiation
2. Add: `rng.get_state.return_value = None` (or `{"seed": 0, "counter": 0}`)
3. Wrap Kernel construction in `try/finally: kernel.shutdown()` or convert test to yield fixture

Spurious teardown errors (will clear automatically after this fix):
- `tests/unit/resource/test_transaction_grouping.py::test_group_failure_rollback`
- `tests/unit/certification/test_catalog_scenario_state_builder.py::test_tick_zero_entities_alive`
- `tests/unit/runtime/test_registry_bootstrap_modes.py::test_content_source_report_is_frozen`
- `tests/docs/test_doc_integrity.py::test_link_integrity`
- `tests/integration/perf/test_phase10_graceful_degradation.py::test_recovery_from_degraded_to_normal_when_pressure_drops`

## Test Summary
Run: `pytest tests/unit/core/test_operational_flags.py::test_flags_cannot_alter_authoritative_semantics tests/unit/core/test_signal_truth.py::test_signal_truth_dropped_work tests/unit/kernel/test_replay_contract.py::test_replay_is_non_authoritative tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update tests/integration/kernel/test_kernel_boundaries.py tests/integration/kernel/test_simulation_kernel_contract.py::test_kernel_tick_execution_order -v`

## Files Changed
TBD during implementation

## Completion Summary
TBD
