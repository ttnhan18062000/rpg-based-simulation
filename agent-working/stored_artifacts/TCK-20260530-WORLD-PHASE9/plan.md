---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE9
artifact_type: plan
tags: [world, phase9]
---

# Implementation Plan - Compiler Integration Hardening (Phase 9)

Reduce hardcoded parameters inside the `WorldCompiler` by integrating `CompileContext` dynamic lookups. Ensure full backward compatibility.

## User Review Required

> [!IMPORTANT]
> - `CompileContext` remains entirely optional for the compiler. If omitted, the compilation path falls back to the existing legacy defaults.
> - Dynamic compilation overrides stats for entities, required harvest ticks for resources, durability for buildings, and starting vault gold for factions.

## Proposed Changes

### Worldbuilding Compiler Component

#### [MODIFY] [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py)
- Update `WorldCompiler.compile` method signature to support `context: Optional[CompileContext] = None`.
- Dynamically fetch HP, Max HP, ATK, Def, Attack Range, and Readiness from `context.entities[pop_key]` if context is provided and contains the key.
- Dynamically fetch Resource required ticks from `context.resources[res_spec.id]` if context is provided.
- Dynamically fetch Building HP and Max HP from `context.buildings[bld_spec.id]` if context is provided.
- Dynamically fetch Faction starting gold from `context.factions[f_spec.id]` if context is provided.
- Ensure 100% backward compatibility for all fallback cases.

## Verification Plan

### Automated Tests
- Run existing compiler tests:
  ```bash
  .venv/bin/pytest tests/unit/ -k compiler
  ```
- Implement new context-aware compiler tests in `tests/unit/worldbuilding/test_compiler_context.py` covering:
  - Compiling without context (confirming match with legacy defaults and hashes).
  - Compiling with partially populated context.
  - Compiling with fully populated context (verifying exact overrides are applied to compiled entities, resources, buildings, and factions).
  - State hash stability validation.
