---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260603-PHASE17-GENERATOR-REGATING
artifact_type: plan
tags: [phase17, generator, regating]
---

# Implementation Plan - Phase 17 (Procedural Generator Re-gating)

This plan details the changes necessary to integrate the procedural generator with the unified catalog and resolved compile context.

## Proposed Changes

### Procedural Generator
#### [MODIFY] [generator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldgeneration/generator.py)
* Refactor building types to use valid catalog definitions (`["shop", "blacksmith", "inn"]` instead of `"tavern"`).
* Refactor resource types to use valid catalog definitions:
  * Select from catalog resources (e.g. `wood`, `iron_ore`).
* Refactor factions and roles to use valid catalog definitions:
  * Citizens/workers should belong to a defender faction (e.g. `"town_council"` or `"hero_guild"`, defaulting to `"town_council"`).
  * Hostiles should belong to an invader faction (e.g. `"goblin_warband"` or `"bandit_company"`, defaulting to `"goblin_warband"`).
* Compile `validation_report` using `WorldValidator().validate(...)` (saving issues in dictionary form) and pass it to `ResolvedWorldBundle`.
* Provenance record generation should match element types/attributes from catalog values.
* Avoid fake created_at timestamps. Allow `created_at` in `ProvenanceManifest` to carry the current time, but ensure `content_fingerprint` or other fields are used for determinism checks.

### Testing & Verification Suite
#### [MODIFY] [test_generator.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldgeneration/test_generator.py)
* Update `test_procedural_generator_determinism`:
  * Assert `content_fingerprint` equality for identical seeds.
  * Compare specific deterministic keys of the provenance manifest model dump instead of doing byte-identical string comparison on full model dumps including the dynamic `created_at` timestamp.
* Add a catalog-backed runtime simulation smoke test `test_generated_world_catalog_smoke_simulation`:
  * Load production catalog repository.
  * Seed runtime registries from catalog.
  * Generate a procedural world spec using `WorldProceduralGenerator`.
  * Compile it with `WorldCompiler` using the bundle's `compile_context`.
  * Run a 5-tick simulation and assert no hard-law violations or lookup errors.
