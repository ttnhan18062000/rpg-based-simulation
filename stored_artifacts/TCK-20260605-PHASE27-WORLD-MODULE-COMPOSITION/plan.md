---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION
artifact_type: plan
tags: [phase27, world, module, composition]
---

# Plan - Phase 27

We will implement `ResolvedModuleContribution` and `WorldCompositionNormalizer` to solve Task 27.1, 27.2, and 27.3.

1. **Task 27.1**: Add `ResolvedModuleContribution`:
   - Create the Pydantic model `ResolvedModuleContribution` with fields:
     - `regions`
     - `factions`
     - `population_refs`
     - `resolved_population_specs`
     - `resource_refs`
     - `building_refs`
     - `service_refs`
     - `relationship_refs`
     - `biome_refs`
     - `ecology_refs`
   - Normalize module v1/v2 data into this format.
   - Refactor `WorldAssemblyResolver` to use component resolvers (e.g. `PopulationRecipeResolver` from Phase 25/24).
   - Ensure duplicate region collision still fails.

2. **Task 27.2**: Add `WorldCompositionNormalizer` and `NormalizedWorldComposition`:
   - Create Pydantic schema for `NormalizedWorldComposition`.
   - Implement `WorldCompositionNormalizer` which takes either composition formats and converts them to `NormalizedWorldComposition`.
   - Ensure default perspectives are preserved.

3. **Task 27.3**: Keep provenance deterministic:
   - Ensure composition fingerprint is deterministic.
