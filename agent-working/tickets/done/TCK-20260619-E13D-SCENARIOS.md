---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13D-SCENARIOS
phase: done
date: 2026-06-20
tags: [content, scenarios, world-compositions, phase-1]
---

# TCK-20260619-E13D-SCENARIOS

## Title
Epic 1.3D · Scenario Authoring (dungeon / urban / wilderness)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
D07 F4: 8 scenarios all using frontier_survival composition (Gap Risk 5/15). Three world compositions — dungeon_crawl, urban_political, wilderness_survival — have zero scenarios. This ticket authors ≥2 scenarios each for those three worlds and writes the integration tests specified in the E13 test plan.

## Scope

### Target compositions and their scenario counts

| World Composition | Current Scenarios | Target |
|---|---|---|
| dungeon_crawl | 0 | ≥ 2 |
| urban_political | 0 | ≥ 2 |
| wilderness_survival | 0 | ≥ 2 |
| frontier_survival | 8 (existing) | keep as-is |

### Scenario YAML schema

Inspect `data/content/simulation_scenarios/` for the authoritative format. Expected fields:
```yaml
id: "<scenario_id>"
world_composition: "<world_id>"
focus_modules: [<module_id>, ...]
perspective: "<entity_archetype_tag>"
initial_conditions:
  entity_count: <int>
  seed: <int>
  tick_limit: <int>
  # other world-specific conditions
```
Confirm actual schema before authoring — do NOT invent fields.

### Scenarios to author

**dungeon_crawl (2 scenarios):**

1. `dungeon_crawl_delve` — Standard dungeon run
   - `focus_modules`: primary dungeon conflict modules (check dungeon_crawl composition for its required_modules)
   - `perspective`: "warrior"
   - `initial_conditions`: entity_count=5, seed=42, tick_limit=200

2. `dungeon_crawl_desperate_descent` — High-difficulty variant
   - Higher entity mortality expected
   - `perspective`: "scout"
   - `initial_conditions`: entity_count=3, seed=99, tick_limit=300

**urban_political (2 scenarios):**

3. `urban_political_trade_war` — Economic pressure scenario
   - Focus: trading company modules, resource scarcity
   - `perspective`: "merchant"
   - `initial_conditions`: entity_count=8, seed=42, tick_limit=400

4. `urban_political_faction_struggle` — Political/conflict variant
   - Focus: conflict modules in urban context
   - `perspective`: "warrior"
   - `initial_conditions`: entity_count=6, seed=77, tick_limit=300

**wilderness_survival (2 scenarios):**

5. `wilderness_survival_long_hunt` — Resource attrition
   - Focus: ecology + wolf_den modules
   - `perspective`: "hunter"
   - `initial_conditions`: entity_count=4, seed=42, tick_limit=500

6. `wilderness_survival_warden_escort` — Escort/cooperation
   - Focus: forest_warden_grove module
   - `perspective`: "scout"
   - `initial_conditions`: entity_count=6, seed=55, tick_limit=300

### Integration tests (new file: `tests/integration/scenarios/test_content_foundation.py`)

Three tests from the E13 test plan:

#### test_quest_starts_in_urban_political
```python
@pytest.mark.integration
@pytest.mark.slow
def test_quest_starts_in_urban_political():
    """Assert at least 1 quest activates in a 400-tick urban_political run."""
    # Build kernel with urban_political, seed=42
    # Run 400 ticks
    # Assert: quest_started events > 0 OR quest_status_counts["ACTIVE"] >= 1
    # (depends on E13A adding quest_definitions to urban_political modules)
```

#### test_crafting_chain_completes
```python
@pytest.mark.integration
@pytest.mark.slow
def test_crafting_chain_completes():
    """Assert gather→craft chain produces output in a 1000-tick world with blacksmith."""
    # Use a world with crafting infrastructure (settled_quarter from E13B)
    # Run 1000 ticks
    # Assert: at least one entity has 'steel' or 'ember_axe' in inventory
    # Fallback assertion: recipe_executed event count > 0
```

#### test_all_world_compositions_have_two_scenarios
```python
@pytest.mark.unit
def test_all_world_compositions_have_two_scenarios():
    """Schema-only: every named world_composition has ≥2 scenarios."""
    import yaml, glob
    scenario_files = glob.glob("data/content/simulation_scenarios/*.yaml")
    world_counts = {}
    for f in scenario_files:
        with open(f) as fh:
            docs = list(yaml.safe_load_all(fh))
        for doc in docs:
            wc = doc.get("world_composition")
            if wc:
                world_counts[wc] = world_counts.get(wc, 0) + 1
    for world_id in ["dungeon_crawl", "urban_political", "wilderness_survival"]:
        assert world_counts.get(world_id, 0) >= 2, f"{world_id} has {world_counts.get(world_id, 0)} scenarios, need ≥2"
```

## Out of Scope
- New world compositions
- Scenario engine modifications
- Dynamic scenario generation
- Scenario difficulty scaling (Epic 2.X)

## Acceptance Criteria
- 6 new scenario definitions authored (2 per target composition)
- `tests/integration/scenarios/test_content_foundation.py` file exists with all 3 tests
- `test_all_world_compositions_have_two_scenarios` passes (schema-only, no simulation)
- `test_quest_starts_in_urban_political` and `test_crafting_chain_completes` are present (may be marked skip if E13A/E13C not yet done)
- `pytest tests/unit/ -x -v` passes (no regressions)

## Related Tickets
- TCK-20260619-E13-CONTENT-FOUNDATION (parent epic)
- TCK-20260619-E13A-QUEST-DEFS (provides quest defs used in `test_quest_starts_in_urban_political`)
- TCK-20260619-E13C-RECIPES (provides gather→craft chain used in `test_crafting_chain_completes`)

## Related Docs
- `docs/mechanics/05_world_evolution.md` (scenario progression rules)
- `docs/audits/D07_content_depth.md` (update F4 count on completion)
- `staging_artifacts/TCK-20260619-E13-CONTENT-FOUNDATION/test_plan.md` (authoritative test plan)

## Related Code Areas
- `data/content/simulation_scenarios/` (new scenario files)
- `tests/integration/scenarios/test_content_foundation.py` (new test file)
- `src/content/repository.py` (scenario loading)

## Assumptions / Open Questions
- What is the exact scenario YAML format? Read one existing scenario in `data/content/simulation_scenarios/` before authoring to confirm fields (especially `focus_modules`, `initial_conditions` subfields, and whether multi-document YAML is used).
- Does `world_composition` in the scenario schema match the directory name in `data/content/world_compositions/` exactly?
- Does `perspective` match entity archetype IDs or tag strings?
- Is `test_quest_starts_in_urban_political` runnable without E13A done? If not, mark it `@pytest.mark.skip(reason="needs E13A quest defs")` with a clear revisit trigger.

## Implementation Notes
- Write all scenario files first, then write the test file.
- For `test_crafting_chain_completes`: if the settled_quarter module from E13B is not included in any world composition, this test may need a custom world fixture rather than a named world. Use `@pytest.mark.skip` with a clear note if so.
- Follow `test_balance_regression.py` pattern for kernel setup (`_build_kernel`, `try/finally: kernel.shutdown()`).
- If `focus_modules` requires module IDs, confirm they match `module_id` fields in the YAML files (not filenames without extension).
- Always call `kernel.shutdown()` in finally block to prevent `QueueDrainWorker` thread leak.
- Run `make knowledge-index-update` if any `docs/` files were touched.

## Test Summary
```bash
# Schema test (fast, no simulation)
pytest tests/integration/scenarios/test_content_foundation.py::test_all_world_compositions_have_two_scenarios -x -v

# Unit suite (no regressions)
pytest tests/unit/ -x -v

# Integration tests (slow, optional — run if E13A/E13C done)
pytest tests/integration/scenarios/test_content_foundation.py -x -v -m "not slow"
```

## Implementation Notes
- Scenario YAML schema uses faction-based perspective IDs (e.g. `hero_guild_perspective`),
  NOT entity archetype tags. Ticket suggestion of `warrior`/`scout`/`merchant`/`hunter`
  corrected to canonical values from `data/content/social/perspectives.yaml`.
- `initial_conditions` uses world-specific semantic keys (matching existing frontier_scenarios.yaml
  format), NOT `entity_count`/`seed`/`tick_limit` as suggested in ticket scope.
- `wilderness_survival_warden_escort` uses `undead_battlefield` focus module (which IS in the
  wilderness_survival composition) instead of `forest_warden_grove` (which is NOT).
- `test_crafting_chain_completes` marked `@pytest.mark.skip` because `settled_quarter` module
  (provider of blacksmith_service) is not in any named world composition.
- Pre-existing test failures (test_catalog_scenario_state_builder, test_combat_reward_trace)
  confirmed not caused by this ticket.

## Files Changed
- `data/content/simulation_scenarios/dungeon_crawl_scenarios.yaml` — new (2 scenarios)
- `data/content/simulation_scenarios/urban_political_scenarios.yaml` — new (2 scenarios)
- `data/content/simulation_scenarios/wilderness_survival_scenarios.yaml` — new (2 scenarios)
- `tests/integration/scenarios/test_content_foundation.py` — new (3 tests)
- `docs/audits/D07_content_depth.md` — F5 marked RESOLVED, F3 also marked RESOLVED

## Completion Summary
Authored 6 new scenario definitions (2 each for dungeon_crawl, urban_political,
wilderness_survival), bringing total simulation_scenarios from 8 to 14 across 4 world
compositions. All three previously zero-scenario target compositions now have ≥2 scenarios.
Perspective IDs corrected to canonical faction-based values; initial_conditions fields follow
the actual YAML schema (semantic condition keys, not entity_count/seed/tick_limit).
Integration test file authored with all 3 E13 test plan tests: schema test passes,
quest test is runnable (E13A done), crafting test skipped (settled_quarter not in any
composition). D07 F5 finding marked RESOLVED. Knowledge index updated.
