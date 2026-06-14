---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-QUEST-MOD
phase: open
date: 2026-06-14
tags: [worldmodules, quest, assembly, merge]
---

# TCK-20260614-WORLDMOD-QUEST-MOD

## Title
Module quest contribution and assembly merge

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
After `QuestDefinition` exists in the world schema (TCK-20260614-WORLDMOD-QUEST-SCHEMA), this ticket wires it into the module and assembly pipeline. Modules can declare quest blueprints they contribute; the assembly resolver merges them with the same ID-collision rules used for all other world elements.

## Scope
- Add `quest_definitions: List[QuestDefinition] = []` to `WorldModuleSpec` in `src/worldmodules/schema.py`
- In `WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py`):
  - Collect `QuestDefinition` records from each module
  - Apply `source_module = module.module_id` to each record
  - Merge into accumulated quest list; raise `AssemblyCollisionError` on duplicate `id` (consistent with region/entity collision policy)
- Populate `WorldSpec.quest_definitions` from merged module contributions after assembly completes
- Provenance sidecar records quest definition origins

## Out of Scope
- Runtime quest execution or Guild integration
- Scenario-level quest filtering
- Parameter-driven quest count templating (can be added later when param engine is complete)

## Acceptance Criteria
- A module declaring `quest_definitions: [{id: mine_fetch_ore, type: fetch, ...}]` produces a compiled `WorldSpec` with that definition present
- Two modules declaring quest definitions with the same `id` fail assembly with collision error naming the conflicting module IDs
- `source_module` field is set correctly from the contributing module's `module_id`
- Quest definitions appear in `ProvenanceManifest` records with `recipe_type="quest_definition"`
- Modules with no `quest_definitions` field are unaffected

## Related Tickets
- TCK-20260614-WORLDMOD-QUEST-SCHEMA (prerequisite)
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260614-WORLDDAT-NEWMODS (validates — ruins_mystery_quest module contributes quests)

## Related Docs
- `docs/world/assembly_contract.md`
- `docs/world/modules_contract.md`

## Related Code Areas
- `src/worldmodules/schema.py` — WorldModuleSpec (add quest_definitions field)
- `src/worldassembly/resolver.py` — resolve_module_contribution(), merge logic
- `src/worldassembly/schema.py` — ResolvedWorldBundle / WorldSpec output

## Test Summary
- Unit: `tests/unit/worldassembly/test_quest_merge.py` — single module with quests, collision detection, source_module set, no-quest module unaffected
- Integration: add `ruins_mystery_quest` module to a test composition after TCK-20260614-WORLDDAT-NEWMODS

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
