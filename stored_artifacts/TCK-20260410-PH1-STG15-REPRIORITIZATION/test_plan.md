# Phase 1 Stage 15: Strategic Reprioritization — Test Plan

## Scenario 1: Default Pursuit
- **Setup**: Region danger = 0. Hero has "Professional" directive.
- **Expected**: `current_project_id` = `project_professional_...`, `status` = `ACTIVE`.

## Scenario 2: Regional Crisis Intervention
- **Setup**: Hero is active on a development project. Set regional `danger_level` = 0.8.
- **Action**: Run `StrategicEvaluatorService.evaluate`.
- **Expected**:
    1. `ConcernRecord` kind `THREAT` labeled "Regional Threat" is added.
    2. `interrupted_project_id` stores the previous project.
    3. `current_project_id` shifts to a "Restore Stability" project.
    4. New `ObjectiveRecord` kind `INVESTIGATE` or `INTERACT` is active.

## Scenario 3: Battlefield Curiosity
- **Setup**: Hero is near a `LocalScarRecord` (kind=BATTLE_FIELD).
- **Action**: Run `StrategicEvaluatorService.evaluate`.
- **Expected**:
    1. `ConcernRecord` kind `OPPORTUNITY` for "Scar Investigation".
    2. New objective to visit the scar coordinates is appended to current project or a new investigation project.

## Scenario 4: Stability Recovery (Hysteresis)
- **Setup**: Hero is on a "Restore Stability" project because danger was 0.8. Set danger = 0.2.
- **Action**: Run `StrategicEvaluatorService.evaluate`.
- **Expected**:
    1. Stabilization project is `RESOLVED` or `SUSPENDED`.
    2. `current_project_id` returns to `interrupted_project_id`.
