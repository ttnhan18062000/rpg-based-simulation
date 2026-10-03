---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-DIRTY-DEPENDENCY-GRAPH
artifact_type: investigation
tags: [dirty, dependency, graph]
---

# Architectural Investigation: Dirty Dependency Graph

## Current State Analysis

Currently, `DirtySet` in `src/core/dirty.py` tracks direct domain modifications (`movement_entities`, `combat_entities`, `inventory_entities`, etc.). Systems and phases query `CandidateSelector` which maps phase domains (e.g., `"interactions"`, `"groups"`) to unions of direct dirty set properties (e.g. `movement_entities | strategic_entities`).

However, direct modifications have inherent downstream causal relationships:
- When an entity moves (`movement`), its spatial relationship with other entities changes. This necessitates re-evaluating strategic proximity, social encounters, and group cohesion.
- When an entity engages in combat (`combat`), its health and stamina are altered. This necessitates checking lifecycle status (near-death/death) and updating social morale or group standing.
- When an entity's inventory changes (`inventory`), its carrying capacity and available items change, affecting strategic decision-making and shop transactions.

## Vulnerability & Enhancement

Without explicit dirty dependency expansion, systems rely on `CandidateSelector` manually unioning direct fields for every possible domain. If a new system is added or an existing system's causal requirements expand, `CandidateSelector` can become convoluted or miss critical dependencies.

By introducing `DirtyDependencyGraph.expand()`, we formalize these relationships directly into the `DirtySet` lifecycle. Whenever a `DirtySet` is constructed or refreshed (via `DirtySetBuilder.build()` or `DirtySet.from_update()`), it will be automatically and deterministically expanded.

## Verification

We will implement `tests/unit/optimization/test_dirty_dependency_graph.py` verifying:
1. `movement` marks `strategic` and `social`.
2. `inventory` marks `strategic`.
3. `combat` marks `lifecycle`, `social`, and `strategic`.
4. `biological`/`attributes` marks `strategic` and `lifecycle`.
5. Idempotency (`expand(expand(d)) == expand(d)`).
6. Determinism (identical output sets across multiple invocations).
