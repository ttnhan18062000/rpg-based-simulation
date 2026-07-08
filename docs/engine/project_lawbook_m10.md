---
status: active
layer: engine
authority: P1
audience: developer
---

# Project Lawbook — Milestone 10

## Purpose

Authoritative laws governing the V2 simulation engine at Milestone 10. All subsystems,
pipelines, and contributors must conform to these laws. See `project_lawbook.md` for
the full law text and parity proofs.

## Architectural Pillars

1. **Determinism**: Identical seed + initial state must always produce identical output.
2. **Authoritative Apply**: All durable mutations flow through a single apply path.
3. **Bounded Resources**: Every subsystem declares and enforces a resource ceiling.
4. **Hardware-Class Honesty**: All claims bind to a specific hardware class (`class_b` baseline).
5. **Observability Separation**: Runtime telemetry is non-authoritative and must not affect state.

## Table of Contents

- Architecture overview: `docs/engine/architecture.md`
- Kernel contract: `docs/engine/kernel.md`
- Authoritative pipeline: `docs/engine/authoritative_pipeline.md`
- Governance: `docs/engine/governance_logic.md`
- Performance contract: `docs/engine/performance_contract.md`
- Known limitations: `docs/engine/known_limitations.md`

## Release-Readiness

The declared release target for Milestone 10 is hardware class `class_b`. Class `class_a`
is unrestricted. Class `class_c` requires SURVIVAL-mode degradation proof. The `class_b`
certification scenario suite is the primary compliance surface.
