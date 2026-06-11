---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE5
artifact_type: plan
tags: [world, phase5]
---

# Phase 5 Execution Plan

We will implement the compositional world resolution systematically:

1. **Task 5.1**: Define the Pydantic schemas in `src/worldassembly/schema.py`:
   - `ModuleRefSpec` (referencing `module_id`, `enabled`, `order`, `parameters`, `namespace`)
   - `WorldCompositionSpec` (referencing `schema_version = worldcomposition.v1`, topology, catalog_refs, module_refs, global_parameters, generation_seed)
2. **Task 5.2**: Create the resolver in `src/worldassembly/resolver.py` representing `WorldAssemblyResolver`:
   - Resolve and sort module dependencies.
   - Inject parameters into modules recursively.
   - Merge module regions, populations, resources, and buildings.
   - Resolve profiles using `CompileProfileResolver` and register CompileContext.
   - Output `ResolvedWorldBundle` containing clean `WorldSpec` and sidecar `ProvenanceManifest`.
3. **Task 5.3**: Modify the `WorldRepository` loader in `src/worldbuilding/repository.py` to index `worldcomposition.v1` schema versions and support resolved folder redirects.
4. **Task 5.4**: Write unit tests in `tests/unit/worldassembly/test_assembly.py` and run the unit test suite.
