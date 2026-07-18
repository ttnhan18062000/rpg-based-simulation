---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260330-CORE-STABILIZATION
phase: done
date: 2026-03-30
tags: [core, stabilization]
---

# TCK-20260330-CORE-STABILIZATION: AOA Hardening & Simulation Purity

## Description
Comprehensive refactor of the simulation's Core Architecture to reclaim the Aspect-Oriented Architecture (AOA) and eliminate "God-Object" patterns, "Boundary Leaks," and "Structural Dishonesty". This task implements the "Burn and Rebuild" approach to strictly enforcetyped compositional boundaries.

## Scope
- Refactor `Entity` to use explicit typed aspect fields instead of a dynamic dictionary.
- Purge ~50 legacy property shims from the core `Entity` model.
- Decompose `MindAspect` into five specialized sub-models (`DecisionState`, `PerceptionMemory`, etc.).
- Enforce strict read-only constraints on AI decision-making phases.
- Decompose the `CombatAction.apply` god-method into discrete services.
- Define explicit orchestrator phases in the `WorldLoop`.

## Acceptance Criteria
- [x] `Entity.aspects` dictionary is removed and replaced by typed fields.
- [x] No property shims (`entity.hp`, `entity.pos`) remain in `src/core/entities/entity.py`.
- [x] `AIBrain.decide()` does not mutate any input snapshots or entity objects.
- [x] `CombatAction.apply` is reduced to an orchestrator calling specialized services.
- [x] All 748 tests pass after the refactor is completed.
- [x] Performance benchmarks for serialization show no regression.

## Related Tickets
- N/A

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1
