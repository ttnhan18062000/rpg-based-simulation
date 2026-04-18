# Arena Resource Exhaustion Investigation

## Root Cause Analysis

### 1. Retention Cycles (Memory Leaks)
The `WorldLoop` and `TelemetryBridge` create a circular reference cycle:
- `WorldLoop` -> `TelemetryBridge`
- `TelemetryBridge` -> `WorldState` (via `self._world`)
- `WorldState` -> `EventBus`
- `EventBus` -> `TelemetryBridge` (via bound method subscribers like `self.handle_combat`)

While `WorldLoop.shutdown()` calls `telemetry_bridge.detach()`, any failure in the shutdown sequence or incomplete detachment prevents the GC from reclaiming these large objects. In arena runs with hundreds of ticks and multiple iterations, these leaked "dead worlds" accumulate until the 1GB process limit in `conftest.py` is hit.

### 2. Redundant Snapshot Overhead (CPU & Memory)
The `PersistencePhase` currently creates a `Snapshot` and converts entities to "slim schemas" every single tick:
- This happens even if `DISABLE_REDIS=1` and `DISABLE_KAFKA=1` are set, if the check is performed too late in the `execute` method or if it only skips the *transmission* but not the *preparation*.
- `Snapshot.from_world(shallow=True)` is used for performance, but it has a **Cell Size Mismatch BUG**:
    - `Snapshot._SPATIAL_CELL` is hardcoded to **16**.
    - `SimulationConfig.spatial_cell_size` defaults to **8**.
    - Because of this mismatch, `from_world` falls back to rebuilding the spatial index from scratch every tick, iterating over all entities and allocating new lists/dicts.

### 3. "System Crash" (Resource Exhaustion)
The "crash" reported by the USER is likely the `pytest_runtest_teardown` tripwire in `tests/conftest.py` firing:
- `LIMIT_MB = 1024`: Global process limit.
- `DELTA_LIMIT_MB = 150`: Per-test leak limit.
Accumulated leaks from multiple arena iterations easily exceed these boundaries.

## Proposed Fixes

### Phase 1: Lifecycle Hardening (Approved)
- **`WorldLoop.shutdown()`**: Enhance to explicitly nullify `_phases`, `_tick_events`, and `_last_applied`.
- **`EventBus.unsubscribe_all()`**: Ensure it's used to clear all subscribers from a specific handler object.
- **`ArenaRunner`**: Explicitly call `loop.shutdown()` and trigger `gc.collect()` between iterations.

### Phase 2: Performance Optimizations (Approved)
- **`PersistencePhase.execute()`**: Add an early return if Redis and Kafka are both disabled.
- **`Snapshot._SPATIAL_CELL`**: Align with `SimulationConfig.spatial_cell_size` to enable direct spatial data sharing in shallow mode.
- **Spatial Index Reuse**: In `from_world(shallow=True)`, if cell sizes match, share the `_cells` dictionary directly.

### Phase 3: Monitoring & Safety
- **Memory Delta Checks**: Implement per-iteration RSS delta monitoring in `ArenaRunner` (e.g., >50MB growth per iteration = Leak).
- **Mutation Tripwire**: Verify `DecisionPhase` coverage in `WorkerPool` (already present, will keep).

## System Resource Protection Investigation

To prevent `pytest` from crashing the system during long arena simulations, I have investigated several "Safety Fuse" methods:

### 1. OS-Level Hard Limit (`resource.RLIMIT_AS`)
- **Action**: Set a virtual memory limit at the OS level using `resource.setrlimit`.
- **Result**: The process will receive a `MemoryError` if it attempts to allocate beyond the limit.
- **Safety Level**: **HIGH**. This is the ultimate fence that prevents the process from threatening system stability.

### 2. Background Watchdog Thread
- **Action**: A daemon thread in `conftest.py` that monitors process RSS every 100-250ms.
- **Result**: If memory exceeds a "Critical" threshold (e.g., 1024MB), it executes `os._exit(1)`.
- **Safety Level**: **MEDIUM-HIGH**. Faster than waiting for a test to complete. Guaranteed to stop the process immediately.

### 3. Loop-Level Iteration Guards
- **Action**: Check memory growth inside `ArenaRunner` and `WorldLoop` every N ticks.
- **Result**: Gracefully halts the current scenario if memory spikes, allowing partial metrics to be saved.
- **Safety Level**: **LOW-MEDIUM** (diagnostic focus).

## Recommended Strategy: "The Three-Tier Guard"

1. **Tier 1 (Hard Stop)**: Set `RLIMIT_AS` to **2048MB** (2GB) in `pytest_sessionstart`. This ensures the process is killed by the OS before it can swap-lock the machine.
2. **Tier 2 (Watchdog)**: Implement a `ResourceWatchdog` thread in `conftest.py` that checks RSS and exits if it stays above **1024MB** for more than 1 second.
3. **Tier 3 (Iteration Guard)**: Enhance `ArenaRunner` to monitor RSS deltas between iterations and `ticks` to provide structured "Memory exhaustion detected" reports instead of silent crashes.

## Next Steps
1. Update Implementation Plan with Tier 1 and Tier 2 guards.
2. Execute fixes in `tests/conftest.py` and `src/engine/arena/runner.py`.
3. Verify with a "Chaos Test" that deliberately allocations memory.
