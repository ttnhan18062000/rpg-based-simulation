---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 9 Entry Package

This package formalizes the readiness gate for Phase 9: Strategic & Social Cognition.

## 1. Gate Prerequisites

| Requirement | Status | Evidence |
| :--- | :--- | :--- |
| Phase 8 Exit Package ratified | **PASSED** | `docs/engine/history/combat_tactical_exit_package.md` |
| Phase 9 row set frozen | **PASSED** | `docs/engine/history/strategy_social_backlog.md` (10 rows) |
| Closure conditions defined | **PASSED** | `docs/engine/history/strategy_social_closure_conditions.md` |
| Support boundary restated | **PASSED** | `docs/engine/history/strategy_social_entry_support_boundary.md` |
| All existing tests passing | **PASSED** | Full `tests/` regression suite |

## 2. Phase 9 Scope

Phase 9 recovers:
- **Strategic Cognition**: Directives, projects, objectives, concerns, interruption resistance, lead bandwidth, detour suggestion, event interpretation, cognition graph export.
- **Social Narrative**: Betrayal consequences, social learning, social contracts, recruitment depth, source trust recalibration.
- **Belief & Knowledge**: Belief cycle (rumors/decay), narrative memory (turning points), knowledge uncertainty.
- **Bounded Progression** (conditional): Dynamic quests, innate talents, skill scaling.

## 3. Phase 9 Assumptions

1. Local combat resolution is handled by `CombatResolutionSystem` (Phase 8 truth).
2. Tactical pathfinding and local positioning are handled by `TacticalDecisionSystem` (Phase 8 truth).
3. Environmental legality (movement/LoS) is managed by `LegalityServiceV2` (Phase 8 truth).
4. Substrate determinism is guaranteed by the Phase 7 kernel loop.

## 4. Phase 9 Constraints

- Phase 9 must NOT reopen Phase 7/8 substrate or combat contracts.
- Phase 9 must NOT absorb Phase 10 compatibility or advanced progression work.
- All new systems must follow the 6-phase kernel loop and emit typed updates.

---
*Phase 9 is officially **OPEN** as of 2026-04-22.*
