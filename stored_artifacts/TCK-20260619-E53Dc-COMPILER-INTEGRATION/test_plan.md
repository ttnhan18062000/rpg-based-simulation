# Test Plan — TCK-20260619-E53Dc-COMPILER-INTEGRATION

## Tests: tests/unit/chronicle/test_faction_chronicle.py

1. test_faction_war_declared_event_in_narrative_ledger — scorer returns >= 0.9, is_chronicle_worthy=True
2. test_chronicle_names_the_war — full compile() produces "The Alpha Kingdom War against Beta Empire"
3. test_chronicle_names_territory_transfer — "The Conquest of The Border Wastes"
4. test_chronicle_era_named_age_of_war — 3 war_declared entries produce "The Age of War" era
