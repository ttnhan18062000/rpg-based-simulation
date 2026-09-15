---
status: active
layer: engine
authority: P1
audience: developer
---

# Simulation Kernel Loop

The `Kernel` is the heartbeat of the RPG V2 Engine. It orchestrates the deterministic, tick-based execution of all simulation systems.

## The 7-Phase Kernel Loop

Every simulation "Tick" follows a strict 7-phase sequence to ensure determinism and prevent race conditions.

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

## ⚠️ The "Sticky-Task" Law (decisions are made once; tasks persist)

> [!IMPORTANT]
> **A gate, filter, or policy placed at a decision point only sees the tick a decision is first
> made — not every tick the resulting task executes.** This is a structural property of the
> Scheduling phase, not specific to any one system, and it will silently defeat any check placed
> at the wrong point in the pipeline.

`_phase_scheduling()` (`src/engine/kernel.py`) calls `DeterministicScheduler.select_work()`
(`src/engine/scheduler.py`), which inspects `entity.task.work_kind`: if it is **already**
`ENTITY_ACT` or `ENTITY_MOVE`, the entity is re-scheduled as that same work kind again —
**without re-invoking the decision system** (`SimulationDomainLogic.execute_brain()` /
`TacticalDecisionSystem.evaluate_entity_intent()`). Only an entity with no active task (or one
whose task has just completed) goes through the decision path (`ENTITY_BRAIN` work kind) this
tick. `_phase_collection()`'s executor (`src/engine/executor.py`) then dispatches `ENTITY_ACT`
work straight to `SimulationDomainLogic.execute_action()`, bypassing `execute_brain()` entirely.

**Confirmed by direct measurement** (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-
EXECUTION`): in the reference metropolis scenario, 93.7% of real attacks had no same-tick call to
the decision function at all — they were repeat executions of a decision made on an earlier tick.
A gate placed inside the decision function itself measured **zero effect** on real outcomes for
this reason, even though the policy it implemented was correct.

**Implication for anyone gating a decision-then-task mechanism** (combat, movement, any future
system with the same shape): a check placed at the decision point only governs the tick a fresh
decision happens. To actually govern every tick a task executes — including sticky repeats — the
check must live at the real per-execution dispatch point (e.g. the domain action router,
`src/engine/domain/action_router.py`'s `execute_action()`), not at the decision point. Measure
whether the gate's own instrumentation fires on the same tick as the outcome it's meant to gate
before trusting a "no effect" result — a decision-point gate showing zero effect is exactly what
this law predicts, not evidence the gate's policy is wrong.

---

## 🛡️ The "Stability Guard" Law

The Kernel enforces a two-tier isolation model for read-only phases (Scheduling, Collection):

**Tier 1 — Gross Isolation Guard (all run modes)**
`_guard_gross_isolation()` runs unconditionally in standard (non-audit) mode after each read-only phase. It checks `len(state.entities)` and `state.tick` — two O(1) integer reads with negligible overhead. Detects entity creation/deletion mid-phase and tick advancement outside the authoritative pipeline. Field-level mutations within existing entities are **not** detected.

**Tier 2 — Full Stability Guard (audit_mode=True only)**
`_guard_stability()` is active only when `Kernel` is initialized with `audit_mode=True` (used in certification scenarios). It:
- **Fingerprints**: At the start of the tick, a SHA-256 fingerprint of the entire world is captured.
- **Verifies**: After non-mutating phases (Scheduling, Collection), the fingerprint is re-verified.
- **Halt Law**: If the hash changes during a read-only phase, the Kernel triggers an **Immediate Halt** to prevent state corruption and identify "leakage" in system logic.

**Detection coverage summary:** See `docs/engine/known_limitations.md` §2.3 for the full violation-type matrix. Isolation breaches that change only entity field values (not count or tick) are invisible in standard runs — `audit_mode=True` is required for complete enforcement.

## 🛡️ The "Hard Law Compliance Guard" Law
During the **Advancement** phase, before the state is committed and persisted:
- **Active Validation**: The Kernel invokes the `HardLawMonitor` on the tick's `dirty_set` and refined state.
- **Mode-Specific Policies**:
  - **`LIGHT`**: Increments cumulative counts and logs structured warnings without aborting tick progression.
  - **`DEBUG` / `CERTIFICATION`**: Immediately throws `HardLawViolationError` and halts loop execution, preventing the corrupt state from being persisted or exposed to APIs.

## ⚡ Concurrency & The Resolution Bottleneck

- **Concurrent Collection**: the Deliberation phase is the only window for parallel execution. Workers analyze the world state in parallel using **Immutable Snapshots**.
- **The Singular Bottleneck**: the Resolution phase is the definitive point of truth. All proposals are sorted (by Class Priority, then Local Priority, then ID) to ensure bit-identical resolution regardless of worker execution order.

See also: [`docs/architecture/kernel_concurrency_design_philosophy.md`](../architecture/kernel_concurrency_design_philosophy.md)
for the full design-philosophy narrative behind this section — why Collection is fork-join instead
of asyncio/anyio, how race-safety is structurally enforced, and how the RuntimeMode ladder degrades
gracefully under load.

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
`shutdown()` return type is unchanged (`ShutdownResult`, `src/core/lifecycle.py`), which carries:
- `final_tick` / `final_hash` — the run's last tick and its final canonical SHA-256
- `replay_outcome` / `overall_outcome` — `LifecycleOutcome` (`SUCCESS`/`TIMEOUT`/`SKIPPED`/`FAILED`)
- `failure_reason` — optional failure detail string
- `verification_level` — `"FULL"` or `"REDUCED"`; see "State Hashing in Phase 7" below and
  `docs/engine/known_limitations.md §2.4`

After shutdown, `shutdown_report()` returns a cached `ShutdownReport` with:
- `workers_started` / `workers_stopped` — lifecycle accounting
- `pending_replay_flushes` — from `ReplayManager.replay_metrics()`
- `survival_event_counts` — from `EventRecorder._survival_event_counts`
- `open_file_handles` — from `psutil` (or -1 if unavailable)
- `outcome` — `"SUCCESS"` / `"PARTIAL"` / `"FAILED"`
- `warnings` — list of advisory strings

`BehaviorWorker` threads (named `"behavior-normalization-worker"`) are joined with a 1-second timeout during shutdown. Non-stop generates `outcome = "PARTIAL"` and a warning entry.

**Shutdown ordering (EventRecorder before QualityPersistence)**: `EventRecorder.shutdown()`
(which stops its `QueueDrainWorker` background thread and runs its own final synchronous drain)
MUST complete before the SimQ `QualityHub`'s `QualityPersistence.shutdown()` runs. The drain
worker calls `quality_fn` (`QualityHub.on_envelope` → `QualityPersistence.write()`) on a
background thread; if `QualityPersistence.shutdown()` closed its file handle first, an in-flight
write racing that teardown would previously find `self._file_handle is None` and silently no-op
rather than persisting or erroring. `Kernel.shutdown()` now calls `_event_recorder.shutdown()`
strictly before the `_quality_hub`/`_persistence` block; `EventRecorder.shutdown()`'s final manual
drain also routes each remaining envelope through `quality_fn` (not just file/stream writes), and
`QualityPersistence.write()` logs a loud warning (rather than staying silent) if a write is ever
still attempted after its file handle has closed. See
`TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD` and
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-249`.

---

## State Hashing in Phase 7 (Persistence)

Phase 7 emits a `TICK_END` replay event whose `hash` field is either a SHA-256 canonical
hash or the sentinel string `"SKIPPED"`, depending on the active `GovernorPolicy`:

```
NORMAL / CONSTRAINED  →  replay_richness = "FULL"   →  TICK_END.hash = SHA-256
DEGRADED              →  replay_richness = "MINIMAL" →  TICK_END.hash = "SKIPPED"
SURVIVAL              →  replay_allowed  = False      →  no TICK_END event
```

The **canonical hash** (`CanonicalStateHasher.get_hash()`) is a full SHA-256 over all
authoritative state fields — entities, regions, resources, buildings, groups, RNG
checkpoint, and more. It is the complete determinism proof. In NORMAL and CONSTRAINED
modes it runs every tick.

The **lightweight fingerprint** (`StateFingerprinter.get_fingerprint()`) is an MD5 over
the most gameplay-visible state (entities, strategic state, resources, regions, groups).
It is emitted in `REFINED_UPDATE` events in all replay-enabled modes (NORMAL, CONSTRAINED,
DEGRADED). It is NOT a complete determinism proof — buildings, corpses, ground items,
chests, home storage, camps, tile indices, work debt, and the RNG checkpoint are excluded.

**Shutdown always emits the final canonical hash** regardless of runtime mode.

See `docs/engine/known_limitations.md §2.4` for the mode-by-mode table and the full list
of fingerprint domain gaps. See `docs/engine/deterministic_execution.md` for the
determinism contract and divergence detection tools.

These per-tick gates stay deliberately conditional — they are never made unconditionally
always-on. Instead, `Kernel.shutdown()` derives a run-level `verification_level`
(`"FULL"` / `"REDUCED"`) from `RuntimeStatus.max_mode_reached`, the worst `RuntimeMode`
reached at any point in the run, and surfaces it on `ShutdownResult.verification_level`,
`RunManifest.verification_level`, and `run_report.json`/`.md`'s
`metadata.verification_level`. See `docs/engine/known_limitations.md §2.4` (subsection
"Run-level `verification_level` label") for the full derivation and rationale.
(TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC, INFRA-363.)

## Phase Domain Permissions

Each phase declares allowed read, write, and emit state domains. Declarations are in `src/engine/phase_domain_permissions.py` and enforced by `tests/architecture/test_phase_domain_permissions.py` (RPG-INFRA-155/156/157).

| Phase | Read domains | Write domains | Emit domains |
|---|---|---|---|
| INIT | policy, platform, infra | policy, infra | — |
| SCHEDULING | entity, policy | schedule | — |
| COLLECTION | entity, schedule | proposals | — |
| RESOLUTION | proposals, policy, entity | entity, world, policy, infra | events, replay |
| CLEANUP | platform, infra | infra | — |
| ADVANCEMENT | entity, lifecycle | lifecycle | events |
| PERSISTENCE _(non-authoritative)_ | entity, world, events | replay | replay, events |

**Key invariant:** RESOLUTION is the sole phase that declares `entity` and `world` write access. All other phases are structurally prohibited from directly writing authoritative entity/world state.

**RNG consumption matches this table:** `docs/engine/contracts/simulation_kernel_contract.md` §7.1 traces the actual `DeterministicRNG` consumers (`EntityGenerator`, `QuestGenerator`, `GuildAction`) and confirms all of them run inside `Kernel._phase_resolution()`, never `_phase_collection()` — consistent with COLLECTION's `proposals`-only write domain above. The Collection-phase worker path itself consumes no RNG.
