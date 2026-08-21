---
status: active
layer: engine
authority: P1
audience: developer
---

# Project Architecture: The Resource-Safe Conductor

This document provides a deep technical overview of the **Resource-Safe Simulation Engine** at the heart of the RPG simulation. It defines the authoritative execution laws, deterministic guarantees, and resource-safety boundaries.

---

## 1. High-Level Architecture

The engine is built on a **Deterministic Orchestrated Loop** where the `Kernel` acts as the authoritative conductor, coordinating decoupled systems and maintaining a single source of truth.

### System Context Diagram

```mermaid
graph TD
    Client["Browser (React + Canvas)"] -- REST/Polling --> API["FastAPI (Web Thread)"]
    API -- "ReadOnly Snapshots" --> Client
    
    API -- Controls --> Kernel["Simulation Kernel (Simulation Thread)"]
    Kernel -- StateUpdate --> ApplyPath["ApplyPath (Authoritative)"]
    ApplyPath -- AuthoritativeState --> Kernel
    
    Kernel -- TraceEvents --> Replay["ReplayManager (Streaming Persistence)"]
    Kernel -- WorkPackets --> WorkerPool["WorkerPool (Concurrent AI)"]
    WorkerPool -- "ActionResults" --> Kernel
```

### The Threaded Concurrency Model

The engine isolates **Authoritative Mutation** from **Concurrent Deliberation** to ensure 100% determinism and resource safety:

1.  **Simulation Thread (`Kernel`)**: The **Single-Writer**. Only this thread is allowed to produce and apply `AuthoritativeState` transitions.
2.  **Web Thread (FastAPI)**: Serves the REST API. It reads immutable `AuthoritativeState` references. 
3.  **Worker Pool (AI)**: AI brain computations are fanned out to background threads. They receive **Compact Worker Packets** (shallow-cloned subset of state) and return **ActionResults**. They never modify the world state directly.
4.  **Generation-Based Apply**: Instead of deep-cloning every tick, the engine uses the `ApplyPath` to create the next "Generation" of the world. This preserves shared references for read-only visibility while ensuring that even a single illegal mutation of a shared reference is caught by runtime checks or caught by the law of separation.

---

## 2. The 7-Phase Deterministic Kernel Loop

Every tick executes exactly seven phases in a strict, contract-enforced sequence. This "Law of Ticks" is fixed and immutable.

### Phase Sequence & Contracts

| Phase | Responsibility | Permissions (READ / MUTATE) |
| :--- | :--- | :--- |
| **1. INIT** | Increments simulation clock and resets per-tick buffers. | `state.world_time` / `state.world_time` |
| **2. SCHEDULING** | Identifies entities due to act and selects work based on the **Work Debt** budget. | `state.entities`, `policy` / `tick_work` |
| **3. COLLECTION** | Offloads AI deliberation tasks to the `WorkerManager` (bounded concurrent pool) using compact packets. | `entity, schedule` / `proposals` |
| **4. RESOLUTION** | **Authoritative Update**. Converts results into `StateUpdate` and applies it via `ApplyPath`, incrementing the state generation. | `worker_results` / `state.authoritative` |
| **5. CLEANUP** | Internal metrics and state finalization. | `platform, infra` / `infra` |
| **6. ADVANCEMENT** | Signal recording and tick seal (`RuntimeStatus`). | `entity, lifecycle` / `lifecycle, events` |
| **7. PERSISTENCE** | **External Phase, non-authoritative**. Streams `TraceEvent` records to the `ReplayManager`. | `state.hash`, `policy` / `disk/stream` (I/O only) |

### Phase Governance
Runtime integrity is enforced by the **PhaseContract**. Any attempt to access state outside the assigned phase boundary or perform unmanaged mutations results in an immediate simulation halt. This prevents "Semantic Drift" where systems accidentally depend on the side effects of others.

---

## 3. Resource-Safe Execution Laws

The engine is governed by three primary laws to ensure it survives pathological conditions:

1.  **Law of Bounded State**: No authoritative collection may grow without limit. Every entity, event buffer, and replay stream must have an explicit retention policy.
2.  **Law of Non-Blocking Persistence**: Replay and observability are "Non-Authoritative." Failures in tracing or persistence must never stall the kernel.
3.  **Law of Progressive Degradation**: The engine must shed optional load (traces, then diagnostics, then AI fidelity) before it crashes due to resource exhaustion.

---

## 4. Determinism & Deterministic RNG

The kernel uses the **Seed-Domain-Identity** formula to ensure perfect replayability across all certified hardware.

### The RNG Formula
The `DeterministicRNG` (using `xxhash`) generates sequences based on:
1.  **World Seed**: Global simulation seed.
2.  **Domain**: Identifies the simulation subsystem (e.g., `Domain.COMBAT`).
3.  **Entity ID**: Ensures different entities don't "sync" their random rolls.
4.  **Tick**: Ensures rolls change every frame.

---

## 5. Performance Monitoring (Standard Hardware Classes)

Throughput claims are never made in isolation. The engine certifies its performance against **Hardware Classes**:
- **Class A (Low-Power)**: Bounded to strictly degraded profiles (10 TPS).
- **Class B (Consumer)**: Standard profile (20 TPS).
- **Class C (High-Performance)**: Enhanced observability profiles.

> **Known conflict, not resolved here**: This table's Class A/B/C mapping is inverted relative to
> `docs/engine/contracts/certification_contract.md` §3 and `docs/performance/perf_baseline_policy.md`
> §2.2, both of which make Class A the *most* powerful tier (≥16 cores/≥32GB or "High-Performance
> Server"). This table makes Class A the *least* powerful ("Low-Power," 10 TPS) and Class C the
> most powerful — an opposite-direction conflict, not just a threshold disagreement. Newly found by
> TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT; see also the pre-existing, differently-shaped conflict
> already flagged at `docs/performance/perf_baseline_policy.md`'s own callout box
> (TCK-20260702-OBSISO-ISOLATION-PROOF). Not fixed here — pending owner decision on which mapping
> is canonical.

---

## 6. Domain-Driven System Organization

The `src/systems/` directory is organized into domain-specific packages to improve maintainability and prevent circular dependencies.

- **Strategic Systems** (`src/systems/strategic_systems/`): High-level intention and redirection logic.
- **Social Systems** (`src/systems/social_systems/`): Relationship management and collective behavior.
- **World Systems** (`src/systems/world_systems/`): Environmental processes, quests, and spatial navigation.
- **Economy Systems** (`src/systems/economy_systems/`): Resource flow, markets, and production.
- **Lifecycle Systems** (`src/systems/lifecycle_systems/`): Biological pressures and entity evolution.

Compatibility is maintained via wrappers in `src/systems/*.py`, which re-export the modular implementations.

## 7. Decoupled Core Models

To further harden the engine against "Graph Hub" fragility, core state and update models are being extracted from `state.py` and `updates.py` into specialized packages:

- **State Models** (`src/core/models/`): Standalone components like `ItemStack`, `SocialBond`, and `QuestState`.
- **Update Models** (`src/core/update_models/`): Standalone intents like `InventoryUpdate` and `ResourceTransferIntent`.

This separation allows systems to depend on specific model definitions without importing the entire world state, reducing the impact of architectural changes.

> [!NOTE]
> All architectural claims in this document are pinned by the `tests/docs/` integrity suite.
