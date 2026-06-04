# Phase 27 Investigation

## Current Code Analysis
1. **World Modules**:
   - Located in `data/content/world_modules/` as YAML files.
   - Let's check which loaders exist. `src/worldassembly/` contains models and resolver logic.
   - Let's locate the module loader/normalizer.
   - Normalizer class: `WorldModuleAuthoringNormalizer` (or similar) from Phase 22.
2. **World Compositions**:
   - Located in `data/content/world_compositions/` as YAML files.
   - Normalizer class: `WorldCompositionNormalizer` (or similar).

Let's locate the files in `src/worldassembly/` using `list_dir`.
