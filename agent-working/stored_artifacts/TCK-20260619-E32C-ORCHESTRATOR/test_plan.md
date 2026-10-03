---
ticket_id: TCK-20260619-E32C-ORCHESTRATOR
date: 2026-06-21
phase: test_plan
status: complete
---

# Test Plan — TCK-20260619-E32C-ORCHESTRATOR

## Regression Surface (existing tests that must pass)

The following suites are in-scope for regression — they must all pass before and after E32C implementation.

| Suite | Command | Rationale |
|---|---|---|
| CampaignState unit tests | `pytest tests/unit/campaigns/test_campaign_state.py -x -v` | E32C populates CampaignState — no model changes allowed without updating this suite |
| Campaign unit suite (all) | `pytest tests/unit/campaigns/ -x -v` | 40 tests covering analysis-domain campaigns; must stay green (different code path but same package) |
| ScenarioRuntimeService unit tests | `pytest tests/unit/engine/test_scenario_runtime_service.py -x -v` | E32C calls `ScenarioRuntimeService`; if a `final_state` property is added, these tests must still pass |
| ScenarioRuntimeService integration | `pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v` | Covers objective evaluation and checkpoint/restore; must not regress |
| Architecture guard — state.py no-engine-imports | `pytest tests/unit/campaigns/test_campaign_state.py::test_campaign_state_module_has_no_engine_imports -x -v` | Ensures state.py remains pure; E32C must not add engine imports there |

---

## New Tests Required (per Acceptance Criteria)

### Integration tests (primary)

**File:** `tests/integration/scenarios/test_campaign_runtime.py`

#### TC-1: `test_entity_state_persists_across_episodes`

**AC:** HERO entity at level 5 in episode 1 starts episode 2 at level 5.

```
Given: A CampaignOrchestrator with a 2-episode manifest
       Episode 1 scenario has tick_limit=50 and at least one entity
       Entity in episode 1 has evolution_level >= 1
When:  orchestrator.run_episode()  # episode 0
       orchestrator.run_episode()  # episode 1
Then:  The entity appears in orchestrator.state.persistent_entities
       EntityCarryForward.level == entity.identity.evolution_level from episode 1 final state
       Episode 2 starts with that entity at the carried-forward level
```

Marker: `@pytest.mark.slow` (runs real kernel ticks).

#### TC-2: `test_dead_faction_absent_in_episode_2`

**AC:** Faction destroyed in episode 1 not spawned in episode 2.

```
Given: A CampaignOrchestrator with a 2-episode manifest
       Episode 1 produces a final state where all entities of faction X are inactive (lifecycle.active=False)
When:  orchestrator.run_episode()  # episode 0
       orchestrator.run_episode()  # episode 1
Then:  orchestrator.state.persistent_factions[faction_id].alive is False
       Episode 2 kernel does not spawn any entity with that faction
```

Marker: `@pytest.mark.slow`.

#### TC-3: `test_episode_history_accumulates`

**AC:** `CampaignState.episode_history` has 2 entries after 2 episodes.

```
Given: A CampaignOrchestrator with a 3-episode manifest
When:  orchestrator.run_episode()  # episode 0
       orchestrator.run_episode()  # episode 1
Then:  len(orchestrator.state.episode_history) == 2
       episode_history[0].episode_index == 0
       episode_history[1].episode_index == 1
       Each entry has a valid completed_tick > 0
```

Marker: `@pytest.mark.slow`.

---

### Unit tests (orchestrator logic, mocked kernel)

**File:** `tests/unit/campaigns/test_campaign_orchestrator.py`

These use mock/stub `ScenarioRuntimeService` to test orchestrator logic without running real Kernel ticks.

#### TC-4: `test_orchestrator_constructs_with_initial_state`

```
Given: A CampaignManifest with campaign_id="test" and 3 episodes
When:  CampaignOrchestrator(manifest) constructed
Then:  orchestrator.state.campaign_id == "test"
       orchestrator.state.episode_index == 0
       orchestrator.state.episode_history == []
```

#### TC-5: `test_advance_state_extracts_entity_carry_forward`

```
Given: A mock AuthoritativeState with 2 entities:
       - entity_id=1, identity.evolution_level=5, identity.evolution_points=1200,
         lifecycle.active=True, social.public_reputation=1.3,
         equipment.slots={MAIN_HAND: "sword_iron"}, equipment.durability={MAIN_HAND: 0.9}
       - entity_id=2, lifecycle.active=False
When:  orchestrator._extract_entity_carry_forwards(state)
Then:  result[1].level == 5
       result[1].xp == 1200
       result[1].alive is True
       result[1].reputation == pytest.approx(1.3)
       result[1].equipment == {"slots": {"MAIN_HAND": "sword_iron"}, "durability": {"MAIN_HAND": 0.9}}
       result[2].alive is False
```

#### TC-6: `test_advance_state_synthesizes_faction_carry_forward`

```
Given: A mock AuthoritativeState with 3 entities:
       - entity_id=1, identity.faction=1, lifecycle.active=True
       - entity_id=2, identity.faction=1, lifecycle.active=False
       - entity_id=3, identity.faction=2, lifecycle.active=False
When:  orchestrator._extract_faction_carry_forwards(state)
Then:  result["faction_1"].alive is True    (at least one active entity)
       result["faction_2"].alive is False   (all inactive)
       (faction_id string form matches the chosen int→str convention)
```

#### TC-7: `test_run_episode_appends_to_episode_history`

```
Given: CampaignOrchestrator with stubbed ScenarioRuntimeService (objective_state=OBJECTIVE_MET at tick=50)
When:  orchestrator.run_episode()
Then:  len(orchestrator.state.episode_history) == 1
       orchestrator.state.episode_index == 1
       episode_history[0].completed_tick == 50
       episode_history[0].episode_index == 0
```

#### TC-8: `test_run_episode_raises_when_no_episodes_remain`

```
Given: CampaignOrchestrator at episode_index == len(episodes)
When:  orchestrator.run_episode()
Then:  RuntimeError raised ("no more episodes")
```

#### TC-9: `test_dead_entity_excluded_from_next_episode_spawn`

```
Given: persistent_entities has entity_id=5 with alive=False
When:  orchestrator._get_spawn_entities()
Then:  entity_id=5 not in result
```

#### TC-10: `test_destroyed_faction_excluded_from_next_episode_spawn`

```
Given: persistent_factions has faction_id="faction_2" with alive=False
When:  orchestrator._get_spawn_factions()
Then:  "faction_2" not in result
```

#### TC-11: `test_equipment_keys_are_strings_in_carry_forward`

```
Given: entity with equipment.slots={EquipSlot.MAIN_HAND: "sword"} (EquipSlot enum key)
When:  orchestrator._extract_entity_carry_forwards(state)
Then:  result[entity_id].equipment["slots"] keys are strings (not EquipSlot enums)
       "MAIN_HAND" in result[entity_id].equipment["slots"]
```

#### TC-12: `test_alive_uses_lifecycle_active_not_combat_alive`

```
Given: entity with lifecycle.active=False and combat.alive=True (combat-dead logic, lifecycle active)
       AND entity with lifecycle.active=True and combat.alive=False (in-combat dead, lifecycle active)
When:  orchestrator._extract_entity_carry_forwards(state)
Then:  entity with lifecycle.active=False → carry_forward.alive is False (regardless of combat.alive)
       entity with lifecycle.active=True → carry_forward.alive is True (regardless of combat.alive)
```

#### TC-13: `test_episode_summary_has_correct_index_and_tick`

```
Given: Run episode 0 with tick=75 at terminal state
When:  EpisodeSummary built from run_episode()
Then:  summary.episode_index == 0
       summary.completed_tick == 75
```

---

### Architecture / Import Guards

**File:** `tests/architecture/test_campaign_orchestrator_guards.py` (or add to existing campaign unit tests)

#### TC-14: `test_orchestrator_does_not_import_via_state_module`

```
AST-parse src/domains/campaigns/orchestrator.py
Assert: all engine imports go through orchestrator.py's own imports
Assert: src.domains.campaigns.state still has no engine imports (re-verify Guard-4)
```

#### TC-15: `test_campaign_state_importable_alongside_orchestrator`

```
from src.domains.campaigns.state import CampaignState
from src.domains.campaigns.orchestrator import CampaignOrchestrator
Assert: no ImportError; these co-exist
```

---

## Scoped Pytest Commands

### Pre-implementation regression baseline

```bash
pytest tests/unit/campaigns/ -x -v
pytest tests/unit/engine/test_scenario_runtime_service.py -x -v
pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v -m "not slow"
```

### During implementation — unit tests only (fast)

```bash
pytest tests/unit/campaigns/test_campaign_orchestrator.py -x -v
pytest tests/unit/campaigns/ -x -v
```

### Acceptance criteria verification (integration, slow)

```bash
pytest tests/integration/scenarios/test_campaign_runtime.py::test_entity_state_persists_across_episodes -x -v -m slow
pytest tests/integration/scenarios/test_campaign_runtime.py::test_dead_faction_absent_in_episode_2 -x -v -m slow
pytest tests/integration/scenarios/test_campaign_runtime.py::test_episode_history_accumulates -x -v -m slow
```

### Full scope check before finalization

```bash
pytest tests/unit/campaigns/ tests/unit/engine/test_scenario_runtime_service.py tests/integration/scenarios/ -x -v -m "not slow"
pytest tests/integration/scenarios/test_campaign_runtime.py -x -v -m slow
```

---

## Anti-Drift Test Guards

| Risk | Guard test | Location |
|---|---|---|
| `lifecycle.active` vs `combat.alive` confusion | TC-12 above | `test_campaign_orchestrator.py` |
| `EquipSlot` enum keys not stringified | TC-11 above | `test_campaign_orchestrator.py` |
| `state.py` engine import creep | TC-14 (AST guard, re-run Guard-4) | architecture test or campaign unit test |
| Episode history not accumulated correctly | TC-7, TC-3 | unit + integration |
| Dead entity not filtered from next episode spawn | TC-9, TC-2 | unit + integration |
| Faction alive when >=1 entity with that faction_int is active | TC-6 | unit |
| episode_index not incremented after run_episode | TC-7 | unit |
| Analysis-domain `CampaignSpec` vs orchestrator spec naming collision | TC-15 import test | architecture test |
