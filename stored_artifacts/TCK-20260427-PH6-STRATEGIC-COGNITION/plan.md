---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260427-PH6-STRATEGIC-COGNITION
artifact_type: plan
tags: [ph6, strategic, cognition]
---

# Implementation Plan - Phase 6 Strategic Cognition Hardening

## Goal
Implement the legacy logic for strategic cognition into the V2 engine, specifically focusing on the failure-to-blocker feedback loop and detour suggestion integration.

## Proposed Changes

### [Component] Authoritative Apply Pipeline
#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- In `_route_combat_intent` and `_route_movement_intent`, capture failure reasons from `LegalityServiceV2` and `MovementSystem`.
- Map these failures to `BlockerState` types.
- Append a `StrategicUpdate` containing the new blocker to the `EntityUpdate`.

### [Component] Strategic Intelligence System
#### [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic.py)
- Update `evaluate_strategic_intent` to check for active blockers on the current project.
- Integrate `DetourSuggestionSystem` to suggest alternative projects when blocked.
- Implement project switching logic with utility-based hysteresis.

### [Component] Detour Suggestion System
#### [MODIFY] [detour.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/detour.py)
- Ensure detour scoring is aligned with V2 utility metrics.
- Harden lead resolution logic to properly remove blockers.

## Verification Plan

### Automated Tests
- Run `pytest tests/systems/test_strategic_cognition_regression.py` (once implemented/recovered).
- Implement a new scenario in `src/certification/scenarios.py` for "Strategic Blockage & Detour".

### Manual Verification
- Use `HeadlessRunner` with a 500-tick run and verify `entity.strategic.blockers` and `current_project_id` transitions in the JSON replay.
