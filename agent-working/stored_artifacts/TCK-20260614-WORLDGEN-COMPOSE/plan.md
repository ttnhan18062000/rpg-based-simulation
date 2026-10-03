---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDGEN-COMPOSE
artifact_type: plan
tags: [worldgen, procedural, composition, generator]
---

# Plan — TCK-20260614-WORLDGEN-COMPOSE

## Implementation Steps

### Step 1: generator.py changes
- Add `GenerationCompositionError(ValueError)` exception class at top of file
- Add `ProceduralCompositionGenerator` class with:
  - `BUDGET = 6` class constant
  - `generate(intent, module_repo) -> Path` method
  - Selection logic: terrain first, settlement conditional, budget fill, dependency resolution
  - Conflict check on `provides` strings (two modules with same provide = conflict)
  - Build WorldCompositionSpec with required fields: schema_version, world_id, name
  - Write YAML to data/content/world_compositions/generated/{world_id}.yaml

### Step 2: cli.py changes
- Add `handle_generate(args) -> int` function
- Add `generate` subparser with --danger-level, --settlement-style, --seed, --terrain-style, --resource-density, --population-scale args
- Wire into main() dispatch

### Step 3: Tests
- `tests/unit/worldgeneration/test_composition_generator.py`
  - Use stub WorldModuleRepository (no file I/O)
  - Test: determinism, settlement_style=none, dependency inclusion, output path pattern, conflict detection

### Step 4: Parity ledger
- Add SUBSTRATE-NEW-010 entry to docs/parity_ledger/substrate.yaml

## Key Constraints
- WorldCompositionSpec requires: schema_version="worldcomposition.v1", world_id, name
- module_refs are ModuleRefSpec instances with module_id and order
- Dependency resolution is BFS (avoid infinite loops via visited set)
- Sort is deterministic: (-score, module_id) for tie-breaking
- Output dir created with parents=True, exist_ok=True
