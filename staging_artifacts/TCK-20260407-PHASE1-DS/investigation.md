# Investigation: Phase 1 Design Shift

## Research Findings
- `src/core/aspects/mind.py`: Current `MindAspect` has sub-models for Decision, Perception, Emotion, Navigation, Narrative, and Routine.
- `src/ai/brain.py`: Implements a 4-phase AI pipeline. Phase 1 (Sensing/Perception) and Phase 2 (Memory/Appraisal) are primary targets for belief refresh and decay.
- `src/core/aspects/identity.py`: Currently holds OCEAN personality traits. The new plan suggests a `PersonalityProfile` under `mind` with different traits (Aggression, Greed, Caution, Loyalty, Ambition, Curiosity).
- `src/core/entities/entity_builder.py`: Seeds OCEAN traits and archetypes. Needs update to support the new `PersonalityProfile`.
- `src/core/logic/personality.py` & `src/core/logic/social_appraisal.py`: Existing logic for OCEAN-based biasing. Needs to be replaced or augmented with the new trait set.

## Duplication/Conflict Scan
- Conflict: Existing OCEAN traits vs. New Personality traits (Aggression, Greed, etc.). The plan suggests the new set. I should probably transition to the new set or allow both if needed, but the plan is specific about the 6-axes.
- Overlap: `DecisionState` already has a `motives` dict and `last_appraisal_tick`. The plan asks for a more structured `PersonalMotive` model.

## Assumptions
- The 6 trait axes (Aggression, Greed, Caution, Loyalty, Ambition, Curiosity) are the new authoritative behavioral model.
- `MindUpdate` and `PerceptionUpdate` in `src/actions/base.py` will needs new fields to transport motive and belief changes.

## Known Risks
- Circular dependencies in Pydantic models when adding complex nested structures (already a known issue in this repo, handled by `model_rebuild`).
- Performance impact of belief-refresh for all visible entities (mitigated by selective attention).
