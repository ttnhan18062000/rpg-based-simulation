# Ticket: TCK-20260407-PHASE1-DS
## Phase 1 - Design Shift Implementation: Behavioral Realism

### Request Summary
Implementation of Phase 1 of the RPG Macro-Interest and Behavioral Realism Plan. This phase focuses on establishing recognizable individuals through personality traits, long-term motives, and subjective belief-based perception.

### Scope
- [ ] Establish the Phase 1 implementation boundary.
- [ ] Add a typed `PersonalityProfile` model under the `mind` layer.
- [ ] Seed personality and archetype at entity creation time.
- [ ] Add a typed `PersonalMotive` model under the `mind/narrative` layer.
- [ ] Seed initial motives at entity creation time.
- [ ] Add a typed `BeliefRecord` model for other entities.
- [ ] Add a typed `ThreatEstimate` submodel with explicit confidence handling.
- [ ] Add a belief-refresh service for observation-to-belief updates.
- [ ] Wire personality bias into goal scoring.
- [ ] Wire long-term motives into goal scoring.
- [ ] Refresh belief records during the sensory/perception phase.
- [ ] Age and degrade beliefs during appraisal/memory maintenance.
- [ ] Replace selected omniscient decision paths with belief-based decision inputs.
- [ ] Extend entity inspection schemas with personality, motives, and important beliefs.
- [ ] Add decision-driver explanation fields for personality, motives, and beliefs.
- [ ] Add behavioral divergence tests.
- [ ] Add belief-update and belief-decay tests.
- [ ] Add inspection-schema tests.

### Out of Scope
- Relationships (deferred to Phase 2).
- Rumors or shared-knowledge systems.
- Daily/weekly routine systems (deferred to Phase 3).
- Public reputation systems.
- Inheritance/successor systems.
- Regional consequence simulation.

### Acceptance Criteria
- Same-class entities behave differently under same conditions due to personality/motives.
- AI uses belief instead of exact hidden truth in at least 2-4 important decision paths.
- Beliefs strengthen through observation and weaken with staleness.
- Chosen-entity inspection clearly shows personality, motives, and important beliefs.

### Status
INPROGRESS
