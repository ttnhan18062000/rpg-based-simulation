---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE3
artifact_type: plan
tags: [world, phase3]
---

# Phase 3 Execution Plan

We will implement the profile consumer bridge systematically:

1. **Task 3.1**: Define the internal compile-ready models in `src/worldassembly/models.py`:
   - `ResolvedEntityProfile`
   - `ResolvedBuildingProfile`
   - `ResolvedResourceProfile`
   - `ResolvedFactionEconomyProfile`
2. **Task 3.2**: Create `CompileContext` under `src/worldassembly/context.py` to hold resolved profiles by category (e.g. keying by pop index, resource node types, etc.).
3. **Task 3.3**: Implement `CompileProfileResolver` under `src/worldassembly/resolver.py` that merges explicit overrides, default roles/factions, and global default configs.
4. **Task 3.4**: Refactor the compilation loop inside `WorldCompiler.compile` in `src/worldbuilding/compiler.py` to override defaults (entity hp/atk/readiness, building hp, node ticks, faction gold) with context values when available.
5. **Task 3.5**: Write focused tests in `tests/unit/worldassembly/` and verify that the test suite passes seamlessly.
