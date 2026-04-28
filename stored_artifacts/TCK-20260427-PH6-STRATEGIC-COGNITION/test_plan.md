# Test Plan - Phase 6 Strategic Cognition

## Objective
Verify the end-to-end strategic loop: Failure -> Blocker -> Lead -> Detour -> Success.

## Test Cases

### 1. Material Blocker & Detour
- **Setup**: Hero has a "Craft" project but lacks "Iron".
- **Action**: Hero tries to interact with a Blacksmith.
- **Expected**: 
    - `AuthoritativeApplyPipeline` generates a `blocker_mat_Iron`.
    - `StrategicIntelligenceSystem` detects the blocker.
    - `DetourSuggestionSystem` finds a lead for Iron (e.g. at a Mine).
    - AI switches project to "Gather Iron".
- **Verification**: Check `entity.strategic.current_project_id` transitions.

### 2. Navigation Blocker
- **Setup**: Hero has a project to reach (10,10), but (10,10) is surrounded by walls.
- **Action**: Hero tries to move.
- **Expected**:
    - `AuthoritativeApplyPipeline` generates a `blocker_nav_PATH_BLOCKED`.
    - Hero suspends the project.
- **Verification**: Check `entity.strategic.blockers` contains a navigation blocker.

### 3. Lead Resolution
- **Setup**: Hero has a blocker for "Gold".
- **Action**: Hero finds a chest and loots 10 gold.
- **Expected**:
    - `StrategicIntelligenceSystem.resolve_blockers` identifies the gold addition.
    - Blocker for "Gold" is removed.
    - Hero resumes the original project.
- **Verification**: Check `entity.strategic.blockers` is empty after loot.
