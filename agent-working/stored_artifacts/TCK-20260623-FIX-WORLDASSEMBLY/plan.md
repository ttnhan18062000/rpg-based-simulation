# Plan — TCK-20260623-FIX-WORLDASSEMBLY

## Summary

Two surgical changes. No other files affected.

Files changed:
1. `data/content/world/terrain.yaml` — add missing `river` terrain entry
2. `tests/unit/core/test_catalog_smoke_simulation.py` — replace legacy `"quests"` dict with schema-compliant `"quest_definitions"` dict

## Step 1: Add `river` terrain to terrain.yaml

Append after the final `volcanic` entry:

```yaml
- id: "river"
  display_name: "River"
  move_cost_multiplier: 1.8
  hazard_multiplier: 1.4
```

River crossing is harder than mountain (1.7) due to water resistance, and slightly more hazardous than swamp (1.5). The `id` must be `"river"` (lowercase) to match `river_crossing.yaml`'s `terrain: "river"` declaration.

## Step 2: Update create_smoke_spec() in the test file

Replace the `"quests"` block (~lines 61-72) with:

```python
        "quest_definitions": [
            {
                "id": "hunt_beasts",
                "type": "hunt",
                "required_participant_tags": ["hostile"],
                "required_location_tags": ["wilderness"],
                "reward_budget": 100
            }
        ]
```

- Key: `"quests"` → `"quest_definitions"` (bypasses the migration path entirely)
- Field: `"kind"` → `"type"` (matches `QuestDefinition.type` Literal field at schema.py:99)
- Remove all non-schema legacy fields

## Parity Ledger

No updates needed. No substrate.yaml entry references CAT-REL-016 or the `river` terrain gap.

## Test Commands

```bash
pytest tests/unit/worldassembly/ -x -q
pytest tests/unit/core/test_catalog_smoke_simulation.py -x -q
pytest tests/unit/worldassembly/ tests/unit/core/test_catalog_smoke_simulation.py \
       tests/integration/content/ tests/integration/content_packs/ \
       tests/integration/scenarios/test_scenario_catalog_matrix.py -x -q
```
