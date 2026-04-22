# Phase Dependency & Blocker Map

This document tracks the dependencies between engine phases and identifies specific blockers for downstream semantics.

## Phase 8 -> Phase 9 Blockers

| Downstream Row | Phase 9 Requirement | Phase 8 Blocker | Reason |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-150** | Belief cycle (Rumors) | **LEG-RPG-098** (Hostility) | Strategic belief requires stable local hostility/engagement triggers. |
| **LEG-RPG-119** | Betrayal (Avenge) | **LEG-RPG-102** (Tactical Bias) | Betrayal logic assumes archetype-consistent tactical responses. |
| **LEG-RPG-141** | Dynamic Quests | **LEG-RPG-117** (Scar Detection) | Quest generation depends on environment/scar awareness. |

## Substrate Dependencies

| Phase 8 Row | Substrate Dependency | Status |
| :--- | :--- | :--- |
| All Tactical AI | **Phase 7 Substrate Closure** | **CLOSED** |
| All World Interaction | **Phase 7 Deterministic RNG** | **CLOSED** |

## Strategic Assumptions
Phase 9 strategic intelligence is currently blocked on:
- Stable local target stickiness (Phase 8).
- Explicit combat legality rules (Phase 8).
- Proven local threat-response heuristics (Phase 8).
