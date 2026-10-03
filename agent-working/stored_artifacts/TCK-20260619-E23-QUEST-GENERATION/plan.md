---
ticket_id: TCK-20260619-E23-QUEST-GENERATION
phase: plan
date: 2026-06-20
---

# Plan: Pressure-Driven Quest Generation — Epic Scope

## Child Ticket Sequence

```
E23A (QuestOpportunity model + generator) ──► E23B (lifecycle + quest_registry)
                                                        │
                                               E23C (reward application) ──► E23D (HERO matching)
```

E23A must complete first (typed model required by all others).
E23B after E23A (lifecycle needs typed model).
E23C can start after E23B (reward applies on lifecycle COMPLETED transition).
E23D can start after E23B (HERO matching reads from quest_registry).

## Child Ticket Summary

| Ticket | Scope | Deliverable |
|---|---|---|
| E23A-QUEST-OPPORTUNITY | `QuestOpportunity` dataclass + `QuestOpportunityGenerator` triggered by depletion/threat/need signals | New model + generator in `src/domains/world_emergence/` |
| E23B-QUEST-LIFECYCLE | OFFERED→ACTIVE→PROGRESSED→COMPLETED/FAILED/EXPIRED state machine + `quest_registry` in `AuthoritativeState` | `src/core/state.py` + new lifecycle service |
| E23C-QUEST-REWARDS | Quest completion applies gold + XP + faction rep via authoritative mutation pipeline | Apply path in authoritative_pipeline |
| E23D-HERO-MATCHING | HERO entities score quest opportunities above generic harvesting in `AdventureRouteScorer` | `src/domains/adventure/scoring.py` |

## Acceptance Path

1. E23A: inject `RESOURCE_DEPLETED` event; assert `QuestOpportunityGenerator` produces `resource_crisis` QuestOpportunity
2. E23B: `quest_registry` exists in `AuthoritativeState`; lifecycle transitions compile correctly
3. E23C: 1000-tick run → ≥1 quest COMPLETED with gold+XP reward in entity state
4. E23D: 400-tick run → HERO entity starts `resource_crisis` quest (scores it above GATHER_RESOURCE)

## Key Design Decisions

- `QuestOpportunity` is a typed frozen dataclass (NOT a string); stored in `quest_registry: Dict[str, QuestOpportunity]` in `AuthoritativeState`
- `diplomatic_errand` trigger family is a stub (generates opportunity but reward=None until Phase 5)
- `DynamicQuestSeedService` remains intact — E23A wraps its output into `QuestOpportunity` objects
- Quest lifecycle transitions are authoritative (go through apply path, not local mutation)
