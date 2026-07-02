---
ticket_id: TCK-20260619-E62B-CULTURE-DERIVER
phase: test_plan
date: 2026-06-23
---

# Test Plan — TCK-20260619-E62B-CULTURE-DERIVER

## Tests Created

`tests/unit/culture/test_culture_deriver.py` (9 tests):
- test_deriver_empty_hierarchy_returns_zero_culture
- test_deriver_calamity_raises_fatalism
- test_deriver_hero_death_raises_hero_veneration
- test_deriver_entity_death_calamity_cause_raises_fatalism
- test_deriver_inflation_raises_scarcity_memory
- test_deriver_war_events_raise_conflict_exposure
- test_deriver_saturation_clamps_at_1_0
- test_deriver_unknown_event_type_no_effect
- test_deriver_global_fallback_when_no_region_in_payload

`tests/unit/culture/test_culture_exporter.py` (6 tests):
- test_exporter_populates_region_cultures
- test_exporter_overwrites_on_later_episode
- test_exporter_empty_hierarchy_no_error
- test_importer_returns_none_for_unknown_region
- test_importer_returns_culture_for_known_region
- test_exporter_round_trips_through_campaign_state_serialization

## Existing Tests

- tests/unit/campaigns/ — 90 tests pass (orchestrator wiring backward-compatible)
- tests/unit/culture/ — 20 total pass (5 from E62A + 15 new in E62B)

## Result: 110 passed
