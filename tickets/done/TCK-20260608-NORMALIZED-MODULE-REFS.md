# TCK-20260608-NORMALIZED-MODULE-REFS

## Title
Rename NormalizedWorldModule biomes/ecologies/populations/relationships to *_refs fields

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
NormalizedWorldModule currently exposes biomes, ecologies, populations, and relationships as Tuple[str, ...] fields — correctly typed but still named like raw authoring fields. This naming ambiguity risks future code conflating normalized ref IDs with raw YAML dict structures. This task renames those four fields to biome_refs, ecology_refs, population_refs, and relationship_refs. Compatibility properties for the old names may be added temporarily, but all internal consumers — WorldModuleAuthoringNormalizer, WorldAssemblyResolver, ContentReferenceGraph, and all tests — must migrate to the *_refs names.

## Scope
- Rename NormalizedWorldModule fields: biomes → biome_refs, ecologies → ecology_refs, populations → population_refs, relationships → relationship_refs
- Update WorldModuleAuthoringNormalizer.normalize() to assign *_refs field names
- Update ContentReferenceGraph.add_module_edges() to consume *_refs fields
- Update WorldAssemblyResolver to use *_refs field names wherever it reads from NormalizedWorldModule
- Update tests/unit/content/test_reference_graph.py to construct NormalizedWorldModule with *_refs fields
- Update tests/unit/worldmodules/test_modules.py to use *_refs field names
- Update tests/integration/worldassembly/* where NormalizedWorldModule is constructed or inspected
- Optionally add compatibility properties (biomes, ecologies, etc.) pointing to *_refs

## Out of Scope
- Renaming resources, buildings, services count map fields (out of scope per source doc)
- Changing the normalizer conversion logic
- Modifying WorldModuleSpec (raw authoring schema)

## Acceptance Criteria
- [ ] NormalizedWorldModule has biome_refs field of type Tuple[str, ...]
- [ ] NormalizedWorldModule has ecology_refs field of type Tuple[str, ...]
- [ ] NormalizedWorldModule has population_refs field of type Tuple[str, ...]
- [ ] NormalizedWorldModule has relationship_refs field of type Tuple[str, ...]
- [ ] No production code constructs or reads the old field names (biomes, ecologies, populations, relationships) without going through a compatibility shim
- [ ] ContentReferenceGraph.add_module_edges consumes biome_refs/ecology_refs/population_refs/relationship_refs
- [ ] WorldAssemblyResolver uses population_refs and relationship_refs instead of raw field names
- [ ] All existing worldmodules and reference_graph tests pass with renamed fields

## Related Tickets
- TCK-20260607-NORMALIZEDMODULE-TYPING (predecessor — typed the fields as Tuple[str, ...]; this ticket renames them)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldmodules/normalizer.py
- src/content/reference_graph.py
- src/worldassembly/resolver.py
- tests/unit/worldmodules/test_modules.py
- tests/unit/content/test_reference_graph.py
- tests/integration/worldassembly/

## Assumptions / Open Questions
- All real YAML modules use plain string lists — no dict-with-id format in production data (confirmed by TCK-20260607-NORMALIZEDMODULE-TYPING implementation notes)
- Compatibility shims are acceptable temporarily but must not become permanent

## Implementation Notes
Renamed four NormalizedWorldModule dataclass fields from biomes/ecologies/populations/relationships to biome_refs/ecology_refs/population_refs/relationship_refs. Updated all internal consumers (normalizer, reference_graph, resolver) and all tests. WorldModuleSpec (raw authoring schema) field names were left unchanged as out of scope. Pre-existing failures in test_real_content_world_compositions.py (moon_cult_ruins) and test_generator.py are unrelated to this change (confirmed via git stash verification).

## Test Summary
31 passed — tests/unit/worldmodules/test_modules.py, tests/unit/content/test_reference_graph.py, tests/integration/worldassembly/test_real_content_world_modules.py

## Files Changed
- src/worldmodules/normalizer.py (field rename + normalize() assignments)
- src/content/reference_graph.py (add_module_edges field accesses)
- src/worldassembly/resolver.py (4 field accesses at lines 699, 705, 711, 727)
- tests/unit/content/test_reference_graph.py (kwargs in _make_normalized_module)
- tests/unit/worldmodules/test_modules.py (12 field access occurrences)
- tests/integration/worldassembly/test_real_content_world_modules.py (2 occurrences)

## Completion Summary
All four NormalizedWorldModule fields renamed to *_refs convention. No production code reads old names. All tests pass.
