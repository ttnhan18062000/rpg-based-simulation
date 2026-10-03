---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260627-P1B-QUEST-ACTIVATION
artifact_type: test_plan
tags: [quest, activation, strategic-intelligence, blockers]
---

# Test Plan: TCK-20260627-P1B-QUEST-ACTIVATION

## Regression Surface (existing tests that must pass)

| Test | Path | Guards |
|---|---|---|
| Quest generation suite | `tests/unit/quest/test_quest_generation.py` | QuestGenerator level banding, determinism, duplicate suppression |
| Quest lifecycle | `tests/unit/quest/test_quest_lifecycle.py` | QuestService add_progress, mark_rewarded |
| Strategic detour PH6 | `tests/unit/strategic/test_strategic_detour_ph6.py` | Detour creation/resumption from material blocker |
| Quest system | `tests/unit/quest/test_quest_system.py` | QuestSystem.update progress/completion |

## New Tests Required (per AC)

### File: `tests/unit/systems/test_quest_activation_pathway.py`

**test_generate_from_blockers_returns_quest_template_for_material_blocker** (AC1, AC2)
- Entity has one unresolved material blocker (kind="material", subject="iron_ore")
- Call `QuestGenerationSystem.generate_from_blockers(entity, tick=100)`
- Assert: returns non-empty list; first template has `kind="resource_expedition"`; objective targets the blocked resource

**test_generate_from_blockers_skips_resolved_blockers** (guard)
- Entity has a resolved blocker and a non-material blocker only
- Assert: `generate_from_blockers()` returns empty list

**test_quest_to_project_produces_valid_project** (AC1, AC2)
- Generate a quest template from a blocker, convert with `quest_to_project(quest, tick)`
- Assert: project has `kind="quest"`, `status=ProjectStatus.ACTIVE`
- Assert: `active_objective_id` is set and points to an objective
- Assert: the objective pointed to by `active_objective_id` has `status=ObjectiveStatus.ACTIVE` (bug fix guard)

**test_quest_project_active_objective_status** (bug fix regression guard)
- Specifically assert that the first/only objective created by `quest_to_project()` has `status=ObjectiveStatus.ACTIVE`, not `UNRESOLVED`
- This is the primary regression guard for the bug fix

**test_quest_activation_pathway_end_to_end** (AC1, AC2)
- Build entity with material blocker via `V2EntityBuilder`
- Call `generate_from_blockers()` → `quest_to_project()`
- Feed resulting project to `StrategicIntelligenceSystem.evaluate_project_switch(entity, project, tick)`
- Assert: project switch accepted; project becomes the current project

## Scoped Pytest Commands

```bash
# New test suite only
pytest tests/unit/systems/test_quest_activation_pathway.py -v

# Regression suite (affected areas)
pytest tests/unit/quest/ tests/unit/strategic/test_strategic_detour_ph6.py -v

# Full scoped run
pytest tests/unit/quest/ tests/unit/systems/test_quest_activation_pathway.py tests/unit/strategic/test_strategic_detour_ph6.py -v
```

## Anti-Drift Test Guards

- `test_quest_project_active_objective_status` directly tests that the first quest objective is `ACTIVE` — any regression to `UNRESOLVED` fails immediately.
- `test_quest_activation_pathway_end_to_end` ensures the quest project is accepted into the strategic system via `evaluate_project_switch()` — guards against future decoupling.
