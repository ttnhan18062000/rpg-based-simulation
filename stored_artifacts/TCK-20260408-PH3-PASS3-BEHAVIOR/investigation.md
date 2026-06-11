---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260408-PH3-PASS3-BEHAVIOR
artifact_type: investigation
tags: [ph3, pass3, behavior]
---

# Investigation - Phase 3 Pass 3: Behavioral Integration

## Findings from Codebase
- `MindAspect.routine_profiles` and `MindAspect.place_attachments` are successfully seeded in Pass 2.
- `AIBrain._memory_appraisal_phase` already has a hook for `RoutineService.calculate_routine_biases`.
- `RoutineService.calculate_routine_biases` currently uses a legacy `RoutineState` model.
- `IdentityAspect` has `world_role` and `cluster_id`.

## Assumptions
- "Hours" in the simulation are 10-tick windows of a 240-tick day.
- Biological needs (sleep/hunger) in `RoutineState` should still be calculated, as they provide a "hard" override to routines.
- `PlaceAttachment` bias will be applied primarily when selecting targets for `REST`, `SLEEP`, and `WORK` type goals.

## Duplication/Conflict Scan
- I noted that `RoutineState` (biological) and `RoutineProfile` (social pattern) overlap in name but serve different roles (Internal Need vs External Window). I will keep both but ensure they synergize.
- No existing group coordination logic beyond basic faction-based following. `cluster_id` is fresh.

## Risks
- Too much bias could make entities "stiff" and unable to react to threats.
- Disruption logic must be robust to prevent entities from trying to sleep while being attacked by a goblin.
