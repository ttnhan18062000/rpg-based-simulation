---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260401-FINAL-NON-PARTIAL-TASKS
artifact_type: investigation
tags: [final, non, partial, tasks]
---

# Investigation: Final Non-Partial Tasks (TCK-20260401)

## Town AI Handlers (`src/ai/states/town.py`)
- **Current State**: Handlers return `AIState` and `ActionProposal`. Most use `ActionType.REST` even for buying/selling, carrying data in `updates`.
- **Issue**: Some hand-rolled dicts might still be used, and the brain has a "restore intent_metadata" hack for explainability.
- **Goal**: Ensure all town actions use typed `IntentUpdate` subclasses. Eliminate reliance on `intent_metadata` for core logic.

## Mind Aspect Typing (`src/core/aspects/mind.py`)
- **Current State**: `EmotionState.emotional_state`, `NarrativeMemory.memory_locations`, `NarrativeMemory.region_fatigue`, etc., are `dict[str, float]`.
- **Issue**: Loose strings allow silent typos and lack validation.
- **Goal**: Replace these with Enums or more specific typed structures where possible. At minimum, add validation for keys.

## Snapshot Immutability (`src/core/models/snapshot.py`)
- **Current State**: `Snapshot` is frozen, but `Entity` members are not. AI can accidentally mutate snapshot entities.
- **Issue**: `model_copy(deep=True)` provides isolation from world state, but not internal immutability for the snapshot itself.
- **Goal**: Implement a mechanism to lock snapshot entities or wrap them in a read-only proxy during the AI Phase.

## AIBrain Side-Effects (`src/ai/brain.py`)
- **Current State**: `decide` method ranks `ctx.visible` and generates hints in `ctx.tactical_hints`.
- **Issue**: These mutate the context object during the "read-only" phase.
- **Goal**: Ensure `AIContext` remains truly immutable or that mutations are explicitly isolated and tracked.
