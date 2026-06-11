---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260406-RPG-CORE-STABILIZE
phase: done
date: 2026-04-06
tags: [rpg, core, stabilize]
---

# TCK-20260406-RPG-CORE-STABILIZE: RPG Core Stabilization & Introspection

## Description
Resolve "split-brain" mutations (AOA Pillar 1 violation), standardize Kafka persistence on the `ActionBatch` schema, and normalized combat result metadata into typed fields. Finalize engine phase contract enforcement via automated tests.

## Scope
- Refactor `KillRewardService` for authoritative world-state updates (`WorldUpdate`).
- Normalize `trauma` and `threat` into typed `CombatTraceRecord` fields.
- Standardize `PersistencePhase` on the `ActionBatch` schema.
- Remove redundant AI-state synchronization in `FinalizationPhase`.
- Add test coverage for `BuildingTarget` and Phase contract enforcement.

## Final Summary
Achieved 100% architectural parity with the Aspect-Oriented Architecture (AOA) by transforming the simulation engine into a strictly authoritative, deterministic system.

## Verification
- **Unit Tests**: 518/518 passed (including strict PhaseGuard proof).
- **E2E Tests**: 40/40 passed (Regression, Replay, Production Stack).
- **Authoritative rewards**: 0 direct mutations found in combat services.
- **Typed metadata**: trauma, threat, and grudge are now first-class fields.

## Status
DONE

**Tier:** standard
**Type:** chore
**Priority:** P1
