---
ticket_id: TCK-20260614-WORLDMOD-PACKS
phase: test_plan
---

# Test Plan: Content Pack Dependency Validation at Assembly Time

## Unit Tests — `tests/unit/worldassembly/test_pack_validation.py`

### Test 1: `test_disabled_pack_raises_assembly_pack_error`
- **Setup:** Build a minimal `WorldCompositionSpec` with `pack_refs: ["frontier_extended_pack"]`. Mock the YAML load to return a manifest with `enabled: False`.
- **Assert:** `assemble()` raises `AssemblyPackError` with `"frontier_extended_pack"` in the message.
- **Covers:** disabled pack gate.

### Test 2: `test_missing_pack_raises_assembly_pack_error`
- **Setup:** Build a `WorldCompositionSpec` with `pack_refs: ["nonexistent_pack"]`. Mock `open()` to raise `FileNotFoundError`.
- **Assert:** `assemble()` raises `AssemblyPackError` with `"nonexistent_pack"` in the message.
- **Covers:** missing manifest gate.

### Test 3: `test_unsatisfied_dependency_raises_assembly_pack_error`
- **Setup:** Build a `WorldCompositionSpec` with `pack_refs: ["swamp_border_pack"]`. Mock the pack's manifest to have `dependencies: ["base_world_pack"]` and mock the dependency's manifest to have `enabled: False`.
- **Assert:** `assemble()` raises `AssemblyPackError` with `"base_world_pack"` in the message.
- **Covers:** dependency disabled gate.

### Test 4: `test_empty_pack_refs_passes_without_error`
- **Setup:** Build a `WorldCompositionSpec` with `pack_refs: []` (or omitting the field).
- **Assert:** No `AssemblyPackError` is raised during pack validation (the rest of assembly is mocked out).
- **Covers:** no-breaking-change guarantee for compositions without pack_refs.

## Integration Tests — `tests/integration/worldassembly/test_real_content_world_compositions.py`

### Test 5: `test_pack_refs_disabled_pack_raises_at_assembly`
- **Setup:** Create a `WorldCompositionSpec` with `pack_refs: ["frontier_extended_pack"]`. Mock the pack YAML to return `enabled: False`.
- **Assert:** `resolver.assemble(spec)` raises `AssemblyPackError` with `"frontier_extended_pack"` in the message.
- **Covers:** integration of pack validation in the full resolver pipeline.

## Regression Tests to Run

- `tests/unit/worldassembly/test_assembly.py` — existing assembly unit tests must still pass.
- `tests/unit/worldassembly/test_resolver.py` — resolver unit tests must still pass.
- `tests/integration/worldassembly/test_real_content_world_compositions.py` — all existing integration tests must still pass.

## Acceptance Coverage Matrix

| Criterion | Test |
|---|---|
| `pack_refs` field added to spec | Test 1-4 (field used) |
| Disabled pack raises AssemblyPackError with pack_id | Test 1 |
| Missing manifest raises AssemblyPackError with pack_id | Test 2 |
| Unsatisfied dependency raises AssemblyPackError naming dep | Test 3 |
| Empty pack_refs passes unconditionally | Test 4 |
| catalog_refs unchanged | All existing tests pass |
| Integration pipeline wires correctly | Test 5 |
