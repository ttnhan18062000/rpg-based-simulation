---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDMOD-QUEST-MOD
artifact_type: plan
tags: [worldmodules, quest, assembly, merge]
---

# Plan — TCK-20260614-WORLDMOD-QUEST-MOD

## Steps

1. **src/worldmodules/schema.py**
   - Add `from src.worldbuilding.schema import QuestDefinition`
   - Add `quest_definitions: List[QuestDefinition] = Field(default_factory=list, ...)`

2. **src/worldmodules/normalizer.py**
   - Add `quest_definitions: Tuple[QuestDefinition, ...]` (or List) to `NormalizedWorldModule`
   - In `WorldModuleAuthoringNormalizer.normalize()`: pass `quest_definitions=tuple(spec.quest_definitions)`

3. **src/worldassembly/schema.py**
   - Add `from src.worldbuilding.schema import QuestDefinition`
   - Add `quest_definitions: List[QuestDefinition] = Field(default_factory=list)` to `ResolvedModuleContribution`

4. **src/worldassembly/resolver.py**
   - Add `AssemblyCollisionError(ValueError)` class
   - In `resolve_module_contribution()`: collect quest_definitions from normalized_module, set source_module via model_copy, return in ResolvedModuleContribution
   - In `assemble()`: accumulate quest defs in dict keyed by id; on duplicate raise AssemblyCollisionError; after loop set WorldSpec(..., quest_definitions=list(accumulated.values())); add ProvenanceRecord per quest def

5. **tests/unit/worldassembly/test_quest_merge.py**
   - 4 unit tests as specified

6. **docs/parity_ledger/substrate.yaml**
   - Add SUBSTRATE-NEW-008 for quest module merge
