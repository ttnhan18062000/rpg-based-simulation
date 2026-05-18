# Project Lawbook: Resource-Safe Simulation Engine

## Purpose
The Project Lawbook is the canonical authority on the simulation engine's architectural invariants, resource laws, and maintenance requirements. It serves as the top-level index for all technical contracts established during Milestones 1-10.

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
- [Simulation Kernel (Substrate)](../engine/simulation_kernel_contract_m1.md): Tick semantics and phase ordering.
- [Runtime Profiles (Substrate)](../engine/runtime_profiles_m1.md): Envelope schema and hardware levels.
- [Runtime State (Substrate)](../engine/runtime_state_contract_m3.md): Authoritative vs Non-authoritative partitioning.
- [Scheduler & Work Model (Substrate)](../engine/scheduler_contract_m4.md): Eligibility and prioritization.
- [Resource Governor (Substrate)](../engine/resource_governor_contract_m5.md): Degradation and shedding laws.
- [Replay & Retention (Substrate)](../engine/replay_contract_m6.md): Bounded persistence and rollback semantics.
- [Observability & Controls (Substrate)](../engine/observability_contract_m7.md): Operational budgets and terminal commands.
- [Worker & Parallelism (Substrate)](../engine/worker_contract_m8.md): Concurrency bounds and deterministic fallback.
- [Certification & Resilience (Substrate)](../engine/certification_contract_m9.md): Hardware labeling and honest-language reporting.

### Technical Contracts (Phase 4: Gameplay Attachment)
- [M1: Substrate Freeze](../engine/runtime_completion_contract_ma.md): Closing the repaired baseline.
- [M2: Movement Slice](attach_gate1_movement_scope.md): First deterministic gameplay slice.
- [M3: Optimization](../engine/performance_contract.md): Benchmark-driven performance.
- [M4: Resource Slice](../engine/m4_test_matrix.md): Resource-node interaction.
- [M5: Gameplay Surface](../engine/supported_gameplay_surface_m5.md): Integrated certification.

### Maintenance & Contribution
- [Engineering Playbook (M10)](../engine/engineering_playbook_m10.md): Extension templates and TDD workflow.
- [Root Contributing Guide](../../CONTRIBUTING.md): Top-level safety guardrails.
- [Divergence Log](attach_gate1_movement_scope.md): Canonical record of intentional parity shifts.

## Release-Readiness (M10)
This engine is certified for production deployment under the following conditions:
1. **Conformance**: 100% pass rate in the Certification Harness for `CLASS_B` hardware.
2. **Integrity**: Zero documentation drift detected by automated CI checks.
3. **Safety**: All new contributions verified by the `test_contributor_guardrails.py` suite.
