PHASE_TS: 2026-06-10T17:21:00Z

# Plan: TCK-20260610-MEMORY-DEBUG-TOOL

## Ordered Steps

### Step 1 — Add memray to pyproject.toml
**File**: `pyproject.toml`
- In `[project.optional-dependencies] dev`, append `"memray>=1.0.0"` after existing entries.
- No other changes.
- Verifiable: `grep memray pyproject.toml` returns a match.

### Step 2 — Create tests/tools/__init__.py
**File**: `tests/tools/__init__.py` (new, empty)
- Required so `tests/tools/` is a package importable as `from tests.tools.memory_probe import ...`.
- Verifiable: file exists, python -c "from tests.tools import memory_probe" succeeds.

### Step 3 — Create tests/tools/memory_probe.py
**File**: `tests/tools/memory_probe.py` (new)
- Dataclasses: `MemorySnapshot(rss_bytes, tracemalloc_snapshot, worker_thread_count, event_recorder_count, timestamp)`, `MemoryReport(rss_delta_bytes, top_allocations, worker_count_delta, event_recorder_delta)`.
- `count_drain_workers() -> int`: `threading.enumerate()` + name match `"observability-drain-worker"`.
- `count_event_recorders() -> int`: `gc.get_objects()` + `isinstance(o, EventRecorder)`.
- `snapshot_start() -> MemorySnapshot`: calls tracemalloc.start() if not started, captures RSS, counts.
- `snapshot_end(start: MemorySnapshot) -> MemoryReport`: takes snapshot, computes deltas, formats top allocations.
- `assert_no_worker_leak(before: int, after: int)`: raises AssertionError with message if after > before.
- NO memray import anywhere in this file.
- Verifiable: import succeeds without memray installed.

### Step 4 — Create scripts/memory_probe.py
**File**: `scripts/memory_probe.py` (new)
- `sys.path.insert(0, str(Path(__file__).parent.parent))` at top.
- argparse: `--flamegraph` (store_true), `--simulate-leak` (store_true), `--output PATH`, `--top-n INT` (default 20), `--leak-count INT` (default 3).
- `run_workload(simulate_leak, leak_count)`: creates 1 `QueueDrainWorker` + starts it; if `--simulate-leak` creates `leak_count` additional workers without stopping; otherwise stops the worker. Used as the measurable workload.
  - Rationale: A full Kernel requires many subsystems (artifact repo, filesystem writes, profile validation). Using QueueDrainWorker directly is cleaner for a diagnostic script and directly demonstrates the leak.
- Default mode: calls `snapshot_start()`, runs workload, calls `snapshot_end()`, prints human-readable report.
  - RSS delta, top-N allocation sites, worker count delta, EventRecorder delta.
  - If `--output PATH`: writes JSON report.
- `--flamegraph` mode:
  - Check `sys.platform == 'win32'` → print message and exit(1).
  - Lazy import: `try: import memray except ImportError: print("memray not installed ..."); exit(1)`.
  - Compute output paths: `bin_path = output or "reports/memory_probe.bin"`, `html_path = output or "reports/memory_flamegraph.html"` (if output ends in .html, use it for html; otherwise derive).
  - `with memray.Tracker(bin_path): run_workload(...)`.
  - `subprocess.run(["python", "-m", "memray", "flamegraph", bin_path, "-o", html_path], check=True)`.
  - Print path to HTML.
- Verifiable: `python scripts/memory_probe.py --help` succeeds; default mode prints report.

### Step 5 — Create tests/unit/test_memory_probe.py
**File**: `tests/unit/test_memory_probe.py` (new)
- Import from `tests.tools.memory_probe`.
- `test_clean_recorder_no_worker_leak`: EventRecorder lifecycle + assert delta == 0.
- `test_assert_no_worker_leak_raises`: assert_no_worker_leak(0, 1) raises AssertionError with "1" in message.
- Verifiable: `pytest tests/unit/test_memory_probe.py -v` passes.

## Dependency Map
- Step 2 must precede Step 3 (package must exist before module).
- Step 3 must precede Step 4 (script imports from tests.tools.memory_probe).
- Step 3 must precede Step 5 (test imports from tests.tools.memory_probe).
- Steps 1 and 2 are independent.

## Explicit Scope Guards (What NOT to Touch)
- Do NOT modify `src/observability/queue.py`, `src/observability/event_recorder.py`, or `src/engine/kernel.py`.
- Do NOT add to existing test files.
- Do NOT import memray in `tests/tools/memory_probe.py`.
- Do NOT add a conftest entry (that is TCK-20260610-THREAD-LEAK-CONFTEST scope).

## AC Mapping
| AC | Step |
|----|------|
| memray in pyproject.toml dev | Step 1 |
| tests/tools/memory_probe.py importable without memray | Steps 2, 3 |
| scripts/memory_probe.py default mode prints report | Step 4 |
| --flamegraph produces HTML | Step 4 |
| clear ImportError message if memray absent | Step 4 |
| smoke test worker delta == 0 | Step 5 |

## Deviations
(none yet)
