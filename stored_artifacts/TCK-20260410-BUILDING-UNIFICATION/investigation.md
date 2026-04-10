# Investigation: TCK-20260410-BUILDING-UNIFICATION

## Current Hybrid Pattern
In `src/ai/states/town.py`, the `VisitGuildHandler` performs:
```python
if revealed:
    return AIState.VISIT_GUILD, ActionProposal(
        ...,
        updates=[PerceptionUpdate(terrain_memory=revealed)]
    )
...
if goal_text not in actor.mind.decision.goals:
     new_goals.append(goal_text)
...
strategic_up = StrategicKnowledgeIngestionService.ingest_guild_intel(...)
```
This means the same "fact" (material location) is being pushed into three different domains (Perception, Decision/Goals, Strategic). This redundant state leads to "strategic drift" where the AI might have a goal string "Guild tip: iron_ore" but no corresponding `LeadRecord`, or vice-versa.

## Target Architecture
The handler should act as a pure sensor aggregator.
1. Capture raw world state (camps_found, resources_found, recipe_needs).
2. Call `StrategicKnowledgeIngestionService` to produce the **Durable Strategic Record**.
3. Call `PerceptionUpdate` only for the **Immediate Map Discovery** (neighboring terrain reveal).
4. Remove all `MindUpdate(goals_add)` for building intel.

---

# Test Plan: TCK-20260410-BUILDING-UNIFICATION

## Functional Tests
- `tests/test_building_unification.py`:
    - **Guild Discovery**: Entity visits Guild hall. Verify `StrategicUpdate` contains expected `LeadRecord` and `CandidateZoneRecord`. Verify NO `MindUpdate(goals_add)` is present.
    - **Blacksmith Blocker**: Entity visits Blacksmith without materials. Verify `StrategicUpdate` contains a `BlockerRecord` for the missing material. Verify zero "Need X" strings in action reason or goal list.
    - **Detour Derivation**: 
        1. Inject a material blocker into an entity.
        2. Inject a corresponding material lead.
        3. Run `DetourSuggestionService.suggest_detours`.
        4. Verify an `ObjectiveRecord` is generated with the correct coordinates from the lead.

## Integration Tests
- **Simulation Loop**: Verify that entities can complete the "Blacksmith -> Guild -> Field -> Blacksmith" loop using only strategic records for detour navigation.
- **Snapshot Purity**: Verify that the new `LeadRecord` and `BlockerRecord` structures do not introduce aliasing bugs in `Snapshot.from_world`.
