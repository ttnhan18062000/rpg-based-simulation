# Test Plan — TCK-20260619-E53Ad-TENSION-UPDATE

## Test File
`tests/unit/faction/test_faction_awareness.py`

## Required Tests (acceptance criteria)

1. `test_faction_tension_increases_on_resource_depletion`
   - FactionState(territory=("region_01",), tension_level=0.0)
   - WorldEvent(category=RESOURCE_DEPLETED, tick=1, region_id="region_01")
   - compute_tension_updates() returns [FactionUpdate(faction_id="hero_guild", tension_delta=0.1)]

2. `test_faction_tension_capped_at_1_0`
   - FactionState(tension_level=0.95) in AuthoritativeState
   - Applying FactionUpdate(tension_delta=0.1) via apply.py → tension_level = 1.0 (not 1.05)

3. `test_resource_depleted_outside_territory_no_update`
   - RESOURCE_DEPLETED event in "region_02", faction territory=("region_01",) → no update

4. `test_no_factions_no_updates`
   - state.factions={} → returns []

## Additional Tests

5. `test_non_resource_depleted_event_ignored`
   - WorldEvent(category=ENTITY_DEATH, region_id="region_01") → no update

6. `test_multiple_events_produce_multiple_updates`
   - Two RESOURCE_DEPLETED events in same region → two FactionUpdate(tension_delta=0.1) emitted
   - Apply both → cumulative +0.2 (or capped at 1.0)

7. `test_event_with_none_region_id_ignored`
   - WorldEvent(category=RESOURCE_DEPLETED, region_id=None) → no update

## Regression Guard
```bash
pytest tests/unit/faction/ -x -v
```
