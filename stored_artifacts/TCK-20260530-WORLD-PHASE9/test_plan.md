---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE9
artifact_type: test_plan
tags: [world, phase9]
---

# Test Plan - Compiler Integration Hardening (Phase 9)

Verify that both the context-backed path and the legacy fallback compile path are fully functional, deterministic, and safe.

## Scenarios to Test

1. **Legacy No-Context Compilation**:
   - Call `WorldCompiler.compile` without passing any `context` object.
   - Assert all compiled entity stats, resource ticks, building HPs, and faction starting gold match the old hardcoded defaults perfectly.
   - Verify state hashes match existing baselines exactly.

2. **Fully Populated Context Compilation**:
   - Create a dummy `CompileContext` and register custom entity, resource, building, and faction profiles.
   - Call `WorldCompiler.compile` passing the context.
   - Assert every entity, resource, building, and faction is compiled using the overridden context parameters.

3. **Partially Populated Context Compilation**:
   - Register only some of the elements in the context (e.g. only resources, or only a single entity population).
   - Assert that specified items use context values and unspecified ones fall back to legacy defaults gracefully.

4. **RNG determinism and state hash stability**:
   - Compiling the same inputs twice (with/without context) must yield exactly byte-identical outcomes and matching hashes.
