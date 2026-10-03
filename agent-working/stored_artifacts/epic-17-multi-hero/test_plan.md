---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: epic-17-multi-hero
artifact_type: test_plan
tags: [epic, multi, hero]
---

# Test Plan: Epic 17 Multi-Hero

## Scope
Validate the independence of 4 concurrent AI heroes operating in the same Engine grid, ensure Name-generation mapping is purely deterministic, and that Permadeath correctly respawns generic Generation N+1 variants without tanking the backend memory structure.

### 1. Engine Load Tests
- **Objective:** Modify existing `PyTest` End-to-End loops to fire up with `config.hero_count=5`.
- **Verification:** Run `pytest tests/e2e/`. Ensure all 5 concurrent heroes naturally run their AI, hunt monsters independently, and successfully load into local JSON test states.

### 2. Permadeath Verification
- **Objective:** Artificially enforce fatal HP damage against a targeted Hero entity 4 consecutive times via `pytest` fixtures.
- **Verification:** Verify that `death_count == 4` drops the entire inventory on the final death, successfully deletes the hero entity ID tracking, and prompts an emergent level 1 hero to spawn at Generation + 1.

### 3. Combat Familiarity
- **Objective:** Place 2 specific heroes inside 1 tile distance and spam ticks.
- **Verification:** Assert that `hero.familiarity` bridges from 0 to 1 over roughly 500 artificial ticks, and dynamically verifies the combat `apply` modifiers are yielding flat +10% conditional ATK modifications inside the Damage Calculator constraints.
