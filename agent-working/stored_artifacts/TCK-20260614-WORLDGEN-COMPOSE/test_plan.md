---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDGEN-COMPOSE
artifact_type: test_plan
tags: [worldgen, procedural, composition, generator]
---

# Test Plan — TCK-20260614-WORLDGEN-COMPOSE

## Unit Tests: `tests/unit/worldgeneration/test_composition_generator.py`

### Test 1: Determinism
Same intent + seed → identical YAML output across two calls.

### Test 2: Settlement style none
`settlement_style="none"` → no settlement-type module in output module_refs.

### Test 3: Dependency auto-inclusion
If a selected module has `requires: ["dep_module_id"]`, that dependency appears in output
even if it didn't score high enough on its own.

### Test 4: Output path pattern
Returned path matches `generated_{settlement_style}_{int(danger_level)}_{seed}.yaml`
pattern in the generated/ directory.

### Test 5: Conflict detection
Two modules with same `provides` string → raises `GenerationCompositionError` naming both module IDs.

### Test 6: Valid WorldCompositionSpec output
Output YAML parses cleanly via `WorldCompositionSpec.model_validate()`.

## Integration Test
- `test_generated_composition_assembles` in `tests/integration/worldassembly/`
- Load real module repo, generate composition, then assert `WorldCompositionSpec.model_validate(yaml)` passes
- (Full assembly via WorldAssemblyResolver deferred to TCK-20260614-WORLDGEN-E2E-SMOKE)

## Test Strategy
- Use stub WorldModuleRepository subclass to avoid file I/O
- Clean up generated test files in tmp_path fixture
- All stubs have deterministic module_id ordering
