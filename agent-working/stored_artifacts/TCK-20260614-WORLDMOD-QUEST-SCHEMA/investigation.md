# Investigation: TCK-20260614-WORLDMOD-QUEST-SCHEMA

## Current State

### `WorldSpec.quests` (line 108, `src/worldbuilding/schema.py`)
- Typed as `list[dict[str, Any]]` — completely untyped bag
- Used in the compiler (`src/worldbuilding/compiler.py`, line 311) with raw dict access: `.get("id")`, `.get("kind")`, `.get("reward")`, etc.
- Used in `WorldTemplateSpec.quests` (`src/worldbuilding/recipe.py`, line 101) — same untyped field, passed through to `expanded_data["quests"]`
- Used in `src/worldbuilding/cli.py` lines 349, 362 as `len(x.quests)` / `len(spec.quests)`

### Data files with `quests:` key
- `data/worlds/sandbox_world/world.yaml` line 53: `quests: []` (empty list — no legacy data to migrate)
- No other YAML files use `quests:` key

### `src/quests/` — READ ONLY context
- `src/quests/generator.py`: pure runtime quest generator using `QuestTemplate` dataclasses (different from authoring layer)
- `src/quests/service.py`: pure lifecycle service operating on `QuestState`
- `src/core/models/quests.py`: `QuestState`, `QuestKind`, `QuestStatus`, `RewardState` (runtime, do not touch)

### Key insight: compiler.py uses `spec.quests` as runtime runtime initialization dicts
- The compiler builds `QuestState` objects from the `quests: list[dict]` in `WorldSpec`
- This is the LEGACY path — the new `QuestDefinition` is authoring schema, not runtime initialization
- The compiler's quest loop at line 311 will need to be updated to iterate over `spec.quest_definitions` instead
- But `QuestDefinition` fields differ from the old dict keys (`kind`, `goal_value`, `reward`, etc.) — the compiler uses old runtime quest fields
- Solution: update `spec.quests` → `spec.quest_definitions` in compiler, but the compiler logic itself (which builds QuestState from dicts) should now build from `QuestDefinition` objects
- Since `QuestDefinition` is authoring schema (not runtime activation), the compiler can simply skip the old runtime quest compilation or adapt it

### Migration decision
- Data file `quests: []` is empty → safe to rename without migration alias
- However, per ticket spec: "if any YAML uses the old `quests:` key, add migration alias"
- The sandbox_world/world.yaml uses `quests: []` — it has the old key
- Therefore: add `@model_validator(mode="before")` migration alias to handle `quests` → `quest_definitions`

## Architecture Notes
- `QuestDefinition` goes in `src/worldbuilding/schema.py` only (authoring layer)
- `src/quests/` untouched, `src/core/models/quests.py` untouched
- `src/worldbuilding/compiler.py`: update `spec.quests` references to `spec.quest_definitions`
- `src/worldbuilding/cli.py`: update `len(x.quests)` / `len(spec.quests)` to `quest_definitions`
- `src/worldbuilding/recipe.py`: `WorldTemplateSpec.quests` is a SEPARATE class — it stays untyped for now (out of scope); only `WorldSpec.quests` is renamed

## Compiler Impact
The compiler loop (lines 311-388) accesses old dict fields: `id`, `kind`, `goal_value`, `reward`, `name`, `metadata`, `target_region_id`, etc. These are NOT fields of `QuestDefinition`. After renaming `spec.quests` → `spec.quest_definitions`, the compiler loop body must be updated to read from `QuestDefinition` fields instead of raw dicts.

Since `QuestDefinition` is authoring schema (no `goal_value`, no `reward`, no runtime assignment), the compiler's old runtime quest-compilation logic is now vestigial. The safest approach for this ticket: update compiler to iterate `spec.quest_definitions` but skip building `QuestState` objects — or build minimal `QuestState` from authoring fields. Per ticket scope, the compiler change is a referential update only (so no silent breakage). The compiler loop will be updated to use `quest_definitions` entries with their typed fields.
