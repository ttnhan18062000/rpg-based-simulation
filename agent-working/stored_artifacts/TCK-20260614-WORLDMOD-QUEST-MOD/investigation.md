---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDMOD-QUEST-MOD
artifact_type: investigation
tags: [worldmodules, quest, assembly, merge]
---

# Investigation — TCK-20260614-WORLDMOD-QUEST-MOD

## Findings

### QuestDefinition (src/worldbuilding/schema.py)
- `QuestDefinition` is a frozen Pydantic model at line 94.
- Has fields: `id`, `type`, `required_participant_tags`, `required_location_tags`, `reward_budget`, `procedural_hints`, `tags`, `source_module` (Optional[str], set by assembler).
- `WorldSpec.quest_definitions: List[QuestDefinition]` already exists at line 135.

### WorldModuleSpec (src/worldmodules/schema.py)
- `quest_definitions` field is NOT present — must be added.
- Model is frozen (`ConfigDict(frozen=True, extra="forbid")`).

### NormalizedWorldModule (src/worldmodules/normalizer.py)
- Dataclass at line 18, frozen=True.
- Does NOT have `quest_definitions` — must be added.
- Pattern: structured fields directly from WorldModuleSpec.

### WorldAssemblyResolver (src/worldassembly/resolver.py)
- `resolve_module_contribution()` at line 707 — returns `ResolvedModuleContribution`.
- `ResolvedModuleContribution` (src/worldassembly/schema.py line 112) — does NOT have `quest_definitions` — must be added.
- `assemble()` iterates sorted_ids, calls `resolve_module_contribution()`, merges results into dicts.
- Collision check pattern: `raise ValueError(f"Duplicate ... collision '...' detected during assembly merge.")`
- `AssemblyCollisionError` does NOT exist — the existing collision pattern uses plain `ValueError`.
  - Decision: add `AssemblyCollisionError(ValueError)` to resolver.py alongside existing `AssemblyPackError`.
  - For quest merge, use `AssemblyCollisionError` per ticket spec; existing ValueError collisions are not touched.

### ProvenanceManifest / ProvenanceRecord
- ProvenanceRecord has `recipe_type` field (string).
- Pattern: per-element provenance record in `prov_records` dict keyed by element_id.
- Quest definitions will get `recipe_type="quest_definition"`, `element_type="quest_definition"`.

### WorldSpec.quest_definitions
- Already present in WorldSpec — needs to be populated in `assemble()` after the module loop.

## Provenance Decision
- ProvenanceManifest records per element ID — quest definitions will follow the same pattern as regions/resources/buildings.
- Each quest definition gets its own ProvenanceRecord with `recipe_type="quest_definition"`.

## Key Files
- `src/worldmodules/schema.py` — add `quest_definitions` field + import
- `src/worldmodules/normalizer.py` — add `quest_definitions` to NormalizedWorldModule + normalize in WorldModuleAuthoringNormalizer
- `src/worldassembly/schema.py` — add `quest_definitions` to ResolvedModuleContribution
- `src/worldassembly/resolver.py` — add AssemblyCollisionError, wire quest merge in assemble(), wire collection in resolve_module_contribution()
