# TCK-20260610-REGION-THREAT-PROJECTION — Test Plan

## Test File

`tests/unit/world/test_region_threat_classifier.py`

## Tests

| Test | Pass condition |
|---|---|
| `test_town_region_safe_from_hero` | label == "safe", source == "catalog_projection" |
| `test_goblin_camp_hostile_from_hero` | label == "hostile", source == "catalog_projection" |
| `test_wolf_den_threatened_from_hero` | label == "threatened" (not "hostile") |
| `test_merchant_road_contested_with_bandit_population` | label == "contested" |
| `test_no_factions_returns_unknown` | label == "unknown", source == "no_faction_data" |
| `test_legacy_fallback_monster_horde_faction` | label == "hostile", source == "legacy_fallback" |
| `test_classification_does_not_mutate_catalog` | catalog.factions unchanged after call |
| `test_classification_deterministic` | same result on two calls with same inputs |

## Regression

Run `tests/unit/world/` to confirm no regressions in regional topology, consequences, or sovereignty tests.
