---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260410-BUILDING-UNIFICATION
phase: done
date: 2026-04-10
tags: [building, unification]
---

# TCK-20260410-BUILDING-UNIFICATION: Strategic Knowledge Unification (Phase 2)

**Request Summary**: Execute [Improvement Phase 2] from `thinking_implementation_improvement.md`. Standardize all building handlers to use typed strategic ingestion and harden centralized detour suggestion logic.

**Scope**:
- [MODIFY] `src/ai/states/town.py`: Refactor all building handlers to remove hybrid updates and legacy string goals.
- [MODIFY] `src/ai/strategy/detour_suggestion.py`: Implement Lead Matching for material blockers and unify objective derivation.
- [MODIFY] `src/core/logic/strategic_knowledge_ingestion.py`: Standardize ingestion contracts and provenance.
- [REMOVE]: Legacy `goals_add` patterns from building interactions.

**Out of Scope**:
- Implementing new building types or interaction verbs.
- Changing the underlying Utility AI scorer logic (except where it reads goals).

**Acceptance Criteria**:
- Building handlers strictly emit `StrategicUpdate` (blockers/leads) and `PerceptionUpdate` (maps), but zero `MindUpdate(goals_add)`.
- The `ActionProposal.reason` field is used only for logging, not for durable AI state variables.
- Entities correctly derive detour objectives from material blockers by matching them with available leads.
- All new logic is verified with integration tests in `tests/test_building_unification.py`.

**Related Tickets**:
- TCK-20260410-STRAT-REFACTOR (Phase 1)
- TCK-20260410-STRAT-GOVERNANCE (Phase 2 Pre-req)

**Current Status**: DONE

**Tier:** standard
**Type:** chore
**Priority:** P1
