# Plan: Phase 1 DS Implementation

## Phase 1: Foundations of Behavioral Realism

### Part 1: Data Models (Foundations)
- [ ] Define `PersonalityProfile` in `src/core/aspects/mind.py`.
- [ ] Define `PersonalMotive` in `src/core/aspects/mind.py`.
- [ ] Define `ThreatEstimate` and `BeliefRecord` in `src/core/aspects/mind.py`.
- [ ] Update `MindAspect` to include these new models.
- [ ] Update `IdentityAspect` to remove OCEAN traits and keep `Archetype`.

### Part 2: Seeding & Infrastructure
- [ ] Update `EntityBuilder` with fluent methods for the new personality/motives.
- [ ] Update `EntityBuilder.build()` to handle trait initialization from Archetype templates.
- [ ] Update `generator.py` to seed initial motives and trait variations.

### Part 3: AI Cognitive Pipeline
- [ ] Implement `BeliefRefreshService` in `src/ai/beliefs.py`.
- [ ] Update `AIBrain._sensory_perception_phase` to call belief refresh.
- [ ] Update `AIBrain._memory_appraisal_phase` to age/decay beliefs.
- [ ] Update `GoalEvaluator` (or `PersonalityLogic`) to use the new 6-axis personality traits.
- [ ] Implement motive-based utility modifiers in `AIBrain`.

### Part 4: Migration of decision paths
- [ ] Update `FleeHandler` or `CombatHandler` to use `belief.threat_estimate` instead of direct target HP/stats.

### Part 5: Visibility & Inspection
- [ ] Update `src/api/schemas.py` and `presenters/entity_presenter.py` to expose the new state.
- [ ] Add `DecisionDriver` metadata to `ActionProposal` for explainability.

### Part 6: Verification
- [ ] Run behavioral divergence tests.
- [ ] Run belief update/decay tests.
- [ ] Verify inspection payloads in a local run.
