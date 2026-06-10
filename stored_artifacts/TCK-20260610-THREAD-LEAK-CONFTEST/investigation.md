# Investigation — TCK-20260610-THREAD-LEAK-CONFTEST

## Current Behavior

### tests/conftest.py (full file read)
- File exists at `tests/conftest.py`.
- Contains only function-level hooks: `pytest_addoption`, `pytest_runtest_setup`, `pytest_runtest_teardown`, `pytest_collection_modifyitems`.
- **No session-scoped fixtures exist.** No `@pytest.fixture(scope="session")` is present.
- No thread-counting logic of any kind.
- Safe insertion point: append to end of file after line 106.

### src/observability/queue.py — QueueDrainWorker thread name
- `QueueDrainWorker.start()` at line 112 creates:
  ```python
  self._thread = threading.Thread(target=self._run, daemon=True, name="observability-drain-worker")
  ```
- Thread name is `"observability-drain-worker"` (fixed string, not parameterized).
- This is exactly the name that `count_drain_workers()` in `tests/tools/memory_probe.py` uses.

### tests/tools/memory_probe.py — count_drain_workers()
- Implemented at lines 34–38:
  ```python
  def count_drain_workers() -> int:
      return sum(
          1 for t in threading.enumerate()
          if t.name == "observability-drain-worker"
      )
  ```
- Already solves the detection problem. The conftest fixture only needs to call this helper before and after the session.

## Mechanics / Engine Constraints
- No production mechanics affected. This is test infrastructure only.
- No docs/mechanics or docs/engine constraints apply.

## Parity Ledger Overlap
- `docs/parity_ledger/infrastructure.yaml` covers telemetry/observability/workers.
- Since no production behavior changes, no parity entry needs updating.
- Checked: no existing sentinel fixture or plugin registers thread guards.

## Prior Work
- TCK-20260610-MEMORY-DEBUG-TOOL: implemented `tests/tools/memory_probe.py` including `count_drain_workers()`. This is the helper we depend on.
- TCK-20260610-WORKER-SINGLETON-GUARD: implemented singleton guard and `test_queue_worker_singleton.py`.
- TCK-20260610-KERNEL-TEST-TEARDOWN: fixed actual leaks so the sentinel should pass cleanly once run.

## Risks and Open Questions
- None. The implementation is unambiguous:
  - Thread name is known and stable (`"observability-drain-worker"`).
  - `count_drain_workers()` is already tested and correct.
  - `tests/conftest.py` has no session fixtures — safe to append.
  - The fixture uses `autouse=True` + `yield` pattern so teardown runs even if tests fail.

## Anti-Drift Hazards
- If `QueueDrainWorker` thread name is ever changed in `queue.py`, both `count_drain_workers()` and the sentinel would silently stop detecting leaks. The thread name `"observability-drain-worker"` must be treated as a stable contract.
- The fixture uses `pytest.fail()` not `assert`, which is correct for conftest-level failures.
