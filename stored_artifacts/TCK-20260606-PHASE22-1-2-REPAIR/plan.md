---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE22-1-2-REPAIR
artifact_type: plan
tags: [phase22, repair]
---

# Implementation Plan - Phase 22.1 & 22.2 Schema and Normalization Repair

## Proposed Changes

### Tests

#### [MODIFY] [test_assembly.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldassembly/test_assembly.py)

- Add a fixture `real_content_paths` that uses the canonical path config to return paths to real content files.
- Add test case `test_unknown_field_in_real_world_module_fails` that:
  - Loads `frontier_village_core.yaml`.
  - Injects an unknown top-level field `unknown_field_xyz: 123`.
  - Asserts that initializing `WorldModuleSpec` raises validation error.
  - Ensures the error message (or contextual wrapping) includes file/family/record ID.
- Add test case `test_unknown_field_in_real_composition_fails` that:
  - Loads `frontier_living_world.yaml`.
  - Injects an unknown top-level field `unknown_field_xyz: 123`.
  - Asserts that initializing `WorldCompositionSpec` raises validation error.
  - Ensures the error message includes the file/family/record details.
- Add test case `test_real_composition_normalization_preserves_perspectives` that:
  - Loads `frontier_living_world.yaml`.
  - Normalizes it using `WorldCompositionNormalizer.normalize`.
  - Asserts that `default_perspectives` is correctly populated with `["hero_guild_perspective", "wild_beast_pack_perspective", "goblin_warband_perspective"]`.
  - Asserts shorthand `modules` are converted to `module_refs` correctly.
  - Asserts mixed declaration throws `ValueError`.
  - Asserts fingerprinting is deterministic.

## Verification Plan

### Automated Tests
- Run assembly unit tests:
  ```bash
  pytest tests/unit/worldassembly/test_assembly.py
  ```
