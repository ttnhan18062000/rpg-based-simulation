---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-QUEST-MOD
phase: done
date: 2026-06-14
tags: [worldmodules, quest, assembly, merge]
---

# TCK-20260614-WORLDMOD-QUEST-MOD

## Title
Module quest contribution and assembly merge

## Status
DONE

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

## Related Stored Artifacts
- `staging_artifacts/TCK-20260614-WORLDMOD-QUEST-MOD/`

## Related Code Areas
- `src/worldmodules/schema.py` — WorldModuleSpec (add quest_definitions field)
- `src/worldmodules/normalizer.py` — NormalizedWorldModule (add quest_definitions field)
- `src/worldassembly/schema.py` — ResolvedModuleContribution (add quest_definitions field)
- `src/worldassembly/resolver.py` — AssemblyCollisionError, resolve_module_contribution(), merge logic
- `src/worldbuilding/schema.py` — QuestDefinition (already exists, read-only)

## Assumptions / Open Questions
- AssemblyCollisionError does not exist yet; it is a new ValueError subclass introduced here.
- NormalizedWorldModule is a frozen dataclass; quest_definitions stored as Tuple[QuestDefinition, ...].
- Provenance: per-quest-definition ProvenanceRecord with recipe_type="quest_definition".

## Implementation Notes
- AssemblyCollisionError(ValueError) introduced alongside AssemblyPackError in resolver.py.
- NormalizedWorldModule carries quest_definitions as Tuple[QuestDefinition, ...] (frozen dataclass pattern).
- resolve_module_contribution() step 9: stamps source_module via model_copy(update={...}) since QuestDefinition is frozen.
- assemble() accumulates quest_defs dict keyed by id; raises AssemblyCollisionError on collision naming both modules.
- ProvenanceRecord per quest with recipe_type="quest_definition", element_type="quest_definition".
- Existing integration test stub for NormalizedWorldModule updated with quest_definitions=().

## Test Summary
- Unit: `tests/unit/worldassembly/test_quest_merge.py` — single module with quests, collision detection, source_module set, no-quest module unaffected

## Files Changed
- src/worldmodules/schema.py — added QuestDefinition import + quest_definitions field to WorldModuleSpec
- src/worldmodules/normalizer.py — added QuestDefinition import + quest_definitions field to NormalizedWorldModule + normalize()
- src/worldassembly/schema.py — added QuestDefinition import + quest_definitions field to ResolvedModuleContribution
- src/worldassembly/resolver.py — added QuestDefinition import, AssemblyCollisionError class, quest collection in resolve_module_contribution(), quest merge loop + provenance in assemble(), quest_definitions in WorldSpec construction
- tests/unit/worldassembly/test_quest_merge.py — 4 new unit tests (created)
- tests/integration/worldassembly/test_real_content_world_compositions.py — added quest_definitions=() to NormalizedWorldModule stub
- docs/parity_ledger/substrate.yaml — added SUBSTRATE-NEW-009

## Completion Summary
Added quest_definitions to WorldModuleSpec, NormalizedWorldModule, and ResolvedModuleContribution. Wired collection and source_module stamping into resolve_module_contribution(). Added collision-checked merge loop in assemble() with AssemblyCollisionError and per-quest ProvenanceRecord. WorldSpec.quest_definitions populated from merged contributions. 4 new unit tests green. Parity ledger updated (SUBSTRATE-NEW-009).
