---
ticket_id: TCK-20260619-E13-CONTENT-FOUNDATION
phase: test_plan
date: 2026-06-20
---

# Test Plan: Content Foundation Layer

## Integration Tests (new file: tests/integration/scenarios/test_content_foundation.py)

Written during E13C and E13D:

### test_quest_starts_in_urban_political
- 400-tick urban_political simulation (seed=42)
- Assert: ≥1 quest_started event in simulation_events (or quest_status_counts["ACTIVE"] >= 1)
- Depends on: E13A adding quest_definitions to urban_political modules

### test_crafting_chain_completes
- 1000-tick run in a world with crafting infrastructure (blacksmith + materials)
- Assert: at least one recipe's output item appears in an entity's inventory
- Depends on: E13C adding gather→craft chain and expanding recipe count

### test_all_world_compositions_have_two_scenarios
- Schema-only test — no simulation
- Load data/content/simulation_scenarios/*.yaml
- Assert each world_id appears as world_composition ≥2 times
- Depends on: E13D adding ≥2 scenarios per world

## Validation Tests (existing infrastructure)

Run per child ticket after authoring:
```bash
# Module validation
python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"

# Recipe/item catalog validation
python3 -c "from src.content.repository import CatalogRepository; r = CatalogRepository('data/content'); r.load_all(); print('OK')"

# World composition smoke (all 5 named worlds)
pytest tests/integration/worldassembly/test_e2e_smoke.py -x -v
```
