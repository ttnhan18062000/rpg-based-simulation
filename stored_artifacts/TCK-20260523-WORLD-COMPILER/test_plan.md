---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-COMPILER
artifact_type: test_plan
tags: [world, compiler]
---

# Test Plan: World Compiler Implementation (Milestone 70)

We will implement three distinct test suites covering unit, integration, and certification aspects of the World Compiler.

## 1. Unit Tests

File: `tests/unit/worldbuilding/test_world_compiler.py`

### Test Cases
- **Minimal World Compilation**: Verify that a very simple, correct `WorldSpec` compiles without errors, generating a valid `AuthoritativeState`.
- **Faction & Role Mapping**: Verify that entities created have correct enums mapped for `Faction` and `EntityRole` based on text fields in the specification.
- **Topology Bounds Enforcement**: Verify that resource nodes and buildings are placed within the bounds of the map topology and their respective regions.
- **Failed Compilation on Invalid World**: Verify that calling the compiler with a structurally invalid world spec (e.g. failing validation) immediately raises a compilation exception and does not return a partial state.

## 2. Integration Tests

File: `tests/integration/worldbuilding/test_world_compile_to_state.py`

### Test Cases
- **Ticks Stability Certification**: Compile a world, pass it to the simulation engine, and verify that the simulation runs for 10 consecutive ticks without immediate structural failure, crash, or invariance violations.
- **Quest Referential Checks**: Verify that quests in the spec containing unmatched region or faction references correctly flag warnings in the compiler report, but do not crash compilation.

## 3. Certification & Determinism Tests

File: `tests/certification/test_world_compile_determinism.py`

### Test Cases
- **Seed-Based State Determinism**: Verify that compiling the same world spec twice with the exact same seed produces matching initial state hashes (`state_hash`) and identical entity coordinates.
- **Seed-Based Placement Variation**: Verify that compiling the same world spec with two different seeds produces different spatial coordinates for spawned entities/resources, reflecting procedural layout variability.
- **Compile Report Verification**: Verify that a correct `world_compile_report.json` is saved at the output path and contains all required metrics (world_id, seed, entity_count, region_count, resource_node_count, building_count, quest_count, compile_duration_ms, state_hash).
