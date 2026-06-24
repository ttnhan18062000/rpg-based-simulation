---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-WORKER-SHUTDOWN
phase: open
date: 2026-06-24
tags: [kernel, shutdown, thread-leak, worker-harden, test-teardown]
---

# TCK-20260624-FIX-WORKER-SHUTDOWN

## Title
Add kernel.shutdown() teardown to test_worker_harden.py

## Status
OPEN

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
Standard pattern:
```python
def test_duplicate_entity_update_rejection():
    kernel = Kernel(...)
    try:
        with pytest.raises(ProtocolViolationError):
            # trigger duplicate entity update
            ...
    finally:
        kernel.shutdown()
```
Or yield fixture approach:
```python
@pytest.fixture
def kernel(profile, state):
    k = Kernel(profile, state, DeterministicRNG(state.seed))
    yield k
    k.shutdown()
```

## Test Summary
Run: `pytest tests/unit/kernel/test_worker_harden.py -v --tb=short`

## Files Changed
TBD

## Completion Summary
TBD
