---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260610-MEMORY-DEBUG-TOOL
phase: done
date: 2026-06-10
tags: [memory, debug, tool]
---

# TCK-20260610-MEMORY-DEBUG-TOOL

## Title
Build a memory and resource debugging tool with per-function flamegraph support

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Engineers need a tool to diagnose memory growth and resource leaks in the simulation test process — specifically around `QueueDrainWorker` thread accumulation and `EventRecorder` object lifetimes. The tool must support per-function memory recording with flamegraph output (HTML) so engineers can visually identify which call paths allocate the most memory. Use `memray` (Bloomberg's memory profiler, added as a dev dependency) for flamegraph recording; use `tracemalloc` (stdlib) and `psutil` (already in pyproject.toml) for lightweight inline assertions. The tool should be usable two ways: as a standalone script (`python scripts/memory_probe.py`) for ad-hoc debugging with `--flamegraph` output, and as an importable helper in tests for targeted before/after assertions.

## Scope
- Add `memray>=1.0.0` to `[project.optional-dependencies] dev` in `pyproject.toml`
- Create `scripts/memory_probe.py` as the primary entry point:
  - **Default mode**: lightweight report using `tracemalloc` + `psutil` + `threading`
    - Top-N allocation sites by memory (configurable, default 20)
    - RSS before/after delta (`psutil.Process().memory_info().rss`)
    - Active `QueueDrainWorker` thread count (`threading.enumerate()` + `isinstance`)
    - Live `EventRecorder` object count (`gc.get_objects()`)
    - Human-readable stdout report; optional JSON via `--output <path>`
  - **`--flamegraph` mode**: wraps the workload in `memray.Tracker`, then calls
    `memray flamegraph` to produce a self-contained HTML file showing per-function
    allocation sizes as a call-tree heatmap. Output path defaults to
    `reports/memory_flamegraph.html`; overridable via `--output`
  - **`--simulate-leak` flag**: creates N kernels without calling shutdown so the tool
    can demonstrate a real leak; works in both default and `--flamegraph` modes
- Create `tests/tools/memory_probe.py` (thin importable wrapper, no memray dep):
  - `snapshot_start() -> MemorySnapshot` — captures RSS + tracemalloc baseline + thread count
  - `snapshot_end(start: MemorySnapshot) -> MemoryReport` — computes deltas
  - `assert_no_worker_leak(before: int, after: int)` — raises `AssertionError` with counts if after > before
  - Usable inside pytest tests for targeted assertions without the full conftest session fixture

## Out of Scope
- Automatic integration with CI pipeline (see TCK-20260610-THREAD-LEAK-CONFTEST for conftest sentinel)
- Reference-chain / object-graph visualization (objgraph-style) — not needed, flamegraph covers allocation attribution
- Profiling production simulation runs under load — tool is a diagnostic helper, not a performance benchmark
- Modifying `QueueDrainWorker`, `EventRecorder`, or kernel source code
- CPU flamegraphs (py-spy / Austin) — memory only

## Acceptance Criteria
- [ ] `python scripts/memory_probe.py` runs end-to-end and prints a report showing RSS delta, top-20 tracemalloc allocation sites, live `QueueDrainWorker` count, and live `EventRecorder` count
- [ ] `python scripts/memory_probe.py --flamegraph` produces a self-contained HTML file at `reports/memory_flamegraph.html`; opening it in a browser shows a per-function call-tree heatmap of allocations
- [ ] `python scripts/memory_probe.py --simulate-leak --flamegraph` produces a flamegraph where `QueueDrainWorker._run` (or its allocation site) is visibly present, demonstrating an actual leak
- [ ] `memray>=1.0.0` is declared in `[project.optional-dependencies] dev` in `pyproject.toml`; the script raises a clear `ImportError` message if memray is not installed and `--flamegraph` is requested
- [ ] `tests/tools/memory_probe.py` is importable with `from tests.tools.memory_probe import snapshot_start, snapshot_end, assert_no_worker_leak`; it does NOT import memray (no hard dep)
- [ ] A smoke test in `tests/unit/` calls `snapshot_start` / `snapshot_end` around a clean kernel creation+shutdown and asserts worker count delta is 0

## Related Tickets
- TCK-20260610-KERNEL-TEST-TEARDOWN
- TCK-20260610-THREAD-LEAK-CONFTEST

## Related Docs
- None.

## Related Stored Artifacts
None.

## Related Code Areas
- `scripts/memory_probe.py` (new)
- `tests/tools/memory_probe.py` (new)
- `pyproject.toml`
- `src/observability/queue.py`
- `src/observability/event_recorder.py`
- `src/engine/kernel.py`

## Assumptions / Open Questions
- `QueueDrainWorker` threads can be identified by `isinstance(t, QueueDrainWorker)` — requires importing `QueueDrainWorker` from `src.observability.queue`. If that import has side effects, it must be done lazily inside the counting function.
- `gc.get_objects()` can enumerate all live `EventRecorder` instances if the class doesn't suppress `__del__`. This should be confirmed at implementation time.
- The `tests/tools/` directory may not exist yet; it should be created with an `__init__.py`.
- `memray` uses a native C extension and only supports Linux and macOS (not Windows). The `--flamegraph` flag should check platform at runtime and emit a clear message on unsupported platforms rather than crashing.
- `memray.Tracker` can be used as a context manager in-process; this is the integration path rather than `memray run` subprocess wrapping.

## Implementation Notes
- `count_drain_workers()` uses thread name matching (`t.name == "observability-drain-worker"`) not isinstance, because threading.enumerate() returns Thread objects, not QueueDrainWorker objects.
- Workload in scripts/memory_probe.py uses QueueDrainWorker directly (not a full Kernel) to avoid filesystem/observability infrastructure overhead and keep the script self-contained.
- memray import is lazy inside `run_flamegraph_mode()` with a clear ImportError message; `tests/tools/memory_probe.py` has no memray dependency.
- `tests/tools/__init__.py` created as empty file to make the package importable.
- Windows guard added to `--flamegraph` mode (memray is Linux/macOS only).

## Test Summary
- 4 tests in `tests/unit/test_memory_probe.py`: all passing
- `test_clean_recorder_no_worker_leak`: EventRecorder lifecycle, worker_count_delta == 0
- `test_no_raise_when_equal`, `test_raises_when_after_greater`, `test_raises_with_larger_delta`: assert_no_worker_leak helper behavior
- Regression: `tests/unit/observability/test_event_recorder.py` — 2/2 passing

## Files Changed
- `pyproject.toml` — added `memray>=1.0.0` to `[project.optional-dependencies] dev`
- `tests/tools/__init__.py` — new empty package init
- `tests/tools/memory_probe.py` — new importable helpers (MemorySnapshot, MemoryReport, snapshot_start, snapshot_end, assert_no_worker_leak, count_drain_workers, count_event_recorders)
- `scripts/memory_probe.py` — new CLI script with default mode and --flamegraph mode
- `tests/unit/test_memory_probe.py` — new unit tests

## Completion Summary
Built the memory and resource debugging tool: an importable `tests/tools/memory_probe.py` with before/after snapshot helpers (no memray dep), and a CLI `scripts/memory_probe.py` that produces inline tracemalloc/RSS/thread-count reports and optionally wraps workloads in memray.Tracker to generate HTML flamegraphs. Added memray>=1.0.0 to dev dependencies. All 4 new unit tests pass; existing EventRecorder tests unaffected.
