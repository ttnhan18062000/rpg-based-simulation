# Plan — TCK-20260623-FIX-OBS-QUEUE

## Summary

Two test files create Kernel instances without calling kernel.shutdown(), leaking
daemon threads that accumulate across the pytest session. daemon=True is already set
on QueueDrainWorker (queue.py:112) — it's defense-in-depth for process exit only,
not intra-session cleanup. Fix: add try/finally + kernel.shutdown() in both files.

## Fix 1: tests/unit/kernel/test_replay_contract.py

Wrap the Kernel lifecycle in test_replay_is_non_autoritative() with try/finally:
```python
kernel = Kernel(...)
try:
    for _ in range(5): kernel.tick_once()
    # assertions
finally:
    kernel.shutdown()
```

## Fix 2: tests/perf/test_concurrency_parity.py

run_parity_check() creates kernel_loc and kernel_con without shutting them down.
Keep the existing worker_manager.shutdown() and add kernel_loc.shutdown() + kernel_con.shutdown()
in the same finally block.

## No production code changes.

## Test Commands

```bash
pytest tests/unit/kernel/test_replay_contract.py -q --tb=short
pytest tests/perf/test_concurrency_parity.py -q --tb=short -m "not slow"
# Thread sentinel check (conftest.py:123 will now pass cleanly):
pytest tests/integration/kernel/test_milestone_a_closure.py -q --tb=short
```
