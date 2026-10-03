---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260427-PH6-STRATEGIC-COGNITION
artifact_type: investigation
tags: [ph6, strategic, cognition]
---

# Investigation - Phase 6 Strategic Cognition

## Current State Analysis

### 1. Project Management
- `StrategicIntelligenceSystem.evaluate_strategic_intent` handles project scoring and creation.
- `TacticalDecisionSystem.evaluate_entity_intent` handles the execution of objectives.

### 2. Blockers
- `BlockerState` is defined in `src/core/strategic.py`.
- `StrategicIntelligenceSystem.generate_crafting_blockers` creates them for materials.
- **GAP**: Non-material blockers (e.g. "path blocked", "target missing") are not automatically generated from action failures.

### 3. Detours
- `DetourSuggestionSystem` is implemented in `src/systems/detour.py`.
- **GAP**: It is not currently integrated into the `StrategicIntelligenceSystem.evaluate_strategic_intent` loop.

## Proposed Strategy

### Blocker Feedback Loop
1.  In `AuthoritativeApplyPipeline._route_combat_intent`, if `LegalityServiceV2.verify_attack_legality` fails, add a `StrategicUpdate` with a blocker.
2.  In `AuthoritativeApplyPipeline._route_movement_intent`, if `MovementSystem.resolve_move` returns a failure, add a navigation blocker.

### Detour Activation
1.  In `StrategicIntelligenceSystem.evaluate_strategic_intent`:
    - Before scoring new projects, check if the *current* project has an active objective that matches an existing blocker.
    - If blocked, call `DetourSuggestionSystem.suggest_detours`.
    - If a detour exists with utility > (current_blocked_project_utility), switch to it.

## Technical Risks
- **Oscillation**: Switching between a blocked project and a detour might cause ping-pong behavior if not handled by hysteresis.
- **Memory Growth**: Blockers must be cleaned up when no longer relevant.
