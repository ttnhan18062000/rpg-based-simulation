---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260405-DOCS
artifact_type: plan
tags: [docs]
---

# Documentation Update Plan

## Goal
Update all `.md` files in `docs/` to reflect the current Aspect-Oriented Architecture (AOA).

## Proposed Changes
I will follow the `doc-coauthoring` workflow for each major document.

### 1. Foundational Architecture
- **`architecture.md`**: Update core engine phases, data flow, and AOA entity container model.
- **`entities_and_factions.md`**: Document Aspect-based composition, removal of `StatsProxy`, and `freeze()` mechanics.

### 2. AI & Systems
- **`ai_system.md`**: Update cognitive pipeline, nested `mind` state, and side-effect-free decision generation.
- **`execution_flow_and_stack.md`**: Align with the new Orchestrated Conductor model.

### 3. Domain Specifics
- **`combat_and_progression.md`**: Document `CombatAspect`, `ProgressionAspect`, and `CombatTraceRecord`.
- **`items_and_inventory.md`**: Document `InventoryAspect`.
- **`attributes_and_classes.md`**: Document attribute scaling in AOA.

### 4. API & Integration
- **`api_reference.md`**: Add introspection endpoints and update schemas to be Aspect-oriented.

## Execution Strategy
1. **Stage 1: Context Gathering**: Present the workflow to the user and confirm the scope.
2. **Stage 2: Refinement & Structure**: Iteratively update each file, verify against `src/`.
3. **Stage 3: Reader Testing**: Use a sub-agent to "read" the updated docs and verify they make sense without prior context.
