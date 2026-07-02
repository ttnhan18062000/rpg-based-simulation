---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23D-HERO-MATCHING
phase: done
date: 2026-06-20
tags: [quest-generation, adventure-scoring, hero, cognition, phase-2]
---

# TCK-20260619-E23D-HERO-MATCHING

## Title
Epic 2.3D · HERO Capability Matching for Quest Routes

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
HERO entities don't currently prioritize quest opportunities over generic harvesting in `AdventureRouteScorer`. This ticket adds capability matching so HERO entities score offered quests proportional to their match with the quest's `objective_chain` requirements.

**Requires:** TCK-20260619-E23B-QUEST-LIFECYCLE (quest_registry must exist for routing to read it)

## Scope

### Extend `AdventureRouteScorer` for quest routes

In `src/domains/adventure/scoring.py`: when scoring a `QUEST_OPPORTUNITY` route family:

1. Check if entity is a HERO archetype (check `entity.identity.properties.get("archetype") == "HERO"` or equivalent tag)
2. Look up the `QuestOpportunity` from `state.quest_registry` by route's quest_id
3. Score `capability_match`: compare entity's capability tags against `quest.objective_chain` requirements
   - Full match → `capability_match = 1.0`
   - Partial match → `capability_match = 0.5`
   - No match → `capability_match = 0.0`
4. Apply: `benefit = base_benefit * (1.0 + capability_match)` for HERO entities; non-HERO entities use `benefit = base_benefit * 0.5` (quests are less attractive to non-HERO)

This makes HERO entities prioritize quests they can complete over generic harvesting.

### Add `QUEST_OPPORTUNITY` as a route family

Check if `RouteFamily.QUEST_OPPORTUNITY` (or equivalent) already exists in `src/domains/adventure/`. If not, add it to the enum and register with the scorer.

## Out of Scope
- Multi-entity party quest assignment (Phase 4)
- Faction-filtered quest visibility (Phase 5)

## Acceptance Criteria
- HERO entity with matching capability scores `QUEST_OPPORTUNITY` route higher than `GATHER_RESOURCE` route (when a quest is OFFERED)
- Non-HERO entity scores quest route ≤ equivalent GATHER_RESOURCE route
- `test_hero_entity_scores_quest_above_harvesting` passes
- `test_non_hero_entity_unaffected` passes
- Existing scoring tests in `tests/unit/domains/adventure/test_phase3_route_scoring.py` pass (no regression)

## Related Tickets
- TCK-20260619-E23-QUEST-GENERATION (parent epic)
- TCK-20260619-E23B-QUEST-LIFECYCLE (required — quest_registry must exist)
- TCK-20260619-E21C-SCORING-WIRE (adjacent — depletion scoring; do not conflict)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §6 (scoring formula — add QUEST_OPPORTUNITY route family note under §6.4 personality bias table)
- `docs/parity_ledger/strategic_cognition.yaml` (add STRAT-228 entry for quest route scoring)

## Related Code Areas
- `src/domains/adventure/scoring.py` (AdventureRouteScorer — add QUEST_OPPORTUNITY handling)
- `src/domains/adventure/` (RouteFamily enum — add QUEST_OPPORTUNITY if missing)
- `tests/unit/domains/adventure/test_hero_quest_scoring.py` (new)
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` (regression)

## Assumptions / Open Questions
- Does a `RouteFamily.QUEST_OPPORTUNITY` or `QUEST` value already exist? Check `src/domains/adventure/` before adding.
- How does `AdventureRouteScorer` receive `state`? It must have access to `state.quest_registry` to look up the `QuestOpportunity`. If it currently doesn't receive state, it needs to be passed in (check the method signature).
- What field identifies a HERO entity? `entity.identity.properties.get("archetype")` or a tag? Check entity state before implementing.

## Implementation Notes
- Added `RouteFamily.QUEST_OPPORTUNITY = "quest_opportunity"` to schema.py enum.
- Added `quest_id: Optional[str] = None` field to `AdventureRouteOption` frozen dataclass.
- Extended `AdventureRouteScorer.score()` with `quest_registry: Optional[Dict[str, QuestOpportunity]] = None` parameter (backward-compatible, follows `resource_nodes` pattern from E21C).
- HERO detection uses `entity.identity.role == EntityRole.HERO` (not `properties.get("archetype")` as originally suggested in ticket).
- Capability tags compared from `entity.identity.traits` (Set[str]) against `quest.objective_chain` verb prefixes.
- Benefit multiplier: HERO full-match ×2.0, partial ×1.5, none ×1.0; non-HERO ×0.5.
- Added `QUEST_OPPORTUNITY: ["gold"]` to family_needs for urgency mapping.
- Added `greed × 0.25` personality bias for QUEST_OPPORTUNITY family.
- Updated docs/mechanics/04_strategic_cognition.md §6.4 and added §6.7.
- STRAT-228 parity entry added to docs/parity_ledger/strategic_cognition.yaml.

## Test Summary
```bash
pytest tests/unit/domains/adventure/test_hero_quest_scoring.py -x -v
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -x -v  # regression
```
Integration:
```bash
pytest tests/integration/scenarios/test_pressure_quest.py -x -v -m slow
```

## Files Changed
- `src/domains/adventure/schema.py` — Added `RouteFamily.QUEST_OPPORTUNITY`; added `quest_id: Optional[str]` field to `AdventureRouteOption`
- `src/domains/adventure/scoring.py` — Extended `AdventureRouteScorer.score()` with `quest_registry` param and QUEST_OPPORTUNITY capability-match branch
- `src/domains/adventure/mapper.py` — Added `QUEST_OPPORTUNITY → (ProjectKind.QUEST, ObjectiveKind.ACCEPT_QUEST)` mapping
- `tests/unit/domains/adventure/test_hero_quest_scoring.py` — New: 8 tests for HERO capability matching
- `tests/unit/domains/adventure/test_phase3_route_families.py` — Updated count assertion 13→14
- `docs/mechanics/04_strategic_cognition.md` — Added QUEST_OPPORTUNITY to §6.4 table; added §6.7 capability-match spec
- `docs/parity_ledger/strategic_cognition.yaml` — Added STRAT-228 entry

## Completion Summary
Implemented HERO capability matching for QUEST_OPPORTUNITY routes in `AdventureRouteScorer`. Added `RouteFamily.QUEST_OPPORTUNITY` enum member and `quest_id` field to `AdventureRouteOption`. Extended scorer with backward-compatible `quest_registry` dict parameter (same pattern as E21C's `resource_nodes`). HERO entities score quests with benefit multiplier 1.0–2.0 based on trait/objective_chain verb alignment; non-HERO entities receive 0.5× benefit. Greedy personality bias applies to all. 8 new tests pass; 40 adventure domain tests total pass (no regression). Mechanics Bible §6.4 and §6.7 updated; STRAT-228 parity entry added.
