---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260326-NARRATIVE
phase: done
date: 2026-03-26
tags: [narrative]
---

# TCK-20260326-NARRATIVE

## Title
Narrative Memory System — Recording & Recall for Goal Influence

## Priority
P1: High

## Description
Entities record significant events (GLORY, TRAUMA) into `memory_log` via `action_system.py`, but this data is never used to influence AI decisions. This ticket completes the Narrative Memory system by:
1. Recording additional memory types (SURVIVAL, DISCOVERY).
2. Adding a `MemoryModifier` that biases goal scores based on accumulated memories.
3. Implementing memory decay to prevent unbounded growth.

## Scope
- **New Memory Types**: SURVIVAL (survived at <20% HP), DISCOVERY (entered new region).
- **MemoryModifier**: Biases goal scores — high GLORY → more combat, high TRAUMA → more flee/rest.
- **Memory Decay**: Prune old memories beyond 50 entries per entity (keep highest-impact).
- **Memory Query API**: `MindAspect.total_glory()`, `total_trauma()` helpers.

## Acceptance Criteria
- [x] SURVIVAL events recorded when entity survives combat at <20% HP.
- [x] DISCOVERY events recorded when entity first enters a new region.
- [x] `MemoryModifier` multiplies combat score by `1 + glory/100` and flee score by `1 + |trauma|/100`.
- [x] Memory is capped at 50 entries per entity (oldest low-impact pruned).
- [x] `total_glory()` and `total_trauma()` return correct sums.
- [x] No test regressions (683 tests passing).

## Status: DONE
- **Implementation**: Completed with 14 target unit tests and full suite verification.
- **Verification**: 683/683 tests PASS.
- **Artifacts**: Stored in `stored_artifacts/TCK-20260326-NARRATIVE/`.

## Related Tickets
- TCK-20260322-RPG_REFINEMENT (Parent)
- TCK-20260326-HYSTERESIS (Sibling — completed)

**Tier:** standard
**Type:** chore
**Priority:** P1
