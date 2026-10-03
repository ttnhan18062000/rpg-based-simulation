---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260331-RUNTIME-INTEGRITY
artifact_type: investigation
tags: [runtime, integrity]
---

# Investigation: Runtime Integrity & Legacy Access Patterns

## Current State Analysis

### 1. Legacy Access Patterns
A grep search revealed ~40+ occurrences of `.stats.*` and `.mind.ai_state` in critical paths:
- **Systems**: `economy_system.py`, `hero_lifecycle_system.py`, `progression_system.py`, `telemetry_system.py`.
- **AI**: `ai/states.py`, `ai/goals/base.py`.
- **API**: `api/encoder.py`.

These call sites are referencing attributes that should have been moved to aspects:
- `entity.stats.combat.hp` -> `entity.combat.hp`
- `entity.stats.progression.gold` -> `entity.progression.gold`
- `entity.mind.ai_state` -> `entity.mind.decision.state`

### 2. AI Mutation Violations
In `src/ai/states.py`, several handlers (especially `VisitShopHandler`, `VisitBlacksmithHandler`, `HarvestingHandler`) mutate the `actor` object directly:
- `actor.stats.gold += price`
- `actor.stats.hp = min(...)`
- `actor.inventory.add(item)`

This is architectural dishonesty because AI is supposed to be side-effect free, emitting only `ActionProposal`s.

### 3. API Serialization
The API routes in `src/api/routes/state.py` still seem to rely on legacy serialization or missing entity methods like `to_slim_schema()`. The `EntityPresenter` exists but is not universally applied.

### 4. Inline Worker Path
The `WorldLoop` currently dispatches AI. If `num_workers <= 1`, it might be passing the live `Entity` object instead of a snapshot copy, allowing accidental mutations to leak into the authoritative state.

## Risks & Assumptions
- **Assumption**: The `Entity` model's aspect fields are correctly typed and initialized.
- **Risk**: Missing a legacy call site in a rare AI state could lead to runtime crashes (`AttributeError`).
- **Risk**: Refactoring shop/crafting to be "proposal-only" requires a robust mechanism to handle multi-step interactions in the authoritative resolver.

## Reuse Opportunities
- `EntityPresenter` in `src/api/presenters/` should be the sole source of truth for API shapes.
- `ActionProposal`'s `intent_metadata` can be used temporarily for deferred updates until typed models are introduced.
