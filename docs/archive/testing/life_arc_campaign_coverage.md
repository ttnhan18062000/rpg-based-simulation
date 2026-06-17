---
status: historical
layer: testing
authority: P2
audience: developer
---

# Phase 9 — Long-Run Life-Arc Scenario Campaigns Coverage Audit

This audit documents the coverage boundaries between existing long-run/arena stress tests and Phase 9 semantic campaigns.

## 1. Existing Long-Run and Stress Tests

The repository already defines tests for pure performance, memory safety, and combat correctness:
- **Long-Run pure stability**: Verifies memory usage and tick bounds over thousands of ticks.
- **Arena 50v50 stress tests**: Validates large scale combat simulation, checking for CPU bottlenecks or out-of-memory errors under intense actions.
- **Determinism parity**: Ensures simulation state transitions are fully deterministic under a fixed seed.
- **Observability / API / WebSocket**: Asserts live status reporting, telemetry channels, and websocket endpoints are responsive.

These are out-of-scope for Phase 9 and will not be duplicated.

## 2. Phase 9 Semantic Test Scope

Phase 9 focuses exclusively on **semantic life continuity**, validating that:
- Entities form cohesive, traceable, and explainable life arcs over long run scenarios.
- Experience changes future behaviors (e.g., memory, upgrades, and social interactions change subsequent action selections).
- Route decisions diverge naturally based on traits, class, and resource availability (diversity vs. collapse).
- Entities respect basic rules (no post-death activities, no omniscient knowledge, bounded retry loops).
- Scoring assesses the semantic richness of the simulation.

## 3. Scope Separation Matrix

| Test Suite / Area | Existing Stress / Arena Coverage | Phase 9 Semantic Campaign Coverage |
| :--- | :--- | :--- |
| **Long-Run Execution** | Memory bounds (RSS), average tick latency, engine stability, no crash | Validates if trace forms an arc like `cautious_growth`, `failed_adventurer` |
| **Arena & Combat** | 50v50 massive battles, combat damage math, execution timing | Asserts combat experience (losses) alters future engagements (avoidance or partying) |
| **World Scarcity & Dynamics** | Material generation, spatial registry, resource distribution | Checks if depletion of resources causes entities to dynamically change routes |
| **Social / Cooperation** | Party formations, quest completion sharing | Verifies entity trust updates and bad partners are rejected on future adventures |
