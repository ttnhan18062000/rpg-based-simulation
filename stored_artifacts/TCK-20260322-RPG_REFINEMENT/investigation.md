# Investigation: RPG Core Refinement (TCK-20260322-RPG_REFINEMENT)

## Current State Analysis

### 1. Cognitive Pipeline (The Soul)
- **Status**: Structural phases are implemented in `AIBrain.py` (Input, Internal State, Deliberation, Output).
- **Gaps**:
    - **Step 2 (Perception)**: Selective attention is basic (nearest hostiles). Needs deeper saliency ranking.
    - **Step 4 (Appraisal)**: Emotions (Panic, Stuck) exist but don't heavily influence Utility AI weights yet.
    - **Hysteresis**: `boredom_multipliers` exist but don't prevent high-frequency goal switching effectively.

### 2. Genetics & Aptitudes (The Body)
- **Status**: `genetic_seed` and `aptitudes` dict exist in `ProgressionAspect`. `init_genetics()` is implemented.
- **Gaps**:
    - Attributes do not yet use `aptitudes` during level-up or training.
    - Breakthrough caps (50, 75, 100) are not enforced or rewarded with traits.

### 3. Tactical Action (The Action)
- **Status**: `action_style` exists in `MindAspect`.
- **Gaps**:
    - Stances/Styles aren't fully integrated into `ConflictResolver` or `SkillEffect` logic beyond simple name tagging.
    - "Generous Thinking": No specific goals for healing or buffing allies in `scorers.py`.

### 4. Relationship Memory (The Social)
- **Status**: `hero_familiarity` and `grudges` exist in `IdentityAspect`.
- **Gaps**:
    - Memory doesn't record "Highlights" (Trauma/Glory).
    - Familiarity growth is linear; needs scaling with Charisma (partially fixed in TCK-20260325-RPG_DEPTH).

## Existing Patterns to Reuse
- `Utility AI`: The `GoalEvaluator` and `GoalScorer` pattern is the primary mechanism for logic injection.
- `Aspect System`: All states are correctly stored in `Mind`, `Identity`, and `Progression`.

## Risks & Assumptions
- **Performance**: High-frequency pathfinding or complex appraisal every tick might drop TPS.
- **Complexity**: Circular dependencies in `src/ai/states.py` might resurface if handlers need deep mind access.
