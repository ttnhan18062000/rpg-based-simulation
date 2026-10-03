---
ticket_id: TCK-20260619-E23D-HERO-MATCHING
phase: test-plan
date: 2026-06-20
---

# Test Plan — TCK-20260619-E23D-HERO-MATCHING

---

## Regression Surface (existing tests that must pass)

- `tests/unit/domains/adventure/test_phase3_route_scoring.py` — all existing scoring tests
- `tests/unit/domains/adventure/test_phase3_route_families.py` — route family enum tests
- `tests/unit/domains/adventure/test_depletion_scoring.py` — GATHER_RESOURCE depletion scoring (E21C)
- `tests/unit/domains/adventure/test_phase3_route_generator.py` — route generation tests
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py` — decision service

---

## New Tests Required (per AC)

### File: `tests/unit/domains/adventure/test_hero_quest_scoring.py`

#### Test 1: `test_hero_entity_scores_quest_above_harvesting`
- Build a HERO entity (`identity.role = EntityRole.HERO`) with traits matching quest objective chain
- Create a `QUEST_OPPORTUNITY` route with `quest_id="q1"`, `expected_benefit=0.5`
- Create a `GATHER_RESOURCE` route with same `expected_benefit=0.5`
- Pass `quest_registry={"q1": QuestOpportunity(objective_chain=("combat:threat:1",), ...)}`
- Assert: `QUEST_OPPORTUNITY` score > `GATHER_RESOURCE` score
- Verifies AC1

#### Test 2: `test_non_hero_entity_unaffected`
- Build a non-HERO entity (`identity.role = EntityRole.SHOPKEEPER`)
- Same routes and quest_registry as Test 1
- Assert: `QUEST_OPPORTUNITY` score <= `GATHER_RESOURCE` score
- Verifies AC2

#### Test 3: `test_hero_full_match_scores_higher_than_partial`
- HERO entity with `traits={"combat"}` vs `traits={"social"}`
- Quest with `objective_chain=("combat:threat:1",)`
- Full-match entity (combat trait) scores higher than partial/no-match entity
- Verifies capability_match=1.0 > capability_match=0.0

#### Test 4: `test_hero_partial_match_intermediate_score`
- HERO entity with 1 of 2 required objective tokens matched
- Assert: score between full-match and no-match scores
- Verifies capability_match=0.5 path

#### Test 5: `test_quest_opportunity_no_registry_entry_uses_no_match`
- HERO entity, QUEST_OPPORTUNITY route with `quest_id` not in registry
- Assert: scores with `capability_match=0.0` (graceful fallback)

#### Test 6: `test_quest_opportunity_none_quest_id_uses_no_match`
- HERO entity, QUEST_OPPORTUNITY route with `quest_id=None`
- Assert: does not crash; scores with `capability_match=0.0`

#### Test 7: `test_non_hero_quest_opportunity_below_gather`
- Non-HERO entity, QUEST_OPPORTUNITY route same expected_benefit as GATHER_RESOURCE
- Assert: quest score is 50% of benefit relative to gather (benefit * 0.5 multiplier)

---

## Scoped Pytest Commands

```bash
# Primary new tests
pytest tests/unit/domains/adventure/test_hero_quest_scoring.py -x -v

# Regression: existing scoring tests
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -x -v

# Regression: all adventure domain tests
pytest tests/unit/domains/adventure/ -x -v
```

---

## Anti-Drift Test Guards

- Every test must import `EntityRole` from `src.core.enums` and use `role=EntityRole.HERO` — never use `properties.get("archetype")`.
- Tests must not import `AuthoritativeState` — pass `quest_registry` as a plain dict.
- Tests for non-HERO must use a non-zero role value (e.g. `EntityRole.SHOPKEEPER`).
- `AdventureRouteOption` construction must use `quest_id` field only for QUEST_OPPORTUNITY family tests.
