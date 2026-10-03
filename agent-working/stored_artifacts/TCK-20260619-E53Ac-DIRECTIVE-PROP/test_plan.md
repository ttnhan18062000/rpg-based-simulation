# Test Plan — TCK-20260619-E53Ac-DIRECTIVE-PROP

## Test File
`tests/unit/faction/test_faction_directive_propagation.py`

## Required Tests (acceptance criteria)

1. `test_guard_patrol_urgency_boosted_by_faction_directive`
   - Entity: GUARD role
   - Route: HUNT_WEAK_ENEMY, score=0, expected_benefit=0, expected_risk=0
   - faction_directives: [FactionDirective(faction_id="f1", directive_kind=DEFEND_BORDER)]
   - factions: any or None
   - Assert: returned route.score == 2.0 (urgency += 2.0)

2. `test_merchant_trade_urgency_boosted_by_allied_region`
   - Entity: SHOPKEEPER role
   - Route: GATHER_RESOURCE
   - faction_directives: [] (non-None, can be empty)
   - factions: {"f1": FactionState(faction_id="f1", diplomatic_relations={"f2": "allied"})}
   - Assert: returned route.score increases by +1.5

3. `test_hero_quest_urgency_boosted_by_commission`
   - Entity: HERO role
   - Route: QUEST_OPPORTUNITY
   - faction_directives: [FactionDirective(faction_id="f1", directive_kind=COMMISSION_QUEST)]
   - factions: any or None
   - Assert: returned route.score increases by +3.0

4. `test_no_faction_directives_scorer_unchanged`
   - Any entity/route
   - faction_directives=None
   - Assert: score == score from same call without faction params

## Regression Tests

5. `test_guard_no_boost_without_defend_border_directive`
   - GUARD + HUNT_WEAK_ENEMY + faction_directives with TRADE_ROUTE only → no boost

6. `test_shopkeeper_no_boost_without_allied_faction`
   - SHOPKEEPER + GATHER_RESOURCE + factions with "enemy" relations only → no boost

7. `test_hero_no_boost_without_commission_directive`
   - HERO + QUEST_OPPORTUNITY + faction_directives with DEFEND_BORDER only → no boost

8. `test_existing_scoring_regression`
   - Call with no faction params → same result as before (no regression to existing tests)

## Regression Guard
```bash
pytest tests/unit/adventure/test_scoring.py -x -v
```
