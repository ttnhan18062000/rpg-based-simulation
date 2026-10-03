---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260518-PHASE-DEPENDENCY-GRAPH
artifact_type: investigation
tags: [phase, dependency, graph]
---

# Phase Dependency Graph Investigation Notes

## Pipeline Architecture Analysis
The `AuthoritativeApplyPipeline.refine` method orchestrates 17 distinct simulation phases across 7 macro blocks. Previously, all 17 phases executed unconditionally on every tick, performing redundant object scans and set evaluations even during completely quiet simulation ticks where no entities moved or interacted.

## Domain Mapping
By leveraging the existing `DirtySet` and `CandidateSelector` architectures from Milestones 12 and 14, each phase can be rigorously mapped to its required dirty input domains:
- **Contracts**: `social`, `lifecycle`
- **Blacksmith**: `inventory`, `movement`, `town`
- **Action & Movement Routing**: `strategic`, `movement`
- **Building Sabotage**: `combat`, `town`, `buildings`
- **Evolution**: `biological`, `combat`, `attributes`
- **Groups**: `social`, `movement`, `combat`, `groups`

## Outcome
By wrapping each phase with `PhaseDependencyGraph.should_run_phase`, the engine short-circuits execution when `update.dirty_set` contains no dirty entities in the required input domains. Unconditional phases (Compactor, Trust Boundary, Lifecycle, Capacity Enforcement) remain locked to execute every tick.
