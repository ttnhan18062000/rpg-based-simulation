---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-WORKER-SHUTDOWN
phase: done
date: 2026-06-24
tags: [kernel, shutdown, thread-leak, worker-harden, test-teardown]
---

# TCK-20260624-FIX-WORKER-SHUTDOWN

## Title
Add kernel.shutdown() teardown to test_worker_harden.py

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/unit/kernel/test_worker_harden.py::test_duplicate_entity_update_rejection` creates a `Kernel` instance but never calls `shutdown()`. The `QueueDrainWorker` thread is left running, triggering the session-scoped conftest sentinel with a teardown ERROR.

Separately confirmed: the `ProtocolViolationError` validation EXISTS at `src/engine/kernel.py:542–543` — the test's `pytest.raises(ProtocolViolationError)` assertion would pass if not for the teardown error masking it. This is the same class of fix as `TCK-20260610-KERNEL-TEST-TEARDOWN`.

Also check other tests in the file (`test_neighbor_view_sorting`, etc.) for the same missing shutdown.

## Scope
- Add `kernel.shutdown()` in a `try/finally` block (or convert to `yield` fixture) for every test in `test_worker_harden.py` that creates a `Kernel` instance
- Verify the `ProtocolViolationError` assertion actually passes once teardown is clean

## Out of Scope
- Changing the duplicate-update validation logic in `kernel.py`

## Acceptance Criteria
- `test_duplicate_entity_update_rejection` passes (both the assertion AND no teardown ERROR)
- No `QueueDrainWorker thread leak detected` from this file
- No regression in other worker harden tests

## Related Tickets
- `TCK-20260610-KERNEL-TEST-TEARDOWN` — prior fix for 11 other files

## Related Docs
- `docs/testing/observability_coverage.md` — worker lifecycle leak regression section

## Related Code Areas
- `tests/unit/kernel/test_worker_harden.py`
- `src/engine/kernel.py:542–543` — `ProtocolViolationError` duplicate-entity check

## Implementation Notes
All three tests in the file construct `Kernel` inline and none had `shutdown()` teardown. Two root causes were fixed:

1. **Thread leak**: Added `try/finally: kernel.shutdown(timeout_s=1.0)` to all three tests.

2. **Emergency throttle masking the duplicate check**: `_phase_resolution()` checks elapsed time at `i % 10 == 0` (i=0 on first result). With `max_tick_budget_ms=10.0`, the kernel init + import overhead (~35ms) caused the throttle to fire before the duplicate-entity check at line 542 was ever reached. Fixed by constructing with `flags={"audit_mode": True}` for the two tests that call `_phase_resolution()` directly — `audit_mode` disables the throttle guard (line 513: `not self._audit_mode`).

## Test Summary
Run: `pytest tests/unit/kernel/test_worker_harden.py -v --tb=short`
Result: 3 passed, 0 errors

Broader suite: `pytest tests/unit/kernel/ -q`
Result: 53 passed in 6.21s

## Files Changed
- `tests/unit/kernel/test_worker_harden.py` — Added `try/finally kernel.shutdown(timeout_s=1.0)` to all 3 tests; added `flags={"audit_mode": True}` to the 2 tests that invoke `_phase_resolution()` directly

## Completion Summary
Added `kernel.shutdown(timeout_s=1.0)` teardown in `try/finally` blocks to all three Kernel-creating tests in `test_worker_harden.py`. Also added `flags={"audit_mode": True}` to prevent the mid-tick emergency throttle from masking the duplicate-entity ProtocolViolationError check in `test_duplicate_entity_update_rejection` and guarding `test_priority_sorted_results` against flaky throttle interference. All 3 tests now pass and 53/53 kernel unit tests pass with no teardown errors.
