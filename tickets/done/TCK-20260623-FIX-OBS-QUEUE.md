---
status: done
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-OBS-QUEUE
phase: done
date: 2026-06-23
tags: [test-repair, observability, queue, thread, crash, SIGABRT]
---

# TCK-20260623-FIX-OBS-QUEUE

## Title
Fix observability queue thread leak causing SIGABRT crash at ~68% test run

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The full test suite (`pytest tests/ -m "not slow"`) crashes at approximately 68% with
`Fatal Python error: Aborted` (exit code 134 = SIGABRT). At crash time, dozens of threads
are still alive all blocked at `src/observability/queue.py:142` (`_run` method).

```
Fatal Python error: Aborted
Thread 0x... (most recent call first):
  File ".../src/observability/queue.py", line 142 in _run
  File ".../threading.py", line 994 in run
  ...
(50+ identical threads)
```

The thread accumulation pattern indicates that `ObservabilityQueue` (or a similar worker
class at `queue.py`) spawns a thread per test (or per simulation run) but never joins or
stops those threads. Over 68% of the test suite, enough threads accumulate to trigger
the OS abort (Linux limits threads per process, typically ~32768, or the process OOM-kills).

This crash prevents the full test suite from running and masks the true final failure count.

**Immediate workaround:** running tests by subdirectory avoids the crash (each subprocess
has fewer threads). The suite can be validated subdirectory-by-subdirectory until this is fixed.

## Scope
- Read `src/observability/queue.py:_run` and surrounding class to understand the thread lifecycle
- Find where `ObservabilityQueue` (or equivalent) is instantiated in tests — likely missing a
  `stop()` / `join()` in test teardown
- Add a `conftest.py` autouse fixture (or fix the queue class's `__del__` / `stop()` method)
  to ensure queue threads are stopped after each test that creates one
- If the queue class has no `stop()` method, add one that sets a shutdown event and joins the thread
- Verify that the thread count does not grow unboundedly across 500+ tests

## Out of Scope
- Observability queue feature changes
- Changing what gets logged
- Performance of the queue

## Acceptance Criteria
- Full `pytest tests/ -m "not slow"` run completes without SIGABRT (exit code 0 or test failures,
  not process abort)
- Thread count at end of test run is within normal bounds (< 50 active threads)
- `tests/observability/` still passes (no regression from the thread fix)

## Related Tickets
- TCK-20260623-FIX-DOCS-INTEGRITY (integration/observability/test_scenario_level_report_flow
  CI gate failure — separate, may resolve independently)

## Related Docs
- `docs/architecture/adr-004` (watchdog / observability)
- `docs/parity_ledger/infrastructure.yaml`

## Related Code Areas
- `src/observability/queue.py:142` (`_run` method — thread entry point)
- `src/observability/` (who instantiates the queue and when)
- `tests/conftest.py` or domain-level conftest (where to add teardown fixture)
- `tests/observability/` (existing observability tests — must stay green)

## Assumptions / Open Questions
- Is `queue.py:142` a `while True: queue.get()` loop with no shutdown event?
- Is the thread started with `daemon=False`? (daemon threads auto-die; non-daemon threads survive)
- Which test or fixture creates the queue? Is it a module-level singleton?

## Implementation Notes
Investigation order:
1. Read `src/observability/queue.py` fully — find thread start, `_run` loop, and any `stop()` method
2. Search for where queue is instantiated in tests or production code called by tests
3. Check if `daemon=True` is set on thread creation (quick fix if not)
4. If no shutdown: add `stop()` method with `threading.Event` sentinel + `thread.join()`
5. Add autouse fixture in `tests/conftest.py` or `tests/observability/conftest.py` that calls `stop()`

Quickest fix: if the thread is created with `daemon=False`, changing to `daemon=True` makes
it auto-terminate when the main thread ends — but this only works if the thread lifecycle
is truly fire-and-forget (no data loss on abort).

## Test Summary
Run: `pytest tests/ -m "not slow" -q --tb=no` — should complete without SIGABRT.
Also run: `pytest tests/observability/ --tb=short` — must stay green.

## Files Changed
- `tests/unit/kernel/test_replay_contract.py` — wrapped Kernel lifecycle in try/finally + kernel.shutdown()
- `tests/perf/test_concurrency_parity.py` — wrapped kernel_loc and kernel_con in try/finally + shutdown; moved worker_manager.shutdown() to kernel_con finally block
- `tests/integration/kernel/test_milestone_a_closure.py` — wrapped Kernel tick in try/finally + kernel.shutdown()

## Completion Summary
Root cause: daemon=True was already set on QueueDrainWorker threads; the leak was 3 test files creating Kernel instances without calling kernel.shutdown(). Added try/finally teardown in all 3. Thread sentinel (conftest.py:123) now passes cleanly. No production code changes required.
