---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

## WorldLoop RPG Macro-Interest and Behavioral Realism Implementation Plan — Phase 2 [COMPLETED]

This plan covers the second major design shift: **Dynamic Social Meaning, Relationships, and Durable History.**

## Status: DONE (2026-04-08)
- [x] Stage 1 & 2: Social Meaning and Relationships
- [x] Stage 3: Routine and Biological Needs
- [x] Stage 4: Social Convergence & Narrative Causal Analysis

This phase builds on Phase 1’s subjective individual state and makes that state socially meaningful. Phase 1 is about “who this entity is, what it wants, and what it believes.” Phase 2 is about “what happened to this entity that matters, who matters to it, and how those things change future behavior.” The core goal is to convert raw events and memory into durable turning points, bounded relationships, public reputation, and readable life-level explanations. The current codebase already has useful anchors for this: mind/perception/narrative state, memory logs, typed updates, event recording, combat traces, and presenter/introspection support.

---

## Proposed Changes

### Phase 2 Stage 1 & 2: Social Meaning and Relationships

This stage focuses on making the individual subjective state (established in Phase 1) socially meaningful by introducing turning-point memory, interpreted events, bounded relationships, and public reputation.

Technical implementation:

- define the Phase 2 scope in `phase_2_implementation_plan.md`
- add a short internal design note near mind/event/presenter modules describing the new responsibilities:
  - turning-point memory
  - interpreted events
  - bounded relationships
  - public reputation
  - social propagation of knowledge
  - life-level explanation

- explicitly defer:
  - routines
  - household role systems
  - inheritance/succession
  - regional consequence simulation

Files affected:

- `phase_2_implementation_plan.md`
- likely a small module-level comment/docstring in:
  - `src/core/aspects/mind.py`
  - `src/ai/brain.py`
  - presenter/introspection modules

Important notes:

- do not pollute Phase 2 with world-economy or settlement simulation
- this phase is about social and historical meaning, not infrastructure expansion
- success means “events now matter later,” not “the world is fully alive”

---

### Turning-Point Memory Foundations

#### [x] Add a typed turning-point memory model under the mind/narrative layer

Review comment: Current memory and logs can record events, but the simulation still needs a stronger distinction between routine events and life-changing events. Phase 2 requires a durable turning-point model for moments like near death, ally death, betrayal, rescue, disgrace, revenge, home loss, or boss encounter.

Technical implementation:

- add a typed `TurningPointRecord` model under mind/narrative
- include fields such as:
  - `event_id`
  - `kind`
  - `tick`
  - `location`
  - `involved_entity_ids`
  - `summary_tag`
  - `emotional_impact`
  - `relationship_effects`
  - `motive_effects`
  - `still_salient`

- add `turning_points: list[TurningPointRecord]` to `mind.narrative`
- add validation and cap rules:
  - hard cap retained turning points
  - salience-based pruning
  - bounded impact values

Files affected:

- `src/core/aspects/mind.py`
- possibly `src/actions/base.py` if turning-point creation is transported through typed updates
- any model rebuild path for mind-related models

Important notes:

- this is not a full diary
- only high-impact memories belong here
- if you allow every event into turning points, the feature becomes useless noise
- turning points should be rare, meaningful, and behaviorally relevant

---

#### [x] Add salience and pruning rules for turning-point memory

Review comment: A turning-point system without retention discipline becomes a memory leak disguised as narrative. Phase 2 needs a clear rule for what stays important, what fades, and what gets replaced.

Technical implementation:

- implement salience scoring based on:
  - emotional impact
  - relation to active motives
  - relation to important entities
  - recency
  - severity

- add utility functions to:
  - insert new turning points
  - merge duplicates if necessary
  - prune low-salience old entries

- store salience or derive it consistently

Files affected:

- `src/core/aspects/mind.py`
- likely a new helper module, for example:
  - `src/ai/life_events.py`
  - or `src/core/narrative/turning_points.py`

Important notes:

- prune by salience, not purely age
- some old events should stay alive because they still define the entity
- do not build a vague “important = true” heuristic; make the rule explicit

---

### Event Interpretation Layer

#### [x] Add a typed interpreted-event model that translates raw simulation events into social meaning

Review comment: Raw events like move, attack, rest, or loot are mechanically useful but socially meaningless. Phase 2 requires a semantic layer that interprets behavior into legible social events such as held line, abandoned ally, avenged friend, panicked flee, opportunistic looting, failed rescue, or survived impossible odds.

Technical implementation:

- add a typed `InterpretedLifeEvent` model with fields like:
  - `event_id`
  - `kind`
  - `tick`
  - `actor_id`
  - `subject_ids`
  - `location`
  - `evidence_refs`
  - `severity`
  - `public_visibility`
  - `relationship_deltas`
  - `reputation_deltas`
  - `turning_point_candidate`

- this model should sit above raw combat/log/event streams
- keep it independent from rendering text

Files affected:

- likely new file:
  - `src/core/models/life_events.py`
  - or similar domain-appropriate location

- `src/core/aspects/mind.py` if interpreted events are attached to narrative state
- presenter/query schema modules later in this phase

Important notes:

- this is a semantic interpretation layer, not prose generation
- interpreted events should be sparse and high-value
- do not attach natural-language text generation logic to the core model

---

#### [x] Add an event-interpretation service that consumes raw actions/traces and emits interpreted events

Review comment: The interpreted-event model is worthless unless there is one explicit place where raw simulation data becomes social meaning. This translation should not be distributed across unrelated systems.

Technical implementation:

- create a dedicated interpretation service, for example:
  - `src/systems/narrative/event_interpreter.py`
  - or `src/ai/life_events.py`

- feed it from authoritative post-application data such as:
  - combat traces
  - action proposals after application
  - deaths
  - flee events
  - rescue-like movement/combat contexts

- implement a first rule set for a limited set of tags:
  - near_death
  - ally_died_nearby
  - avenged_ally
  - fled_from_threat
  - held_position
  - looted_during_danger
  - first_boss_encounter

- emit typed interpreted events, not strings

Files affected:

- new interpreter module
- likely `src/systems/gameplay/action_system.py` to invoke it after authoritative application
- maybe `src/engine/world_loop.py` or an appropriate post-action phase if that is the canonical hook
- possibly `src/actions/combat.py` only if additional trace fields are needed

Important notes:

- place the hook after authoritative action application, not inside speculative AI logic
- do not start with twenty event kinds
- begin with a small set that clearly affects relationships, reputation, and turning points

---

#### [x] Route interpreted events into turning points, motives, and social state updates

Review comment: Interpretation only matters if it changes later behavior. Phase 2 requires a clear flow from interpreted events into memory, relationships, motives, and reputation. Otherwise it becomes another analytics layer.

Technical implementation:

- after interpreted events are emitted:
  - update turning-point memory when salience threshold is met
  - adjust motive frustration/progress when relevant
  - apply relationship deltas
  - apply reputation deltas

- this can be done through typed updates or one centralized authoritative social-state application path
- prefer a centralized path if multiple state domains are touched

Files affected:

- `src/systems/gameplay/action_system.py`
- possibly a new authoritative social-state application module
- `src/actions/base.py` if new typed updates are introduced
- `src/core/aspects/mind.py`

Important notes:

- do not let interpreted events directly mutate arbitrary fields in scattered places
- this is a dangerous place for hidden coupling
- keep the mutation path authoritative and inspectable

---

### Relationship Graph Foundations

#### [x] Add a bounded typed relationship model for important entities

Review comment: Memory about others is not enough. Phase 2 needs explicit social meaning: trust, fear, loyalty, resentment, rivalry, debt, admiration, blame. This is one of the highest-leverage systems for making behavior watchable.

Technical implementation:

- add a typed `RelationshipRecord` model with fields like:
  - `other_entity_id`
  - `trust`
  - `fear`
  - `loyalty`
  - `resentment`
  - `admiration`
  - `debt`
  - `rivalry`
  - `last_updated_tick`
  - `relationship_tags`

- add a bounded relationship map/list under mind state
- choose storage shape carefully:
  - `dict[int, RelationshipRecord]` is practical
  - but enforce a max relationship count

- add helper functions for safe updates and pruning

Files affected:

- `src/core/aspects/mind.py`
- `src/actions/base.py` if relationship deltas travel through typed updates
- any presenter showing chosen-entity relationship context

Important notes:

- bound the relationship graph hard
- “important entities only” is mandatory
- avoid creating a full NxN social graph in Phase 2
- not every observed entity deserves relationship state

---

#### [x] Add relationship update rules driven by interpreted events and repeated interaction

Review comment: Relationship records should not be hand-authored or updated arbitrarily. Phase 2 needs explicit update rules tied to what happened: rescue, betrayal, repeated cooperation, repeated threat, debt, revenge, or abandonment.

Technical implementation:

- implement relationship delta rules for:
  - ally saved me -> trust/loyalty up
  - abandoned me -> resentment/blame up
  - repeated nearby support -> admiration/trust up
  - repeated threat/ambush -> fear/resentment up
  - avenged me/us -> admiration/loyalty up
  - killed my ally -> resentment/fear up

- use interpreted events as the primary source
- allow repeated low-impact reinforcement from recurring interaction later if cheap enough

Files affected:

- likely new relationship helper/service module
- event interpreter module
- authoritative social-state application path
- `src/core/aspects/mind.py`

Important notes:

- use interpreted events, not raw every-tick co-location
- avoid noisy constant drift from proximity alone in Phase 2
- relationship changes should be legible and attributable

---

#### [x] Prune and prioritize important relationships

Review comment: A relationship system becomes unreadable and expensive if every entity relationship is retained forever. Phase 2 requires explicit prioritization and eviction rules.

Technical implementation:

- define relationship salience or importance based on:
  - emotional magnitude
  - recency
  - repeated interaction
  - motive relevance
  - threat relevance

- add eviction logic for low-salience relationships when capacity is exceeded
- preserve a small top set for inspection and decision use

Files affected:

- relationship helper/service module
- `src/core/aspects/mind.py`

Important notes:

- chosen-entity viewing only needs the top few relationships
- relationship capacity should be small enough to stay meaningful
- if everything matters, nothing matters

---

### Public Reputation and Shared Social Memory

#### [x] Add a typed public reputation model at the entity and group-facing layer

Review comment: Private memory and relationships are not enough. The world also needs socially shared memory: defender, coward, looter, boss-slayer, unreliable, feared raider, trusted escort. That memory should be queryable and behaviorally relevant.

Technical implementation:

- create a typed `ReputationProfile` model with fields like:
  - `local_reputation_tags`
  - `defender_score`
  - `cowardice_score`
  - `greed_score`
  - `heroism_score`
  - `threat_notoriety`
  - `trustworthiness`
  - maybe scoped by faction/town later if the model supports it cleanly

- attach it to an appropriate stable domain:
  - objective identity/progression layer if truly public and world-facing
  - or a dedicated world/social state registry if more correct

- for Phase 2, attaching a compact profile to the entity may be acceptable if scope is controlled

Files affected:

- likely `src/core/entities/entity.py` or a suitable aspect model if a dedicated reputation aspect is introduced
- possibly `src/core/aspects/interaction.py` if you keep public/social state there
- presenter/schema modules later in this phase

Important notes:

- reputation is public-facing state, not private belief
- do not overload personality or motives with public reputation
- keep the first version compact

---

#### [x] Add reputation update rules from interpreted life events

Review comment: Reputation must be earned from visible actions, not arbitrary scripted labels. The event-interpretation layer is the correct source for reputation deltas.

Technical implementation:

- map interpreted events to public reputation deltas:
  - held_line -> defender_score up
  - fled_from_threat -> cowardice_score up
  - looted_during_danger -> greed_score / trustworthiness down
  - avenged_ally / boss_slaying -> heroism up / notoriety up

- respect event visibility:
  - private acts should not become public reputation automatically
  - use `public_visibility` from interpreted events

- apply reputation updates in the same authoritative social-state path as relationships when possible

Files affected:

- event interpreter module
- authoritative social-state application path
- entity/aspect model holding reputation
- presenter modules

Important notes:

- public and private meaning must stay separate
- not everything witnessed by one actor becomes town-wide truth
- reputation is for social memory, not exact moral accounting

---

### Social Propagation of Knowledge

#### [x] Add a bounded social knowledge propagation mechanism for important threat and reputation information

Review comment: The world becomes more believable when actors can learn from others instead of only direct contact. Phase 2 does not need a full rumor economy, but it does need a limited mechanism for allies/towns/factions to share important knowledge about threats and notable deeds.

Technical implementation:

- add a propagation service, for example:
  - `src/systems/social/knowledge_propagation.py`

- support a narrow set of transferable knowledge:
  - dangerous actor identities
  - known boss capabilities
  - trusted defenders
  - feared raiders

- propagate into:
  - private belief records with lower confidence than direct observation
  - or public reputation profiles where appropriate

- mark propagated knowledge as indirect/source-derived

Files affected:

- new knowledge propagation module
- `src/core/aspects/mind.py` if belief records gain source/source-confidence fields
- reputation-holding model
- world/system hooks that run propagation at appropriate intervals or triggers

Important notes:

- keep indirect knowledge weaker than direct knowledge
- do not invent a full rumor simulation in Phase 2
- a small, explicit propagation rule set is enough

---

#### [x] Differentiate direct knowledge from indirect knowledge in belief records

Review comment: If second-hand information is stored the same way as direct observation, the AI will treat rumor as certainty. Phase 2 needs source quality in the belief model.

Technical implementation:

- extend the belief record model added in Phase 1 with:
  - `knowledge_source` or source tags
  - `directness`
  - `source_confidence`

- when social propagation updates a belief:
  - mark it as indirect
  - use lower confidence
  - allow direct observation to overwrite or refine later

Files affected:

- `src/core/aspects/mind.py`
- `src/ai/beliefs.py`
- social propagation module
- any decision path reading belief confidence

Important notes:

- this is necessary for believable mistakes
- “I heard he is dangerous” should not equal “I saw him kill three allies”
- if you skip this, social knowledge will flatten all uncertainty

---

### Life-Level Explainability and Chosen-Entity Viewing

#### [x] Extend chosen-entity inspection with top relationships, turning points, and public reputation

Review comment: Phase 2 only matters if observers can read it. The chosen-entity inspection panel must now answer: who matters to this entity, what changed its life, and how is it seen by others. Existing presenter/introspection foundations are the correct place to extend.

Technical implementation:

- extend inspection schemas to include:
  - top turning points
  - top relationships
  - public reputation summary

- presenters should select:
  - highest-salience turning points
  - top-N relationships by importance
  - compact reputation summary tags/scores

- do not return the full relationship map or full turning-point history

Files affected:

- `src/api/schemas.py`
- presenter modules for inspection/introspection
- possibly dedicated query service modules if inspection composition is split there

Important notes:

- this is a viewer feature, not a full debug dump
- choose relevance over completeness
- the panel should stay legible with a quick glance

---

#### [x] Add life-level “why changed” explanation output

Review comment: Phase 1 explains “why this action.” Phase 2 needs to explain “why this entity changed.” That means the inspection view should be able to say an entity became more fearful, more vengeful, or more loyal because of turning points and interpreted events.

Technical implementation:

- add a compact life-change explanation structure, for example:
  - recent turning point
  - affected motive
  - affected relationship
  - resulting current bias

- derive this from turning points and interpreted events rather than generating prose in core logic
- extend presenter/query code to surface top recent causal chains

Files affected:

- `src/api/schemas.py`
- inspection/AI presenter modules
- turning-point/interpreted-event helper modules

Important notes:

- keep this structured in Phase 2
- avoid freeform narrative text generation
- show causal chains, not just state snapshots

---

### Testing and Validation

#### [x] Add turning-point creation and pruning tests

Review comment: Turning-point memory needs tests or it will either flood with junk or never retain anything.

Technical implementation:

- add tests that verify:
  - salient interpreted events create turning points
  - low-value repeated routine events do not
  - turning-point caps and pruning rules work
  - old but still-salient events survive pruning

Files affected:

- new tests under unit/core/ai/narrative-related directories
- may need test helpers to fabricate interpreted events

Important notes:

- test salience behavior directly
- do not only test serialization

---

#### [x] Add interpreted-event and social-state update tests

Review comment: This is the core of the phase. Raw event -> interpreted event -> relationship/reputation/turning-point update needs at least a few end-to-end proofs.

Technical implementation:

- add integration tests for cases like:
  - ally dies nearby -> interpreted event -> fear/resentment/turning point update
  - actor avenges ally -> admiration/reputation update
  - actor flees dangerous fight -> cowardice/public meaning where visible

- verify the authoritative social-state application path, not just local helper outputs

Files affected:

- tests under integration/component/api as appropriate
- event interpreter test modules
- social-state update test modules

Important notes:

- one or two end-to-end tests are more valuable than many isolated unit tests
- prove causality, not just field mutation

---

#### [x] Add relationship-importance and reputation-visibility tests

Review comment: Bounded relationships and public/private separation are failure points. They need tests.

Technical implementation:

- add tests that verify:
  - relationship capacity/eviction works
  - top relationships are the ones surfaced
  - private events do not automatically become public reputation
  - indirect knowledge is weaker than direct knowledge

Files affected:

- tests for relationship helper/service
- tests for propagation/reputation logic
- presenter inspection tests

Important notes:

- public/private boundary mistakes will make the world feel fake fast
- relationship overflow bugs will ruin inspectability

---

#### [x] Add inspection-schema tests for turning points, relationships, and public reputation

Review comment: Chosen-entity viewing is a primary product surface, so the social-history output should be a tested contract.

Technical implementation:

- extend inspection tests to verify:
  - turning points appear
  - relationship summaries appear
  - reputation summaries appear
  - life-change explanation appears

- ensure outputs remain bounded and relevance-filtered

Files affected:

- `tests/api/test_introspection_api.py`
- presenter-specific tests under `tests/api/presenters/`

Important notes:

- verify relevance selection, not just presence
- this prevents the inspection surface from regressing into noise or disappearing

---

---

### Phase 2 Stage 3: Routine and Biological Needs [DONE]

#### [x] Implement authoritative biological decay (sleep, hunger)
Routines must be driven by internal states. entities will accumulate hunger and sleep debt over time, which will be managed by the `ActionSystem`.

Technical implementation:
- [x] Update `ActionSystem._apply_biological_decay` to increment `sleep_debt` and `hunger_level` per tick.
- [x] Implement forced sleep (passing out) if `sleep_debt` reaches 1.0.

#### [x] Implement EatAction and refine Sleep/Rest behavior
Entities need a way to reduce biological debt.

Technical implementation:
- [x] Create `src/actions/eat.py` to handle consumption of `CONSUMABLE` items.
- [x] Ensure `RestAction` transitions entities into the `is_sleeping` state if appropriate.

#### [x] Update AI Goal Scoring with biological biases
The AI must prioritize biological needs when they become critical.

Technical implementation:
- [x] Refine `SleepScorer` and `EatScorer` in `src/ai/goals/scorers.py`.
- [x] Use `RoutineService` to apply utility multipliers based on debt levels and time-of-day.

#### [x] Expose Routine state to Inspection API
Biological needs must be visible to the user.

Technical implementation:
- [x] Update `EntityPresenter` to correctly serialize `RoutineState` into `RoutineStateSchema`.

---

### Phase 2 Stage 4: Social Convergence & Narrative Causal Analysis [DONE]

#### [x] Proximity-based Gossip Propagation
Emergent information sharing between entities within proximity range.

Technical implementation:
- [x] Integrated `KnowledgePropagationService.propagate_gossip` into `ActionSystem`.
- [x] Reciprocal gossip triggers for entities within Manhattan distance 5.

#### [x] Authoritative Knowledge Merging with Confidence Decay
Ensure gossip is treated as indirect evidence with source-based confidence reduction.

Technical implementation:
- [x] Updated `ActionSystem._apply_updates` to use `BeliefService.merge_indirect_belief`.
- [x] Implemented source tracking and directness penalty for second-hand knowledge.

#### [x] Narrative Causal Explanation in API
Surface "Why" explanations for social bond changes in the inspection UI.

Technical implementation:
- [x] Extended `SocialBondSchema` and `AIDecisionSchema` with narrative impact fields.
- [x] Refactored `AIPresenter.get_explanation` to derive explanations from `TurningPointRecord` memory.

#### [x] Reputation Hardening
Ensure public reputation tags influence social appraisal logic.

Technical implementation:
- [x] Added reputation modifiers in `EventInterpreterService`.
- [x] Penalized trust gains for entities with "Ally-Slayer" or "BETRAYER" tags.

---

### Scope-Control Restraints for Phase 2

#### [x] Explicitly defer routines, household role systems, inheritance, and regional consequence from Phase 2

Review comment: The main risk to Phase 2 is mixing social meaning with full world-liveness systems. Those matter, but they are later-phase work. Phase 2 should stop at “social memory and turning-point meaning.”

Technical implementation:

- document deferred items in `implementation_plan.md`
- reject additions that require:
  - daily schedules
  - household economy
  - successor state
  - town-region consequence systems

- keep Phase 2 focused on life history, social bonds, and social knowledge

Files affected:

- `implementation_plan.md`

Important notes:

- do not sneak routines or households in “just for one case”
- scope discipline matters more here than extra breadth

---

## Priority Order

### Priority 1 — Social/History Core Models

1. Establish the Phase 2 implementation boundary
2. Add a typed turning-point memory model under the mind/narrative layer
3. Add salience and pruning rules for turning-point memory
4. Add a typed interpreted-event model that translates raw simulation events into social meaning
5. Add a typed bounded relationship model for important entities
6. Add a typed public reputation model at the entity and group-facing layer

### Priority 2 — Authoritative Meaning Pipeline

7. Add an event-interpretation service that consumes raw actions/traces and emits interpreted events
8. Route interpreted events into turning points, motives, and social state updates
9. Add relationship update rules driven by interpreted events and repeated interaction
10. Add reputation update rules from interpreted life events

### Priority 3 — Shared Knowledge and Inspection Payoff

11. Add a bounded social knowledge propagation mechanism for important threat and reputation information
12. Differentiate direct knowledge from indirect knowledge in belief records
13. Extend chosen-entity inspection with top relationships, turning points, and public reputation
14. Add life-level “why changed” explanation output

### Priority 4 — Validation and Scope Control

15. Add turning-point creation and pruning tests
16. Add interpreted-event and social-state update tests
17. Add relationship-importance and reputation-visibility tests
18. Add inspection-schema tests for turning points, relationships, and public reputation
19. Explicitly defer routines, household role systems, inheritance, and regional consequence from Phase 2

---

- bounded propagation of major threat/reputation knowledge

### Pass 4 — Inspection and explanation

- chosen-entity relationship/turning-point/reputation output
- life-change explanation output

### Pass 5 — Tests and scope discipline

- pruning/importance tests
- end-to-end meaning pipeline tests
- inspection contract tests
- deferred-scope lock-in

---

## Success Criteria for Phase 2

Phase 2 is successful when:

- some events now become durable turning points instead of disappearing into logs
- entities have a bounded set of socially meaningful relationships that influence later state
- public reputation exists separately from private memory
- actors can learn important things indirectly from others, but with weaker certainty than direct experience
- chosen-entity inspection can clearly show what changed this life, who matters, and how the world sees this entity
- observers can explain not just what the entity chose, but what happened that made it become this way

---

## Non-Goals for Phase 2

The following are explicitly deferred:

- daily/weekly routine simulation
- household/home-role anchoring systems
- inheritance/successor systems
- regional/world consequence simulation
- full rumor markets or large-scale information economies
- natural-language storytelling generation
- broad economy/settlement changes

---

## Priority Plan

What you must change in mindset or assumptions:
Phase 2 is not about adding more memory. It is about adding meaning filters so that a small number of events become socially and historically important.

What actions you must take immediately:
Implement typed turning points, interpreted life events, bounded relationships, and public reputation first; then add one authoritative pipeline that turns raw simulation outcomes into social-state changes; then expose the result in chosen-entity inspection.

What you must stop or eliminate:
Stop treating raw event logs as enough. Stop storing unlimited social state. Stop letting every witnessed action become public knowledge. Stop mixing this phase with routines, inheritance, or macro world consequence.

The consequences and opportunity cost if you fail to change:
You will keep a simulation that records a lot but remembers nothing important. Entities may have state, but they still will not have legible life history, social gravity, or meaningful change over time.
