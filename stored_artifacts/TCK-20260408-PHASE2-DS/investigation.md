---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260408-PHASE2-DS
artifact_type: investigation
tags: [phase2, ds]
---

# Investigation — Phase 2 Design Shift: Social Meaning and Behavioral Realism

## Codebase Scan Summary

### Existing Infrastructure (Phase 1 Foundations)
- **`MindAspect`** (`src/core/aspects/mind.py`): Decomposed into Decision, Perception, Emotion, Navigation, Narrative, Routine, and Social sub-models. All under `ConfigDict(extra='forbid')`.
- **`SocialRegistry`** (`src/core/models/social.py`): Global registry for directed `SocialBond`s (trust/fear/rivalry/familiarity). Already has pruning capacity logic and reputation tracking via `reputation: dict[str, float]`.
- **`SocialBondPerception`** + **`SocialStance`** (`mind.py`): Subjective relationship mapping on the mind aspect. Already has `known_bonds` and `faction_standing` and `social_utility_biases`.
- **`InterpretedEvent`** (`mind.py`): Already exists as `memory_log` entries with typed details (`CombatNarrative`, `LootNarrative`, `DiscoveryNarrative`, `SocialNarrative`).
- **`NarrativeMemory`** (`mind.py`): Holds `memory_log` (list of `InterpretedEvent`), `memory_locations`, `region_fatigue`.
- **`MemorySalienceService`** (`src/core/logic/memory_salience.py`): Existing pruning logic for memory_log based on impact × recency weighting.
- **`SocialInterpretationService`** (`src/core/logic/social_interpretation.py`): Already translates harm/help events into `SocialUpdate` deltas.
- **`BeliefRecord`** / **`BeliefService`** (`src/ai/beliefs.py`): Phase 1 subjective perception system.
- **`ActionSystem._apply_updates`** (`src/systems/gameplay/action_system.py`): Authoritative pipeline handling `MindUpdate`, `PerceptionUpdate`, `SocialUpdate`, `RoutineUpdate`, etc.

### Existing Anchor Points for Phase 2
1. **`SocialNarrative`** detail type already exists — can serve as a template for social event interpretation.
2. **`SocialRegistry`** already has `update_bond()` returning old/new values, and creates milestone `InterpretedEvent`s in `action_system.py`.
3. **Reputation** field exists in `SocialRegistry` but is a simple float per entity — Phase 2 needs a typed multi-dimensional reputation profile.
4. **Memory log pruning** exists via `MemorySalienceService` but is for all events — Phase 2 needs a separate turning-point list with its own salience rules.

### Conflicts / Overlaps
- No duplicate tickets found in `tickets/done/` or `tickets/inprogress/` for Phase 2 scope.
- The existing `SocialBondPerception` on mind.social duplicates some of what Phase 2's `RelationshipRecord` needs. Resolution: extend `SocialBondPerception` with additional dimensions (loyalty, resentment, admiration, debt) rather than creating a parallel model.
- The existing `InterpretedEvent` model can serve as the base for the "interpreted life event" concept, but Phase 2 needs a more specific `InterpretedLifeEvent` that carries semantic tags (near_death, avenged_ally, etc.) and relationship/reputation deltas. Resolution: extend the existing type with new detail discriminators.

### Architecture Decisions
1. **Turning points stored on `mind.narrative`** — not a separate registry. This keeps per-entity lifecycle intact and avoids a global cross-cutting concern.
2. **Reputation as a typed profile on the entity**, not just a float in SocialRegistry — enables multi-dimensional reputation (defender_score, cowardice_score, etc.).
3. **Event interpreter as a dedicated service** under `src/core/logic/event_interpreter.py` — centralizes the translation from raw simulation events to social meaning.
4. **Social state application centralized** in ActionSystem's existing pipeline via a new `SocialStateUpdate` or by extending `PerceptionUpdate` / `SocialUpdate`.
5. **Knowledge propagation** as a bounded, tick-triggered service — not continuous gossip.

### Test Patterns
- Existing unit tests under `tests/unit/ai/` use `MagicMock` entities and `@pytest.fixture` patterns.
- Integration tests wire real `Entity` + `WorldState` objects.
- Follow the same pattern for new Phase 2 tests.
