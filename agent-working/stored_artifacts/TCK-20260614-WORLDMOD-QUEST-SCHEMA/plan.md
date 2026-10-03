# Plan: TCK-20260614-WORLDMOD-QUEST-SCHEMA

## Overview
Replace `WorldSpec.quests: list[dict[str, Any]]` with a typed `QuestDefinition` Pydantic model and `quest_definitions: List[QuestDefinition]` field. Add backward-compat migration validator since `data/worlds/sandbox_world/world.yaml` uses `quests: []`.

## Step 1: Add `QuestDefinition` to `src/worldbuilding/schema.py`
- Frozen Pydantic model with fields: `id`, `type` (Literal), `required_participant_tags`, `required_location_tags`, `reward_budget`, `procedural_hints`, `tags`, `source_module`
- Add necessary imports: `List`, `Dict`, `Literal` from `typing`
- Place before `WorldSpec` class

## Step 2: Update `WorldSpec` in `src/worldbuilding/schema.py`
- Replace `quests: list[dict[str, Any]] = Field(default_factory=list)` with `quest_definitions: List[QuestDefinition] = Field(default_factory=list)`
- Add `@model_validator(mode="before")` to migrate `quests` → `quest_definitions` (handles `quests: []` in sandbox_world/world.yaml)
- Remove `Any` from imports if no longer used (check — `Any` is still used in `QuestDefinition.procedural_hints`)

## Step 3: Update `src/worldbuilding/cli.py`
- Line 349: `len(template.quests)` → `len(template.quests)` — NOTE: this is `WorldTemplateSpec.quests` (recipe.py), NOT `WorldSpec.quests`. Leave this one alone.
- Line 362: `len(spec.quests)` → `len(spec.quest_definitions)` — this IS `WorldSpec`, update it.

## Step 4: Update `src/worldbuilding/compiler.py`
- Line 311: `for quest_idx, q_data in enumerate(spec.quests):` → `for quest_idx, q_def in enumerate(spec.quest_definitions):`
- Update the loop body to use `QuestDefinition` fields (`q_def.id`, `q_def.type`) instead of old dict `.get()` calls
- Since `QuestDefinition` is authoring schema (no `goal_value`, `reward`, etc.), build a minimal `QuestState` from the authoring fields or skip the runtime build
- The compiler builds `QuestState` objects for immediate activation — with the new schema, `QuestDefinition.type` maps to quest archetype. Build minimal QuestState seeded from authoring data.

## Step 5: Update `src/worldbuilding/recipe.py`
- Line 140: `"quests": list(template.quests)` — this references `WorldTemplateSpec.quests` (recipe model), NOT `WorldSpec`. The expander produces a dict that is then validated as `WorldSpec`. The key in the output dict must become `"quest_definitions"` so `WorldSpec.model_validate()` accepts it.
- `WorldTemplateSpec.quests` field itself stays as `list[dict]` (out of scope for this ticket) but the output key in `expanded_data` must be `"quest_definitions"` — OR rely on the migration validator.
- Since the migration validator handles `quests` → `quest_definitions`, leaving `"quests"` in the expanded dict is safe. But cleaner to rename the key to `"quest_definitions"` in recipe.py output.

## Step 6: Update `data/worlds/sandbox_world/world.yaml`
- Rename `quests: []` → `quest_definitions: []` (the migration alias handles the old key, but updating the canonical data file is correct)

## Step 7: Tests
- Create `tests/unit/worldbuilding/test_quest_definition.py`
