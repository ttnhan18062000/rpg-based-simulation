---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260627-P1B-QUEST-ACTIVATION
artifact_type: investigation
tags: [quest, activation, strategic-intelligence, blockers]
---

# Investigation: TCK-20260627-P1B-QUEST-ACTIVATION

## Current Behavior (file:line refs)

### Quest pathway components

1. **Blocker inference** — `src/systems/strategic_systems/intelligence.py:L70–L197`
   - `infer_blockers()`: infers material, access, and inventory blockers from recent failures
   - `generate_crafting_blockers()`: infers material blockers from recipe requirements

2. **Quest generation from blockers** — `src/systems/world_systems/quests.py:L94–L152`
   - `QuestGenerationSystem.generate_from_blockers(entity, tick)` — iterates over `entity.strategic.blockers`, skips resolved and non-material blockers, returns list of `QuestTemplate` objects
   - `QuestGenerationSystem.quest_to_project(quest, tick)` — converts a `QuestTemplate` to `ProjectState`

3. **Strategic intent evaluation** — `src/systems/strategic_systems/intelligence.py:L1059–L1379`
   - `evaluate_strategic_intent()` creates "detour" projects for entities with active material blockers (via `DetourSuggestionSystem.suggest_detours()`), NOT quest projects
   - `fused_strategic_pass()` orchestrates blocker inference + intent evaluation in one pass

4. **Quest models** — `src/core/models/quests.py`
   - `QuestOpportunity` (world-level opportunity from pressure signals, L66–L82)
   - `QuestState` (entity-level quest project, extends `ProjectState`)
   - `QuestGenerationSystem` produces `ProjectState` with `kind="quest"`, not `QuestState`

### Critical Bug Found

**Location**: `src/systems/world_systems/quests.py:L133–L152` (`quest_to_project`)

```python
objectives = [
    ObjectiveState(
        id=obj.id,
        kind=obj.kind,
        target=obj.target,
        status=ObjectiveStatus.UNRESOLVED   # <<< BUG
    )
    for obj in quest.objectives
]
return ProjectState(
    ...
    active_objective_id=objectives[0].id if objectives else None,
    ...
)
```

The `active_objective_id` field points to the first objective, but that objective has `status=ObjectiveStatus.UNRESOLVED`. The strategic system (`fused_strategic_pass()`) only processes objectives with `status=ObjectiveStatus.ACTIVE`:

```python
# intelligence.py:L396
active_obj = next((o for o in project.objectives if o.id == obj_id), None)
if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:  # REQUIRES ACTIVE
```

This means:
- Blocker resolution for quest objectives never fires
- Navigation to quest objective targets never fires  
- Quest projects are effectively dead on arrival

**Fix**: The first objective in `quest_to_project()` (which becomes `active_objective_id`) must use `ObjectiveStatus.ACTIVE`. Subsequent objectives stay `UNRESOLVED`.

### Gap: `StrategicIntelligenceSystem` does not call `QuestGenerationSystem`

`intelligence.py` never imports or calls `quests.py`'s `QuestGenerationSystem`. The blocker → quest pathway exists as standalone utility logic but is not wired into the strategic evaluation loop. This is by design for the unit-test phase (the ticket explicitly defers end-to-end wiring to post-P0 integration). The unit test will test the pathway components together directly.

## Mechanics/Engine Constraints

- Decision logic must read state, not mutate it — `QuestGenerationSystem` returns templates/projects, does not write to state. This is correct.
- `ObjectiveStatus` enum (`src/core/strategic.py:L26–L31`): `UNRESOLVED`, `ACTIVE`, `RESOLVED`, `FAILED`
- All objectives start `UNRESOLVED` by default; the active objective must be `ACTIVE` for the strategic loop to process it.
- Docs/mechanics/04_strategic_cognition.md covers project creation patterns.

## Parity Ledger Overlap

- `STRAT-150` to `STRAT-163` cover quest creation, progression, and rewards (all `verified`)
- `STRAT-184`: "Strategic project creation is based on current needs/world state" — `status: verified`, no test_path. This ticket adds coverage.
- No existing parity entry covers the blocker-triggered quest activation pathway specifically. A new entry `STRAT-235` will be added.

## Prior Work

- `TCK-20260425-PH8-M1`: Quest lifecycle and reward models
- `TCK-20260427-QUEST-IDENTITY`: Quest identity paradox + authoritative rewards
- `stored_artifacts/TCK-20260425-PH8-M2-GENERATION/`: Prior quest generator implementation

## Risks and Open Questions

- The `StrategicIntelligenceSystem` and `QuestGenerationSystem` are currently decoupled. The unit test will call `generate_from_blockers()` directly (not through `evaluate_strategic_intent()`). This is the correct scope for the unit test phase per the ticket.
- Integration assertion (AC3) is deferred until P0 tickets complete — recorded as out-of-scope.

## Anti-Drift Hazards

- Any future refactor that removes `ObjectiveStatus.ACTIVE` from the initial objective of quest projects will silently break the pathway.
- The `quest_to_project()` function uses a comprehension that applies `UNRESOLVED` to ALL objectives; fixing it must only change the FIRST objective.
