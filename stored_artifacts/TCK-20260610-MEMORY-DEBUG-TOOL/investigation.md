---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260610-MEMORY-DEBUG-TOOL
artifact_type: investigation
tags: [memory, debug, tool]
---

PHASE_TS: 2026-06-10T17:20:00Z

# Investigation: TCK-20260610-MEMORY-DEBUG-TOOL

## Current Behavior

### QueueDrainWorker (src/observability/queue.py:87–143)
- `QueueDrainWorker` is a standalone class (NOT a subclass of `threading.Thread`).
  - `start()` at line 108 creates a `threading.Thread` internally stored as `self._thread`.
  - The thread name is `"observability-drain-worker"` (hardcoded, line 112).
  - Thread is daemon=True (will not block Python exit but does stay alive until `.stop()` is called).
- **Identification strategy**: `isinstance(t, QueueDrainWorker)` will NOT work via `threading.enumerate()`
  because the enumerated objects are `threading.Thread` instances, not `QueueDrainWorker` instances.
  The reliable identification method is thread name matching: `t.name == "observability-drain-worker"`.
  Alternatively, count by `t.name.startswith("observability-drain-worker")` to handle multiple workers.
- Module-level singleton `_global_queue` (line 146) is an `Optional[BoundedObservabilityQueue]`, not a worker.
  No module-level worker singleton exists.
- `stop()` at line 115 sets `self.running = False` and calls `self._thread.join(timeout=1.0)` then sets
  `self._thread = None`.

### EventRecorder (src/observability/event_recorder.py:18–177)
- `EventRecorder.__init__` creates a `QueueDrainWorker` at line 43 and starts it at line 48 if `enabled=True`.
- `shutdown()` at line 155 calls `self._worker.stop()` (line 159), flushes queue, closes file handle.
- `gc.get_objects()` will return all live `EventRecorder` instances — there is no `__del__` or `__slots__`
  suppression that would hide them from gc.
- Creating `EventRecorder(enabled=False)` does NOT start a worker thread.

### Kernel (src/engine/kernel.py)
- `Kernel.__init__` creates an `EventRecorder` at line 222 with `enabled=(obs_mode != ObservabilityMode.OFF)`.
- `Kernel.shutdown()` at line 792 calls `self._event_recorder.shutdown()` (line 796).
- Kernel construction requires `RuntimeProfile`, `AuthoritativeState`, and `DeterministicRNG`.
- Existing pattern in `scripts/profile_engine.py` and `tests/unit/kernel/test_local_executor.py` shows a
  minimal kernel can be built with:
    - `RuntimeProfile(name="...", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, ...)`
    - `AuthoritativeState(tick=0, seed=42, entities={...})` — even empty entities works
    - `DeterministicRNG(42)`
  However, the Kernel `__init__` also touches `ObservabilityConfig`, `RunArtifactRepository`, `ReplayManager`,
  and other subsystems. Using a full Kernel in the test is feasible but heavy.
- For the smoke test in `tests/unit/test_memory_probe.py`, using `EventRecorder` directly (not Kernel) is
  cleaner and avoids filesystem side effects, while still testing the worker lifecycle that is the actual
  concern.

### pyproject.toml
- `psutil>=5.9.0` already in `[project.dependencies]` (line 16).
- `[project.optional-dependencies] dev` exists with pytest, testcontainers, httpx, hypothesis.
- `memray>=1.0.0` is NOT yet present in any section.

### tests/ structure
- `tests/tools/` does NOT exist. Must be created with `__init__.py`.
- `tests/unit/` exists with a flat pattern (`tests/unit/observability/test_event_recorder.py` etc.).
- `tests/__init__.py` exists.

### scripts/ naming conventions
- All scripts are lowercase_underscore.py (e.g., `profile_engine.py`, `run_benchmarks.py`).
- All start with `sys.path.insert(0, str(Path(__file__).parent.parent))` for local imports.

## Mechanics / Engine Constraints
- This is a pure tooling addition (no simulation law or durable state involved).
- No parity ledger entries affected.
- No Mechanics Bible chapters apply.

## Parity Ledger Overlap
- None. Tooling/observability infrastructure only.

## Prior Work
- No prior stored artifacts in `stored_artifacts/` for this exact scope.
- Related ticket TCK-20260610-THREAD-LEAK-CONFTEST covers the conftest sentinel CI integration; this ticket
  builds the underlying counting/profiling primitives that conftest will use.

## Risks and Open Questions
1. **Thread identification**: `isinstance(t, QueueDrainWorker)` does NOT work since enumerated objects are
   `threading.Thread` instances. Use name matching: `t.name == "observability-drain-worker"`.
2. **gc.get_objects() reliability**: Safe for EventRecorder (no __del__, no __slots__ hiding from GC).
   However, note that test isolation matters — if another test in the same session leaves a live
   EventRecorder, count_event_recorders() will over-count. The snapshot_start/end delta approach mitigates
   this.
3. **memray platform**: memray uses C extensions; only Linux/macOS. `--flamegraph` must check
   `sys.platform == 'win32'` and emit a clear message.
4. **memray Tracker API**: `memray.Tracker(output_file)` is a context manager. Usage:
   ```python
   with memray.Tracker("output.bin"):
       # workload
   ```
   Then post-process: `subprocess.run(["python", "-m", "memray", "flamegraph", "output.bin", "-o", "out.html"])`
5. **Kernel in smoke test**: Using a full Kernel for the smoke test introduces filesystem writes and
   observability infrastructure overhead. Prefer testing with `EventRecorder` directly for the worker
   lifecycle assertion — this is the actual leak concern.
6. **tests/tools/__init__.py**: Must be created as an empty file.

## Anti-Drift Hazards
- If `QueueDrainWorker._thread` naming convention changes, `count_drain_workers()` must be updated.
- If memray changes its `Tracker` context manager API, the script needs updating.
- The `EventRecorder(enabled=False)` path must NOT start a worker — confirmed by inspection (line 48: `if self.enabled:`).
