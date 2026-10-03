# Test Plan: TCK-20260614-WORLDMOD-QUEST-SCHEMA

## Test File
`tests/unit/worldbuilding/test_quest_definition.py`

## Test Cases

### 1. Valid QuestDefinition loads without error
- Construct a `QuestDefinition` with minimum required fields (`id`, `type`)
- Assert model instantiation succeeds and defaults are correct

### 2. All valid types accepted
- Test each of the 6 valid types: `escort`, `hunt`, `fetch`, `explore`, `defend`, `investigate`

### 3. Invalid `type` raises ValidationError
- Pass an invalid type string (e.g., `"raid"`)
- Assert `ValidationError` is raised

### 4. `source_module` defaults to None
- Create `QuestDefinition` without `source_module`
- Assert `source_module is None`

### 5. `QuestDefinition` is frozen (immutable)
- Attempt to assign to a field after construction
- Assert `ValidationError` or `TypeError` is raised

### 6. `WorldSpec` round-trip with `quest_definitions`
- Build a `WorldSpec` dict with `quest_definitions` containing one `QuestDefinition`
- Call `WorldSpec.model_validate(data)` and assert the field is populated

### 7. Migration alias: old `quests:` key round-trips to `quest_definitions`
- Build a `WorldSpec` dict using the old `quests` key (mimicking sandbox_world/world.yaml)
- Call `WorldSpec.model_validate(data)` and assert `.quest_definitions` is populated correctly

### 8. `WorldSpec.model_dump()` serializes `quest_definitions` correctly
- Build WorldSpec with a QuestDefinition entry
- Call `.model_dump()` and assert the output has `quest_definitions` key with correct data

## Run Command
```bash
python3 -m pytest tests/unit/worldbuilding/test_quest_definition.py tests/unit/worldbuilding/ -q --tb=short
```
