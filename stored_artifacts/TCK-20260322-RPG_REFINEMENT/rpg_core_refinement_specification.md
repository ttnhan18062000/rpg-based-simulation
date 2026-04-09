# Specification: RPG Core Refinement (The 4 Pillars)

This document defines the transition from a "Robotic/Reactive" simulation to a "Living/Proactive" RPG world.

## The 7-Step Cognitive Pipeline

The `AIBrain` must orchestrate entity thinking through these distinct steps, grouped into 4 execution phases:

### Phase 1: Input (Sensory & Perception)
1. **Sensory (Sensing)**: Gather raw snapshot data (visible entities, tiles, items).
2. **Perception (Selective Attention)**: Filter data through vision and saliency. Rank entities by importance (Hostility, Distance, Rarity).

### Phase 2: Internal State (Memory & Appraisal)
3. **Memory Recall (Context)**: Retrieve past interactions (Grudges, Territory sentiment, "Am I stuck?").
4. **Appraisal (Subjectivity)**: Update mood (0.0 to 1.0) and internal needs. Influence thresholds (Flee @ 30% HP if panicking, 10% if brave).

### Phase 3: Deliberation (Planning)
5. **Deliberation (Goal Evaluation)**: Run Utility AI scorers with all modifiers (Boredom, Personality, Mood).
6. **Tactical Planning**: For the selected goal, compute the "how". A* pathfinding, kiting distance, AoE positioning.

### Phase 4: Output (Execution)
7. **Finalization (Proposal)**: Construct the final `ActionProposal`. Must include a narrative `reason` string for debugging and UI.

---

## The 4 Pillars of Refinement

### 1. The Soul (Mind & Emotions)
- **Mood Lifecycle**: Restore mood passively when safe. Mood decreases when outnumbered.
- **Narrative Memory**: Heroes record "Memory Highlights" (e.g., "Slew a goblin chieftain in the Swamp").
- **Proactive Goals**: Entities shouldn't just wait for HP to drop; they should "Seek Adventure" or "Visit Town" based on long-term goals.

### 2. The Body (Genetics & Aptitudes)
- **Genetic Seed**: Every entity has a fixed seed deriving its potential.
- **Attribute Aptitudes**: Multipliers (0.8x to 1.3x) applied to attribute training and level-up gains.
- **Breakthrough Refinement**: High attributes (50, 75, 100) unlock unique "Pillar Traits".

### 3. The Action (Hysteresis & Movement)
- **Hysteresis**: Stronger persistence in goals. Don't jitter between "Combat" and "Flee" every tick.
- **Generous Thinking**: Entities consider "What is best for my faction/party?" not just self (e.g., healing an ally).
- **Movement Fluidity**: Use road costs more aggressively. Avoid "vibrating" on the same tile.

### 4. The Social (Relationships)
- **Relationship Depth**: Familiarity leads to "Friendship" or "Rivalry".
- **Dynamic Factions**: Relations can shift globally based on world events (implemented in StrategySystem, but AI must react).
