---
status: active
layer: engine
authority: P1
audience: developer
---

# Project Lawbook: Resource-Safe Simulation Engine

## Purpose
The Project Lawbook is the canonical authority on the simulation engine's architectural invariants, resource laws, and maintenance requirements. It serves as the top-level index for all technical contracts.

## Architectural Pillars

### 1. The Authoritative Heart
- **Law**: Only state required for deterministic outcomes belongs in `AuthoritativeState`.
- **Enforcement**: Any mutation of authoritative state MUST flow through the `apply` path.
- **Isolation**: Non-authoritative systems (Replay, Telemetry) must never influence simulation logic.

### 2. Resource Envelopes
- **Law**: No engine operation may be unbounded.
- **Enforcement**: All buffers, collectors, and queues must have explicit retention policies and memory ceilings.
- **Classification**: All performance claims are bound to specific `HardwareClass` (A/B/C) labels.

### 3. Graceful Degradation
- **Law**: The system must degrade before it fails.
- **Enforcement**: The `ResourceGovernor` triggers mode transitions (`NORMAL` -> `CONSTRAINED` -> `DEGRADED` -> `SURVIVAL`) based on pressure signals.
- **Shedding**: Work must be shed in a defined order (Telemetry -> Sampling -> Fidelity -> Stall).

### 4. Deterministic Proof
- **Law**: Simulation must be bit-identical across different execution contexts (Concurrent vs Sequential).
- **Enforcement**: Mandatory `CertificationHarness` runs verify final hash equivalence vs a sequential baseline.

## Table of Contents

### Technical Contracts (Substrate)
- [Simulation Kernel (Substrate)](../engine/simulation_kernel_contract.md): Tick semantics and phase ordering.
- [Runtime Profiles (Substrate)](../engine/runtime_profiles.md): Envelope schema and hardware levels.
- [Runtime State (Substrate)](../engine/runtime_state_contract.md): Authoritative vs Non-authoritative partitioning.
- [Scheduler & Work Model (Substrate)](../engine/scheduler_contract.md): Eligibility and prioritization.
- [Resource Governor (Substrate)](../engine/resource_governor_contract.md): Degradation and shedding laws.
- [Replay & Retention (Substrate)](../engine/replay_contract.md): Bounded persistence and rollback semantics.
- [Observability & Controls (Substrate)](../engine/observability_contract.md): Operational budgets and terminal commands.
- [Worker & Parallelism (Substrate)](../engine/worker_contract.md): Concurrency bounds and deterministic fallback.
- [Certification & Resilience (Substrate)](../engine/certification_contract.md): Hardware labeling and honest-language reporting.

### Technical Contracts (Gameplay Attachment)
- [Substrate Freeze](contracts/substrate_baseline_contract.md): Deterministic single-process baseline laws.
- [Movement Slice](../archive/engine_contracts/attach_gate1_movement_scope.md): First deterministic gameplay slice (archived).
- [Optimization](../engine/performance_contract.md): Benchmark-driven performance.
- [Scheduler & Work Model](../engine/scheduler_contract.md): Resource-node interaction and scheduling laws.
- [Gameplay Surface](../engine/supported_gameplay_surface.md): Integrated certification.

### Maintenance & Contribution
- [Engineering Playbook](../engine/engineering_playbook.md): Extension templates and TDD workflow.
- [Root Contributing Guide](../../CONTRIBUTING.md): Top-level safety guardrails.
- [Divergence Log](../guidelines/intentional_divergences.md): Canonical record of intentional parity shifts.

## Release-Readiness
This engine is certified for production deployment under the following conditions:
1. **Conformance**: 100% pass rate in the Certification Harness for `CLASS_B` hardware.
2. **Integrity**: Zero documentation drift detected by automated CI checks.
3. **Safety**: All new contributions verified by the `test_contributor_guardrails.py` suite.
