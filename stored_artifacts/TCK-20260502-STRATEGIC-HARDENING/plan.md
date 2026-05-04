# Technical Plan: Strategic Hardening E5.5

## Components Affected

### 1. `src/core/enums.py`
- Refactor `ReasonCode` to `IntEnum`.
- Add new failure codes for capacity, budget, and interruption.

### 2. `src/engine/interaction.py`
- Integrate damage check in `InteractionSystem.enforce`.
- Define threshold (e.g., `0.05 * max_hp`).

### 3. `src/systems/strategic.py` & `src/systems/detour.py`
- Implement bandwidth enforcement logic.
- Ensure `DetourSuggestionSystem` respects `RuntimeProfile` limits.

### 4. `src/engine/tactical.py`
- Implement hierarchical priority for group targets.
- Use `entity.social` trust scores to weight the override.

### 5. `src/engine/kernel.py`
- Add timing checkpoints in `tick_once`.
- Implement graceful degradation on budget exhaust.
