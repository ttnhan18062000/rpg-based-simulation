# Test Plan — TCK-20260610-KERNEL-TEST-TEARDOWN

## Verification Approach

### Thread-count verification (manual spot-check)
To confirm a single test leaves no `QueueDrainWorker` thread behind after the fix:

```python
import threading
before = {t.name for t in threading.enumerate()}
# ... run the test ...
after = {t.name for t in threading.enumerate()}
leaked = {t for t in after - before if "drain-worker" in t or "observability" in t}
assert not leaked, f"Leaked threads: {leaked}"
```

This is not added inline to the tests (the ticket scope is teardown only, not monitoring). The TCK-20260610-THREAD-LEAK-CONFTEST ticket owns that pattern.

### Correctness: all existing assertions must pass unchanged
Adding `kernel.shutdown()` to teardown must not alter any test outcome. Shutdown is non-destructive relative to the state already read by assertions: it only stops background workers, flushes queues, and releases resources. The assertions in each test operate on `kernel.state`, `kernel.status`, or other already-computed values before teardown runs.

## Scoped pytest command

Run exactly the affected files (no full suite):

```bash
pytest \
  tests/perf/test_profiler_integrity.py \
  tests/perf/test_dirty_parity.py \
  tests/perf/test_dirty_set_integrity.py \
  tests/arena/test_arena_tactics.py \
  tests/unit/core/test_catalog_smoke_simulation.py \
  tests/unit/core/test_operational_flags.py \
  tests/unit/core/test_engine_integrity.py \
  tests/unit/core/test_signal_truth.py \
  tests/unit/resource/test_resource_intelligence_contract.py \
  tests/unit/kernel/test_worker_equivalence.py \
  tests/unit/kernel/test_replay_determinism.py \
  -v --tb=short -m "not slow"
```

To include slow tests (required for `test_dirty_parity.py`):

```bash
pytest \
  tests/perf/test_profiler_integrity.py \
  tests/perf/test_dirty_parity.py \
  tests/perf/test_dirty_set_integrity.py \
  tests/arena/test_arena_tactics.py \
  tests/unit/core/test_catalog_smoke_simulation.py \
  tests/unit/core/test_operational_flags.py \
  tests/unit/core/test_engine_integrity.py \
  tests/unit/core/test_signal_truth.py \
  tests/unit/resource/test_resource_intelligence_contract.py \
  tests/unit/kernel/test_worker_equivalence.py \
  tests/unit/kernel/test_replay_determinism.py \
  -v --tb=short
```

## Expected outcome
- All tests pass (same pass count as before the change)
- No test status changes from pass to fail
- No new warnings or errors introduced
