---
status: active
layer: engine
authority: P1
audience: developer
---

# Simulation Engine & Orchestration

This directory documents the engine's deterministic heart and the pipeline that governs state transitions.

## Core Loop
- [Simulation Kernel](../engine/kernel.md): The 7-phase orchestrator (Init, Scheduling, Collection, Resolution, Cleanup, Advancement, Persistence).
- [Authoritative Pipeline](../engine/authoritative_pipeline.md): The refinement-phase sequence for world mutation (counted unit and generated list defined there).

## Architectural Standards
- [High-Level Architecture](../engine/architecture.md): System context and threading model.
- [Implementation Conventions](../engine/architecture_reference.md): Coding standards and architectural spines.
- [Project Lawbook](../engine/project_lawbook.md): The master index of technical contracts.

## Verification & Performance
- [Performance Contract](../engine/performance_contract.md): Hardware classes and scaling limits.
- [Divergence Log](../engine/divergence_log.md): Record of intentional parity shifts.
- [Known Limitations](../engine/known_limitations.md): Current scope boundaries.
