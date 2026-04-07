# Ticket: TCK-20260407-STAGE1-DS
## Stage 1 - Design Shift Implementation: Behavioral Realism

### Request Summary
Implementation of Stage 1 of the RPG Macro-Interest and Behavioral Realism Plan. This Stage focuses on establishing recognizable individuals through personality traits, long-term motives, and subjective belief-based perception.

### Scope
- [x] Establish the Stage 1 implementation boundary.
- [x] Add a typed `PersonalityProfile` model under the `mind` layer.
- [x] Seed personality and archetype at entity creation time.
- [x] Add a typed `PersonalMotive` model under the `mind/narrative` layer.
- [x] Seed initial motives at entity creation time.
- [x] Add a typed `BeliefRecord` model for other entities.
- [x] Add a typed `ThreatEstimate` submodel with explicit confidence handling.
- [x] Add a belief-refresh service for observation-to-belief updates.
- [x] Wire personality bias into goal scoring.
- [x] Wire long-term motives into goal scoring.
- [x] Refresh belief records during the sensory/perception stage.
- [x] Age and degrade beliefs during appraisal/memory maintenance.
- [/] Replace selected omniscient decision paths with belief-based decision inputs.
- [x] Extend entity inspection schemas with personality, motives, and important beliefs.
- [/] Add decision-driver explanation fields for personality, motives, and beliefs.
- [x] Add behavioral divergence tests.
- [/] Add belief-update and belief-decay tests.
- [/] Add inspection-schema tests.

### Out of Scope
- Relationships (deferred to Stage 2).
- Rumors or shared-knowledge systems.
- Daily/weekly routine systems (deferred to Stage 3).
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
