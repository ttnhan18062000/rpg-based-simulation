---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-QUEST-SCHEMA
phase: open
date: 2026-06-14
tags: [worldmodules, quest, schema, foundation]
---

# TCK-20260614-WORLDMOD-QUEST-SCHEMA

## Title
QuestDefinition authoring schema as world-level foundation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`WorldSpec.quests` (line 108, `src/worldbuilding/schema.py`) is `list[dict[str, Any]]` — an untyped bag. The runtime quest system (`src/quests/`) generates quests procedurally at Guild buildings during simulation — that is a separate runtime concern. This ticket adds a typed `QuestDefinition` authoring schema at the world layer: a structural record that modules and compositions can contribute, and that the procedural generator can seed from. It is not a runtime quest — it is the authoring blueprint.

## Scope
- Define `QuestDefinition` frozen Pydantic model in `src/worldbuilding/schema.py`:
  - `id: str` — unique identifier (collision rules same as other world IDs)
  - `type: Literal["escort", "hunt", "fetch", "explore", "defend", "investigate"]`
  - `required_participant_tags: List[str]` — entity tags that must exist in world (e.g. `["hostile", "humanoid"]`)
  - `required_location_tags: List[str]` — region/biome tags required (e.g. `["wilderness", "dungeon"]`)
  - `reward_budget: int = 100` — relative reward weight for downstream generation
  - `procedural_hints: Dict[str, Any] = {}` — open-ended dict for procedural signals (difficulty, escalation, etc.)
  - `tags: List[str] = []` — freeform for filtering and module scoring
  - `source_module: Optional[str] = None` — set by assembly resolver, not authored
- Replace `WorldSpec.quests: list[dict[str, Any]]` with `quest_definitions: List[QuestDefinition] = []`
- No runtime behavior — `QuestDefinition` is static authoring data consumed by the procedural layer
- Do NOT touch `src/quests/` runtime system

## Out of Scope
- Quest runtime execution, FSM, or reward generation (`src/quests/` unchanged)
- Module quest contribution (TCK-20260614-WORLDMOD-QUEST-MOD)
- Linking `QuestDefinition` to runtime `QuestState` (future work)

## Acceptance Criteria
- `QuestDefinition` is a frozen Pydantic model with all listed fields
- `WorldSpec.quest_definitions` serializes/deserializes correctly
- A hand-authored YAML WorldSpec with `quest_definitions` containing one or more entries loads without error
- Invalid `type` value raises validation error
- `WorldSpec.quests` (old untyped field) is removed or aliased — no silent data loss on existing YAML with the old field
- `src/quests/` files are unchanged

## Related Tickets
- TCK-20260614-WORLDMOD-QUEST-MOD (depends on this)
- TCK-20260614-WORLDGEN-COMPOSE (procedural generator uses quest_definitions for seeding)

## Related Docs
- `docs/simulation/quest_contract.md` — runtime quest system (do not conflict)
- `docs/world/compiler_contract.md`

## Related Code Areas
- `src/worldbuilding/schema.py` — WorldSpec (L108), new QuestDefinition class
- `src/quests/generator.py`, `src/quests/service.py`, `src/quests/templates.py` — READ ONLY for context; do not modify
- `src/core/models/quests.py` — QuestState, QuestKind (READ ONLY; different layer)

## Assumptions / Open Questions
- `WorldSpec.quests` old field: if any existing YAML files use it, a migration alias or validator is needed. Check all files in `data/worlds/` for existing `quests:` keys before removing the field.

## Test Summary
- Unit: `tests/unit/worldbuilding/test_quest_definition.py` — valid definition loads, invalid type raises, source_module not authored (None), WorldSpec round-trip with quest_definitions
- Check existing world YAML files for `quests:` field presence before removal

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
