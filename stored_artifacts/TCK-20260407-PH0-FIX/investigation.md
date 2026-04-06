# Phase 0 Corrective Alignment Investigation

## Goal:
Resolve the architectural misalignments and "fake" narrative logic reported in `phase_0_update_implementation.md`.

## Research Findings:

### 1. EntityInspector Curated Lens
- **Status**: The current `EntityInspector` is a debug panel.
- **Requirement**: Answer Who/What/Risk. Show ongoing arc and likely next choices.
- **Missing Data**: "Likely next choices" needs predictive goal scoring integration. "Ongoing Arc" needs a summary of Recent Memories.

### 2. Overstated Salience Logic
- **Status**: `MindAspect.prune_memories()` is naive. It sorts by `abs(impact)` and hard-truncates to 50.
- **Missing Integration**: `MemorySalienceService` is separate and not called in the main loop.

### 3. Mutation Discipline (AIBrain & ActionSystem)
- **Status**: `AIBrain` mutates state via `prune_memories()` (Side-effect violation).
- **Status**: `ActionSystem` directly appends `InterpretedEvent` to target's `memory_log`.
- **Solution**: Refactor to use `PerceptionUpdate` for all memory additions. Ensure `AIBrain` only proposes updates.

### 4. Social Registry Bug
- **Status**: `SocialRegistry.update_bond()` returns `None`.
- **Status**: `ActionSystem` expects `old_vals, new_vals`.
- **Solution**: Update `SocialRegistry.update_bond()` to return a dictionary of old and new values.

### 5. Divergent Registry Wiring (WorldLoop)
- **Status**: `WorldLoop` owns `_social_registry`. `WorldState` owns `social_registry`.
- **Status**: `ActionSystem` uses `world.social_registry`.
- **Solution**: Unify all references to `world.social_registry`. Ensure `WorldLoop` injects its registry into `WorldState`.

## Duplication / Conflict Scan:
- **Phase 1** work (Personality/Relationships) touched these files. The corrections must preserve Phase 1's personality-driven motives.
- No other active tickets in this area.

## Risks:
- High risk of breaking `GoalEvaluator` or `SocialRegistry` integrations if not carefully refactored.
- `MemorySalienceService` integration could impact performance if not throttled correctly.
