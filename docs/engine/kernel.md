---
status: active
layer: engine
authority: P1
audience: developer
---

# Simulation Kernel Loop

The `Kernel` is the heartbeat of the RPG V2 Engine. It orchestrates the deterministic, tick-based execution of all simulation systems.

## The 6-Phase Kernel Loop

Every simulation "Tick" follows a strict 6-phase sequence to ensure determinism and prevent race conditions.

| Phase | Name | Responsibility | Concurrency |
| :--- | :--- | :--- | :--- |
| 1 | **Initialization** | Prepare the tick context and snapshot state. | Synchronous |
| 2 | **Governance** | Apply world-level laws (Time, Weather, Global Events). | Synchronous |
| 3 | **Scheduling** | Determine which entities act in this tick (Cadence). | Synchronous |
| 4 | **Deliberation** | Workers generate `StateUpdate` proposals based on state. | **Concurrent** |
| 5 | **Resolution** | Refine proposals through the `AuthoritativeApplyPipeline`. | Synchronous |
| 6 | **Persistence** | Commit the new state and emit telemetry events. | Synchronous |

---

## The "Law of Ticks"

> [!IMPORTANT]
> **Deterministic Order**: Within the `Resolution` phase, entities are processed in a deterministic order (usually sorted by ID) to ensure that the outcome of a tick is identical given the same input state and seed.

| 1 | **Initialization** | Reset tick stats, collect hardware signals, and evaluate Governor policy. | Synchronous |
| 2 | **Scheduling** | Select which entities act this tick based on readiness and priority. | Synchronous |
| 3 | **Collection** | Workers execute "thought" processes and generate proposals. | **Concurrent** |
| 4 | **Resolution** | Collapse all proposals through the `AuthoritativeApplyPipeline`. | Synchronous |
| 5 | **Cleanup** | Finalize performance telemetry and hardware stats. | Synchronous |
| 6 | **Advancement** | Update world clock and commit the new state to the main container. | Synchronous |
| 7 | **Persistence** | Calculate state hashes and emit Replay trace events. | Synchronous |

---

## 🛡️ The "Stability Guard" Law
When running in `audit_mode`, the Kernel enforces strict isolation.
- **Fingerprinting**: At the start of the tick, a SHA-256 fingerprint of the entire world is captured.
- **Verification**: After non-mutating phases (Scheduling, Collection), the fingerprint is re-verified.
- **Halt Law**: If the hash changes during a read-only phase, the Kernel triggers an **Immediate Halt** to prevent state corruption and identify "leakage" in system logic.

## 🛡️ The "Hard Law Compliance Guard" Law
During the **Advancement** phase, before the state is committed and persisted:
- **Active Validation**: The Kernel invokes the `HardLawMonitor` on the tick's `dirty_set` and refined state.
- **Mode-Specific Policies**:
  - **`LIGHT`**: Increments cumulative counts and logs structured warnings without aborting tick progression.
  - **`DEBUG` / `CERTIFICATION`**: Immediately throws `HardLawViolationError` and halts loop execution, preventing the corrupt state from being persisted or exposed to APIs.

## ⚡ Concurrency & The Resolution Bottleneck

- **Concurrent Collection**: Phase 3 is the only window for parallel execution. Workers analyze the world state in parallel using **Immutable Snapshots**.
- **The Singular Bottleneck**: Phase 4 is the definitive point of truth. All proposals are sorted (by Class Priority, then Local Priority, then ID) to ensure bit-identical resolution regardless of worker execution order.

---

## 📈 Observability & Telemetry
The Kernel maintains a `TickAudit` record for every cycle, capturing:
- **Phase Costs**: Millisecond duration of each phase for bottleneck analysis.
- **Rejection Delta**: Count of proposals rejected by the refinement pipeline.
- **Compute Ratio**: Current tick duration vs. the allowed `max_tick_budget_ms`.

### Emergency Throttling
If a tick exceeds 2x its average duration or the hard cap in `RuntimeProfile`, the Kernel will:
1. Signal the Governor to transition to **DEGRADED** mode.
2. Drop remaining work items in the current resolution queue.
3. Log a "Tick Budget Violated" warning with phase-by-phase cost breakdown.

---

## 🔒 Content Hot-Path Guard (WORLD-CAT-004)

`CatalogRepository.load_all()` is forbidden during a kernel tick. The Kernel sets a thread-local flag `_tick_context_active.active = True` inside `tick_once()` and clears it in a `finally` block. If `load_all()` is called while the flag is set, `ContentHotPathViolation(RuntimeError)` is raised immediately.

**Warmup**: `Kernel.__init__()` calls `ContentWarmupService.warmup()` after validation to eagerly load all content singletons before the first tick. This guarantees the hot-path guard never fires under normal operation.

---

## 📊 Resource Snapshot and Lifecycle Supervisor

### `Kernel.resource_snapshot() -> list[SubsystemPressureReport]`
Collects advisory `pressure_report()` from all owned subsystems (event recorder, replay). Errors per subsystem are swallowed — this is a read-only diagnostic method, never called on the tick hot path.

### `Kernel.shutdown() → ShutdownResult` + `Kernel.shutdown_report() → ShutdownReport`
`shutdown()` return type is unchanged (`ShutdownResult`). After shutdown, `shutdown_report()` returns a cached `ShutdownReport` with:
- `workers_started` / `workers_stopped` — lifecycle accounting
- `pending_replay_flushes` — from `ReplayManager.replay_metrics()`
- `survival_event_counts` — from `EventRecorder._survival_event_counts`
- `open_file_handles` — from `psutil` (or -1 if unavailable)
- `outcome` — `"SUCCESS"` / `"PARTIAL"` / `"FAILED"`
- `warnings` — list of advisory strings

`BehaviorWorker` threads (named `"behavior-normalization-worker"`) are joined with a 1-second timeout during shutdown. Non-stop generates `outcome = "PARTIAL"` and a warning entry.
