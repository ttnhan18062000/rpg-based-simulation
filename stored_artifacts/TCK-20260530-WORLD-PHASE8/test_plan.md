---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE8
artifact_type: test_plan
tags: [world, phase8]
---

# Test Plan: Simple Procedural Generation Foundation (Phase 8)

## Test Matrix

1. **RNG Determinism**:
   - Running the generator twice with the same seed and intent must yield byte-identical WorldSpec specs.
   - Different seeds must yield different layouts.

2. **Structural Integrity**:
   - Assert all generated region bounds reside completely inside map dimensions.
   - Assert building spawn coordinates and resource nodes reside strictly inside applicable regions.

3. **Compiler Compatibility**:
   - Assert that the procedurally generated `WorldSpec` successfully compiles into a running simulation `AuthoritativeState`.

## Execution
```bash
.venv/bin/pytest tests/unit/worldgeneration/test_generator.py -v
```
