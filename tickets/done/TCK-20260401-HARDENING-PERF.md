---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260401-HARDENING-PERF
phase: done
date: 2026-04-01
tags: [hardening, perf]
---

# TCK-20260401-HARDENING-PERF: Infrastructure Safety & Performance Optimization

## Description
This ticket addresses the fifth priority of the `final_implementation_plan.md`. It focuses on infrastructure safety (replacing or hardening pickle) and transport efficiency (payload caching).

## Scope
- **Serialization Safety**: Audit and replace `pickle` with schema-checked JSON/BSON for recovery payloads.
- **Transport Caching**: Precompute tick overview payloads once per tick to serve multiple clients efficiently.
- **Stream Compression**: Optimize the binary WebSocket stream for high-entity-count scenarios.
- **Phase Invariants**: Add runtime assertions for phase-boundary safety.

## Acceptance Criteria
- [x] `pickle` is removed from all high-risk infrastructure channels.
- [x] Tick overview generation takes < 2ms for 50+ entities.
- [x] Payload size remains stable even as simulation complexity grows.

## Related Tickets
- [TCK-20260331-RUNTIME-INTEGRITY](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260331-RUNTIME-INTEGRITY.md)

## Status
DONE

## Final Status
**DONE**: Implemented recursive freeze guards to prevent mutation during serialization and optimized StaticData payload caching. Replaced vulnerable serialization with structured Pydantic models and verified < 2ms overview generation.

**Tier:** standard
**Type:** chore
**Priority:** P1
