# Phase 27 Implementation Plan

## Goal Description
Prove that real `data/content/world_modules` and `data/content/world_compositions` are executable.

## Proposed Changes

### Integration Tests
- **`tests/integration/worldassembly/test_real_content_world_modules.py`**:
  - Test loading all real module files from `data/content/world_modules`.
  - Validate schema conformance of each module.
  - Normalize modules and assert no count map data loss.
  - Resolve contributions for the module matrix (`frontier_village_core`, `wolf_den_near_forest`, `goblin_camp_conflict`, `old_mine_resource_loop`, `bandit_road_trade_pressure`, `moon_cult_ruins`, `undead_battlefield`).
  - Verify that the reference graph handles references between modules correctly.
- **`tests/integration/worldassembly/test_real_content_world_compositions.py`**:
  - Load real composition YAML files.
  - Verify both `modules` shorthand and `module_refs` load referenced modules from the canonical repository.
  - Assemble the merged world contribution and build the compile context.
  - Verify deterministic compilation output, fingerprint stability, and provenance sidecar data (ensuring provenance registers module source, archetype source, population recipe source, etc.).
