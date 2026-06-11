---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260608-REAL-MODULE-SNAPSHOT
phase: done
date: 2026-06-08
tags: [real, module, snapshot]
---

# TCK-20260608-REAL-MODULE-SNAPSHOT

## Title
Add integration snapshot test using a real world module YAML for normalized contract proof

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
All existing normalized module tests use synthetic in-memory module objects. While useful for unit testing, this leaves a gap: there is no proof that the normalization pipeline produces the correct typed output when given an actual YAML file from data/content/world_modules. This task adds one integration snapshot test that loads a real module (e.g., frontier_village_core) through WorldModuleRepository and WorldModuleAuthoringNormalizer, then asserts the normalized shape — module_id, module_type, biome_refs, ecology_refs, population_refs, relationship_refs, and count maps for resources, buildings, services.

## Scope
- Add tests/integration/worldassembly/test_real_module_normalized_snapshot.py
- Load a real module from data/content/world_modules via WorldModuleRepository().load_all() and get the frontier_village_core module (or equivalent real module)
- Pass the loaded module through WorldModuleAuthoringNormalizer.normalize()
- Assert normalized snapshot: module_id, module_type, biome_refs (tuple of strings), ecology_refs, population_refs, relationship_refs, resources dict, buildings dict, services dict
- Assert no raw dicts remain in any *_refs field
- Assert test does not manually inject or construct a module object — must use the real repository

## Out of Scope
- Snapshotting the entire raw YAML file
- Testing normalizer error paths (covered in unit tests)
- Adding snapshot tests for all modules — one real-module proof is sufficient for this ticket

## Acceptance Criteria
- [ ] tests/integration/worldassembly/test_real_module_normalized_snapshot.py exists and passes
- [ ] Test loads module from real data/content/world_modules directory, not from a synthetic object
- [ ] Test asserts biome_refs is a non-empty tuple of strings
- [ ] Test asserts ecology_refs, population_refs, relationship_refs are tuples of strings
- [ ] Test asserts resources, buildings, services are dicts mapping str → int
- [ ] Test asserts no element in any *_refs field is a dict
- [ ] Test does not use manually constructed NormalizedWorldModule

## Related Tickets
- TCK-20260608-NORMALIZED-MODULE-REFS (dependency — *_refs field names must be in place before this snapshot is written)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldmodules/normalizer.py
- tests/integration/worldassembly/test_real_module_normalized_snapshot.py
- data/content/world_modules/

## Assumptions / Open Questions
- frontier_village_core module exists in data/content/world_modules and has non-empty biome/ecology/population/relationship lists
- WorldModuleRepository has a load_all() and get_module() or equivalent interface to retrieve a specific module by ID

## Implementation Notes
Created tests/integration/worldassembly/test_real_module_normalized_snapshot.py loading frontier_village_core via WorldModuleRepository (no synthetic construction). frontier_village_core has biomes, ecologies, populations, buildings — all verified to normalize into the correct *_refs tuple/dict shapes. relationship_refs and resources are empty (module has none); this is valid and tested. The `test_snapshot_loaded_from_repository_not_synthetic` test verifies the module came from real YAML via schema_version and display_name fields that synthetic objects wouldn't carry.

## Test Summary
10 passed — tests/integration/worldassembly/test_real_module_normalized_snapshot.py

## Files Changed
- tests/integration/worldassembly/test_real_module_normalized_snapshot.py (new)

## Completion Summary
Integration snapshot test added. Proves the full repository→normalizer pipeline produces typed *_refs tuples and str→int count maps from a real YAML file.
