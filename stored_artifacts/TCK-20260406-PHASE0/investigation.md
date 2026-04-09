# TCK-20260406-PHASE0 Investigation

## Existing State Analysis

### Memory & Narrative
- `src/core/aspects/mind.py`: Holds `NarrativeMemory` with `memory_log` (list of `MemoryLogEntry`).
- `memory_log` has `tick`, `type`, `impact`, and `details` (Combat, Loot, Discovery).
- Pragmatic salience already exists: `prune_memories` keeps highest impact memories.

### Identity & Personality
- `src/core/aspects/identity.py`: Holds OCEAN traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism).
- `src/core/aspects/identity.py` and `src/core/aspects/mind.py` both have `life_directive`. This is a duplication point.
- `IdentityAspect` holds `reputation` (float).
- `MindAspect` holds `grudges` (dict[int, float]).

### Goals & Decision
- `MindAspect.decision` holds `goals`, `ai_state`, and `last_reason`.
- Goal selection is influenced by `action_style` ("balanced", "aggressive", "evasive").

## Proposed Redesign Ownership

### Canonical Owners (Initial Hypothesis)
- **Soul (Personality, Archetype, Life Directive)**: `IdentityAspect`. This represents the immutable "core" of the entity.
- **Mind (Cognitive State, Motives, Beliefs, Relationships)**: `MindAspect`.
- **Social (Global Status, Reputation)**: `IdentityAspect` (personal reputation) + `SocialRegistry` (public memory).

## Risks
- **Overlapping Concepts**: "Archetype" vs "Personality" vs "Role".
- **Sprawl**: Each new state bucket needs pruning rules to avoid memory bloat in long-running simulations.
