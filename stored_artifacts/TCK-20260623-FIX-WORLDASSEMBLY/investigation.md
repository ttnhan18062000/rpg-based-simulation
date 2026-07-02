---
ticket_id: TCK-20260623-FIX-WORLDASSEMBLY
phase: investigation
date: 2026-06-23
status: complete
---

# Investigation: TCK-20260623-FIX-WORLDASSEMBLY

## Current Behavior

Two independent failures block all worldassembly and integration tests:

1. `tests/unit/worldassembly/test_assembly.py::test_structural_world_assembly_resolver` fails with:
   ```
   InvalidWorldSpecError: Assembly validation failed with blocking errors:
   [CAT-REL-016] Region 'river_ford' references non-existent terrain 'river'
   ```
   Source: `src/worldassembly/resolver.py:712`

2. `tests/unit/core/test_catalog_smoke_simulation.py::test_catalog_mode_smoke_simulation` fails with:
   ```
   ValidationError: 1 validation error for WorldSpec
   quest_definitions.0.type — Field required
   ```
   Source: `tests/unit/core/test_catalog_smoke_simulation.py:85` — `WorldSpec.model_validate(spec_data)`

---

## Root Cause 1: river_ford terrain reference

### What references it
- `data/content/world_modules/river_crossing.yaml` (line 14) defines region `river_ford` with `terrain: "river"`
- `data/content/world/runtime_regions.yaml` (lines 129–134) registers `river_ford` as a runtime region (biome: `near_forest`, no terrain field there — that is a separate catalog concept)

### How validation fires
- `src/content/reference_graph.py:280`: when scanning module regions, adds graph edge `region:river_ford → terrain:river` (lowercased)
- `src/content/reference_graph.py:236–238`: built-in terrain nodes seeded are only `{grass, floor, hill, sand}`
- `src/content/validator.py:648–670`: edge-walk finds `terrain:river` has no graph node → fires `CAT-REL-016` (region → non-existent target) with message `Region 'river_ford' references non-existent terrain 'river'`
- `src/worldassembly/resolver.py:709–712`: the WorldAssembly validator wraps content validator results; any blocking error raises `InvalidWorldSpecError`

### What is missing
`data/content/world/terrain.yaml` contains: `plain`, `forest`, `swamp`, `cave`, `mountain`, `ruin`, `road`, `snow`, `volcanic`. **`river` is absent.**

The `biomes.yaml` terrain_mix values for `near_forest` do not include `river` either — confirming `river` was never registered as a terrain type.

### The fix
Add a `river` terrain entry to `data/content/world/terrain.yaml`:
```yaml
# STATE: ADDITIONAL
- id: "river"
  display_name: "River"
  move_cost_multiplier: 1.8
  hazard_multiplier: 1.4
```
This is the minimal correct fix: `river_crossing.yaml` authoritatively says `terrain: "river"` and the module was added during the worldgen epic (TCK-20260619-E13B-MODULE-TYPES, evidenced by the comment on line 121 of `runtime_regions.yaml`). The terrain entry was simply never added to the catalog.

Alternative (do NOT take): changing `river_crossing.yaml` to use an existing terrain like `plain` would silently misrepresent the module's semantics. The terrain value is meaningful for movement cost and hazard calculations.

---

## Root Cause 2: quest_definitions missing `type` field

### Where the schema requires it
`src/worldbuilding/schema.py:99`:
```python
type: Literal["escort", "hunt", "fetch", "explore", "defend", "investigate"] = Field(
    ..., description="Quest archetype category"
)
```
`type` has no default — it is strictly required (`...`).

### The migration path
`src/worldbuilding/schema.py:142–148`: `_migrate_quests_field` migrates the legacy `quests` key → `quest_definitions` key at validation time, but does NOT remap legacy field names (`kind` → `type`, etc.).

### The broken fixture
`tests/unit/core/test_catalog_smoke_simulation.py:61–72` — the `create_smoke_spec()` function supplies a quest dict under the `quests` key with legacy fields:
```python
"quests": [
    {
        "id": "hunt_beasts",
        "name": "Hunt Wild Beasts",
        "kind": "hunt",          # <-- legacy field; schema expects "type"
        "goal_value": 3.0,
        "reward": {...},
        "target_role": "raider",
        "target_region_id": "near_forest",
        "assignee": "citizen"
    }
]
```
After migration `quests` → `quest_definitions`, Pydantic validates the dict as `QuestDefinition` and finds `type` missing (the dict has `kind`, not `type`; all other fields are also non-schema).

### Content YAML check
All 17 world module YAML files with `quest_definitions` were checked — **every one has a `type` field**. The content YAMLs are already compliant. Only this test fixture uses the old schema.

### The fix
Update `create_smoke_spec()` in `tests/unit/core/test_catalog_smoke_simulation.py` to supply a valid `QuestDefinition`-shaped dict. The minimal compliant dict:
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
Use `quest_definitions` directly (skip the `quests` migration path since this is a test fixture, not legacy data). Drop all non-schema legacy fields (`name`, `kind`, `goal_value`, `reward`, `target_role`, `target_region_id`, `assignee`).

---

## Mechanics/Engine Constraints

- `docs/mechanics/06_worldbuilding_foundation.md` governs terrain types as part of declarative topology. Adding `river` is a content extension within spec.
- `docs/engine/authoritative_pipeline.md`: content catalog mutations (adding terrain entries) are safe at this layer — they extend the registry, not the resolution pipeline.
- No parity formula is affected; terrain entries are reference data only (move_cost_multiplier, hazard_multiplier).
- `QuestDefinition.type` is an authoring-time field (not a runtime quest instance). No simulation mechanic references it at tick time.

---

## Parity Ledger Overlap

- `docs/parity_ledger/substrate.yaml` — may have an entry for content catalog integrity/terrain registration. Check and update if a `missing`/`divergent` entry exists for terrain coverage.
- No combat or progression parity entries are affected.
- `infrastructure.yaml` parity — no overlap.

---

## Risks and Open Questions

1. **move_cost_multiplier / hazard_multiplier values for `river`**: The ticket says to add the entry; the exact values are not mandated by the Mechanics Bible. Using `move_cost_multiplier: 1.8` and `hazard_multiplier: 1.4` follows the pattern of other high-friction terrains (swamp=1.5×, mountain=1.7×). River should be slightly harder than mountain due to water crossing. This is an assumption — if a specific value is preferred, it can be adjusted.

2. **`river` in biomes.yaml `terrain_mix`**: The `near_forest` biome does not include `river` in its `terrain_mix`. This is not currently validated (biome terrain_mix is descriptive, not a strict set), so it is not blocking. Out of scope for this ticket.

3. **Other quest fixtures**: All other test files using `QuestDefinition` (test_quest_merge.py, test_quest_definition.py, test_world_compiler.py) construct `QuestDefinition` objects or dicts that already have `type`. No other fixture has the legacy-field problem.

4. **Cascade of ~70 failures**: Both root causes are independent. Fixing RC1 unblocks the worldassembly tests and integration matrix tests. Fixing RC2 unblocks the catalog smoke simulation test. Together they should clear all ~70 failures listed in the acceptance criteria.

---

## Fix Plan

### Fix 1 — Add `river` terrain to catalog
**File:** `data/content/world/terrain.yaml`
**Change:** Append a new entry at the bottom (after `volcanic`):
```yaml
# STATE: ADDITIONAL
- id: "river"
  display_name: "River"
  move_cost_multiplier: 1.8
  hazard_multiplier: 1.4
```
No other files need changing — `river_crossing.yaml`'s `terrain: "river"` reference is correct.

### Fix 2 — Update smoke test fixture
**File:** `tests/unit/core/test_catalog_smoke_simulation.py`
**Function:** `create_smoke_spec()` (lines 33–73)
**Change:** Replace the `"quests"` list with a `"quest_definitions"` list using the current `QuestDefinition` schema shape. Remove all legacy fields. Keep `"id"`, add `"type": "hunt"`, use `required_participant_tags`, `required_location_tags`, `reward_budget`.

### Verification
After both fixes:
- Run `pytest tests/unit/worldassembly/ tests/unit/core/test_catalog_smoke_simulation.py tests/integration/content/ tests/integration/content_packs/ tests/integration/scenarios/test_scenario_catalog_matrix.py -x -q`
- Expected: all pass, no blocking errors.
