## WorldLoop RPG Macro-Interest and Behavioral Realism Plan — Phase 1

This phase turns the design shift into an actual implementation slice. The goal is not to build the full living-world stack yet. The goal is narrower: make entities observably different, make them reason from belief instead of hidden truth in selected decision paths, and make that visible when inspecting a chosen entity. The current codebase already has the right structural footholds for this: nested mind state, typed updates, staged AI, and presenter/introspection support.

---

## Proposed Changes

### Phase 1 Objective and Scope

#### [x] Establish the Phase 1 implementation boundary

Review comment: Phase 1 will fail if it tries to absorb relationships, rumors, routines, inheritance, and regional consequence all at once. The correct first slice is: personality/archetype, long-term motives, belief-based target knowledge, and chosen-entity inspection. Everything else is deferred.

Technical implementation:

- define the Phase 1 scope in `phase_1_ds_implementation_plan.md`
- add a short internal design note near the AI/mind modules describing the four new responsibilities:
  - personality
  - motives
  - beliefs
  - chosen-entity inspection

- explicitly mark out-of-scope systems as deferred in the plan so they do not creep into this phase

Files affected:

- `phase_1_ds_implementation_plan.md`
- likely a small module-level docstring or comment block in:
  - `src/ai/brain.py`
  - `src/core/aspects/mind.py`

Important notes:

- do not create placeholder models for future relationship or rumor systems in this stage
- do not let Phase 1 become “macro systems lite”
- success for this task is clean boundaries, not code volume

---

### Personality and Archetype Foundations

#### [x] Add a typed personality profile model under the mind layer

Review comment: The simulation currently has class, faction, role, AI state, and emotion, but still lacks a stable behavioral identity layer that explains why similar entities choose differently. This belongs under mind, not objective identity.

Technical implementation:

- extend the mind-side model with a typed `PersonalityProfile`
- store:
  - `archetype`
  - `aggression`
  - `greed`
  - `caution`
  - `loyalty`
  - `ambition`
  - `curiosity`

- attach it under `mind.narrative` unless you want a clean new submodel like `mind.identity_model`; for Stage 1, extending `narrative` is lower-risk
- add validators/clamps for scalar values so the profile cannot drift into nonsense ranges
- ensure the model participates in Pydantic rebuild if needed by the existing circular rebuild flow

Files affected:

- `src/core/aspects/mind.py`
- possibly `src/actions/base.py` if new typed mind update fields are needed
- any model-rebuild helper that resolves forward refs for mind-related types

Important notes:

- keep trait count small; 5 to 6 meaningful axes are enough
- do not add twenty sliders that never influence decisions
- archetype should be readable, but scalar traits should be what actually drive behavior
- this must be structured state, not `metadata` or loose dict payloads

---

#### [x] Seed personality and archetype at entity creation time

Review comment: Personality must exist before the first decision tick. If it is invented later by AI code, it becomes fake retrospective flavor instead of a life-shaping seed.

Technical implementation:

- update entity creation/builder flow to assign:
  - one `archetype`
  - initial scalar trait values

- bias defaults by:
  - role
  - faction
  - class
  - tier

- retain randomness so entities of the same class are not clones
- seed through the builder/generator layer, not AI

Files affected:

- `src/core/entities/entity_builder.py`
- `src/systems/world/generator.py`
- possibly any direct constructor shortcuts used in tests or calamity generation
- tests that construct entities directly may need helper defaults

Important notes:

- same-class entities must diverge at spawn time
- do not hard-map class to archetype; that creates predictable caricatures
- mobs need personality too, not just heroes, or the world stays one-sided
- boss personality can be more deterministic

---

### Long-Term Motive Foundations

#### [x] Add a typed long-term motive model under the mind/narrative layer

Review comment: Current goals are too transient and `life_directive`-style state is too thin. Stage 1 needs a persistent motive model that survives across many ticks and biases short-term choices.

Technical implementation:

- add a typed `PersonalMotive` model with:
  - `motive_id`
  - `kind`
  - `priority`
  - `progress`
  - `frustration`
  - `active`
  - optional target entity/location reference

- attach `motives: list[PersonalMotive]` under `mind.narrative`
- add validation rules:
  - bounded motive count
  - bounded priority/progress/frustration ranges

- motives should be persistent state, not recomputed each tick

Files affected:

- `src/core/aspects/mind.py`
- possibly `src/actions/base.py` if motive-updating transport is added later in Stage 1
- any AI explanation schema that will expose motives

Important notes:

- hard-cap active motives at 2 to 4
- motives are not the same as per-tick goals
- do not allow free-form strings here; typed motive kinds matter for later scoring and inspection
- frustration exists so later stages can change behavior when motives are blocked

---

#### [x] Seed initial motives at entity creation time

Review comment: Motives must exist from the beginning or entities still start as generic tactical shells. Spawn-time motive seeding is what creates early divergence in life direction.

Technical implementation:

- assign 1 to 2 motives at spawn time
- choose from weighted motive sets based on:
  - archetype
  - class/role
  - faction
  - home/town affinity if available

- examples:
  - greedy scavenger hero: `build_wealth`
  - cautious guard: `seek_safety` plus `serve_faction`
  - aggressive warrior: `prove_strength`

- use builder/generator assignment, not runtime AI improvisation

Files affected:

- `src/core/entities/entity_builder.py`
- `src/systems/world/generator.py`

Important notes:

- motive selection should be weighted, not deterministic
- do not create long motive lists
- motives should be inspectable and stable enough to matter

---

### Belief-Based Perception Foundations

#### [x] Add a typed belief record model for other entities

Review comment: Existing memory/perception is useful, but it still trends too close to fact cache rather than actor belief. Stage 1 needs a first-class subjective record of what an entity thinks it knows about another entity.

Technical implementation:

- introduce a typed belief record to replace or extend the current memory entry structure for entity-memory
- include fields like:
  - `entity_id`
  - `last_seen_tick`
  - `last_seen_pos`
  - `apparent_kind`
  - `apparent_faction`
  - `apparent_role`
  - `visible_weapon`
  - `visible_injury`
  - `threat_estimate`
  - `observed_skills`
  - `confidence_score`
  - `fear_bias`
  - `respect_bias`
  - `stale_ticks`

- migrate `mind.perception.entity_memory` to store this belief-oriented structure
- update any serializers/validators that expect the old record shape

Files affected:

- `src/core/aspects/mind.py`
- `src/actions/base.py` because `PerceptionUpdate` currently validates `entity_memory`
- any presenter reading memory state
- any AI code reading entity memory

Important notes:

- this model stores beliefs, not truth
- do not expose exact HP, exact stats, or full skill lists here
- keep this bounded by remembered-entity count if necessary later; Phase 1 can start with current storage behavior if it is already bounded enough

---

#### [x] Add a typed threat-estimate submodel with explicit confidence handling

Review comment: A single vague threat number is not enough. The actor needs a structured estimate and an explicit measure of certainty. Otherwise the AI will either ignore the uncertainty or treat guesses like truth.

Technical implementation:

- add a `ThreatEstimate` submodel with at least:
  - `overall`
  - `survivability`
  - optional `melee` / `ranged` in Phase 1 if cheap enough
  - `confidence` or a separate scalar confidence field

- use a simple enum or scalar banding for confidence:
  - low
  - medium
  - high
    or a float with thresholds

- reference this from the belief record

Files affected:

- `src/core/aspects/mind.py`
- `src/actions/base.py` if perception update coercion must recognize the new nested structure

Important notes:

- do not build a full statistical inference system
- the estimate only needs to be good enough to generate understandable mistakes
- confidence decay is as important as confidence increase

---

#### [x] Add a belief-refresh service for observation-to-belief updates

Review comment: Belief mutation logic will become unmaintainable if scattered across brain stages and state handlers. Phase 1 needs one dedicated place that transforms observation into updated belief.

Technical implementation:

- create a new AI utility/service module, for example:
  - `src/ai/beliefs.py`

- add functions such as:
  - refresh belief from direct observation
  - estimate visible injury band from observed condition
  - update threat estimate from observed outcomes
  - record observed skill usage
  - decay stale confidence

- keep heuristics simple:
  - weapon seen -> adjust apparent combat style
  - heavy observed damage -> raise threat
  - target survives strong attack -> raise survivability estimate
  - repeat sightings -> increase confidence
  - long absence -> reduce confidence

Files affected:

- new file: `src/ai/beliefs.py`
- `src/ai/brain.py` to call it
- possibly tests for this service

Important notes:

- this service should not return exact truth-mirror records
- do not bury these heuristics in `AIBrain` directly
- this module is one of the most important units for future tuning

---

### AI Integration for Personality, Motives, and Beliefs

#### [x] Wire personality bias into goal scoring

Review comment: Personality is worthless if it only appears in inspection. The current AI already computes goal scores, so that is the right place to apply bounded personality bias.

Technical implementation:

- add a personality-bias pass to AI scoring
- likely insertion points:
  - in `src/ai/brain.py` during appraisal/deliberation
  - or in goal-evaluation helpers if those are already separated

- apply additive score modifiers:
  - caution -> flee/rest
  - greed -> loot/resource actions
  - aggression -> hunt/engage
  - ambition -> tolerate higher threat
  - curiosity -> explore/wander

- preserve existing base score calculations, then bias them

Files affected:

- `src/ai/brain.py`
- any goal-evaluation helper modules the brain delegates to
- possibly `src/actions/base.py` if decision drivers are stored in typed updates

Important notes:

- additive only; do not hard-script personalities to force outcomes
- if the weights are too weak, behavior stays generic
- if the weights are too strong, entities become cartoonishly predictable
- same-class divergence is the benchmark

---

#### [x] Wire long-term motives into goal scoring

Review comment: Motives must bend short-term decision-making or they are just labels. They should bias current goal selection, not replace it.

Technical implementation:

- add a motive-bias pass after baseline goal scoring
- examples:
  - `build_wealth` -> loot/trade/resource behavior
  - `seek_safety` -> flee/regroup/rest
  - `prove_strength` -> challenge/hunt/combat
  - `serve_faction` -> faction-aligned goals
  - `explore` -> movement/exploration when idle

- keep the effect bounded and additive
- optionally record which motive contributed how much for explainability

Files affected:

- `src/ai/brain.py`
- any goal-scoring helper modules
- possibly `src/actions/base.py` if you add typed decision-driver fields

Important notes:

- motives should change tie-breaks and ambiguous decisions most strongly
- do not let motives completely override immediate survival unless that is an intentional archetype effect later
- keep the mapping between motive kinds and supported goal types explicit and readable

---

#### [x] Refresh belief records during the sensory/perception stage

Review comment: The belief system must start where the actor sees the world. The current perception pass should stop behaving like a simple fact refresh and instead update subjective belief state.

Technical implementation:

- in the perception stage of `AIBrain`:
  - iterate visible/attended actors
  - call the new belief-refresh service
  - write updated belief records into `PerceptionUpdate.entity_memory`

- update fields such as:
  - visible injury band
  - visible weapon
  - apparent role/style
  - threat estimate
  - confidence growth
  - observed skill evidence when relevant

- keep compatibility with the existing typed `PerceptionUpdate`

Files affected:

- `src/ai/brain.py`
- `src/actions/base.py` for `PerceptionUpdate` coercion/validation
- `src/core/aspects/mind.py`

Important notes:

- refresh beliefs only from actual observation, not hidden state leakage
- if an entity is not currently observed, do not silently refresh its record with current truth
- do not overcomplicate visibility logic in Phase 1; use existing visibility/perception flow

---

#### [x] Age and degrade beliefs during appraisal/memory maintenance

Review comment: Beliefs that never decay become delayed omniscience. Uncertainty has to return when the actor stops seeing the target.

Technical implementation:

- in the memory/appraisal stage:
  - increment staleness
  - lower confidence on stale records
  - degrade visible condition certainty
  - keep observed-skill history but mark it as old if necessary

- do this via typed updates if the current architecture expects AI-side writes to come back as updates

Files affected:

- `src/ai/brain.py`
- `src/ai/beliefs.py`
- `src/actions/base.py` if new fields are needed in `PerceptionUpdate`

Important notes:

- stale beliefs should remain beliefs, not be discarded immediately
- confidence decay must be slow enough to preserve continuity but real enough to restore uncertainty
- this is important for believable re-encounters

---

#### [x] Replace selected omniscient decision paths with belief-based decision inputs

Review comment: This is the integrity test of the stage. If the AI still reads exact hidden target state everywhere that matters, the whole belief system is a cosmetic fraud. Phase 1 does not need total migration, but it needs a few visible end-to-end paths.

Technical implementation:

- identify 2 to 4 high-visibility decision points and migrate those first:
  - attack vs flee
  - chase vs disengage
  - loot vs abort
  - approach vs hesitate

- replace direct use of exact opponent stats in those paths with:
  - `belief.threat_estimate`
  - `belief.visible_injury`
  - `belief.confidence`
  - `belief.observed_skills`

- keep authoritative truth in combat execution itself; the migration target is AI choice, not combat resolution

Files affected:

- `src/ai/brain.py`
- likely AI state handlers under `src/ai/states/` that currently use direct target data
- maybe helper modules used by flee/hunt/loot logic

Important notes:

- do not try to purge all truth-based reads in Phase 1
- choose a few important decisions and make those honest
- this task is more important than adding extra data fields

---

### Chosen-Entity Inspection and Explainability

#### [x] Extend entity inspection schemas with personality, motives, and important beliefs

Review comment: If the chosen-entity view does not show the new subjective state, there is no product payoff. Existing inspection/presenter infrastructure is already the correct place to extend. Phase 1 goal is legibility.

Technical implementation:

- extend inspection schemas to include:
  - personality profile
  - active motives
  - a bounded set of important beliefs

- choose the most relevant beliefs by:
  - highest threat
  - nearest known danger
  - strongest confidence
  - most recently observed major actor

- do not dump the full memory table

Files affected:

- `src/api/schemas.py`
- `src/api/presenters/entity_presenter.py` or whichever presenter builds inspection payloads
- any introspection route or query service returning inspection payloads

Important notes:

- readability matters more than exhaustiveness
- this is a chosen-entity panel, not a debug memory dump
- if the inspection view becomes too dense, the whole design shift loses visibility

---

#### [x] Add decision-driver explanation fields for personality, motives, and beliefs

Review comment: The chosen-entity view must not only show state. It must show why that state mattered to the current decision. Otherwise the observer still sees data without narrative logic.

Technical implementation:

- add a small typed decision-driver structure, either:
  - inside existing AI explanation data
  - or as new fields on a typed `MindUpdate`

- store compact contributions such as:
  - `trait:greed`
  - `motive:build_wealth`
  - `belief:enemy_12_high_threat`

- surface only the top drivers for the chosen action

Files affected:

- `src/actions/base.py` if adding typed decision-driver fields
- `src/ai/brain.py`
- `src/api/presenters/ai_presenter.py` or inspection presenter path
- `src/api/schemas.py`

Important notes:

- do not generate prose in Phase 1
- structured driver records are enough
- this is explainability, not storytelling yet

---

### Testing and Validation

#### [x] Add behavioral divergence tests for same-class entities with different personalities

Review comment: The first real proof of value is visible divergence, not richer data models. Two same-class entities in the same scenario should not always make the same choice once personality exists.

Technical implementation:

- add tests that construct two same-class entities with:
  - different archetypes
  - different scalar traits

- place them in the same world conditions
- assert different score preferences or different chosen proposals for at least one scenario

Files affected:

- likely new tests under:
  - `tests/unit/ai/`
  - or existing AI/introspection test directories

- may need helper builders in test support code

Important notes:

- the test should check behavior, not just stored fields
- this is the fastest way to catch “personality exists but does nothing”

---

#### [x] Add belief-update and belief-decay tests

Review comment: The belief system is only credible if it updates when entities observe things and decays when they stop.

Technical implementation:

- add tests for:
  - first observation creates/updates a belief record
  - repeated observation raises confidence
  - observed skill use is recorded
  - stale time lowers confidence or certainty
  - at least one migrated decision path uses belief rather than direct truth

Files affected:

- new tests under AI or core/perception test directories
- possibly integration-style tests that step the brain and action system together

Important notes:

- one end-to-end test is more valuable than many isolated field tests
- include at least one wrong or uncertain case to prove imperfection exists

---

#### [x] Add inspection-schema tests for personality, motives, beliefs, and decision drivers

Review comment: The chosen-entity view is part of the actual product goal, so its schema and presence should be tested as a stable contract.

Technical implementation:

- extend inspection tests to verify:
  - personality appears
  - motives appear
  - important beliefs appear
  - decision drivers appear when available

- ensure the output is bounded and does not expose raw full memory tables by accident

Files affected:

- `tests/api/test_introspection_api.py`
- possibly presenter-specific tests under `tests/api/presenters/`

Important notes:

- test for content shape and presence, not just serialization success
- this prevents the chosen-entity payoff from regressing silently

---

### Scope-Control Restraints for Stage 1

#### [x] Explicitly defer relationships, rumors, routines, inheritance, and regional consequence from Phase 1

Review comment: This is a planning task, but it is necessary. The main technical threat to Phase 1 is scope dilution. These systems matter, but not yet.

Technical implementation:

- document these as explicit non-goals in the plan
- reject model additions that are only placeholders for later systems
- reject AI wiring that depends on unfinished relationship or rumor infrastructure
- keep Phase 1 focused on subjective individual state and selected decision integration

- **Deferred Systems**:
  - `Relationships`: No complex social graph or kinship tracked yet.
  - `Rumors`: No propagation of second-hand information; entities only believe what they've seen.
  - `Routines`: No daily cycles or sleep/hunger simulation in Phase 1.
  - `Inheritance`: No lineage or successor logic.
  - `Regional Consequence`: No global map influence or town-wide impact tracking.

Files affected:

- `implementation_plan.md`

Important notes:

- placeholder complexity is still complexity
- stage_1_implementation_plan.md should be phase_1_ds_implementation_plan.md or removed
- Phase 1 should ship observable individuality first, not future architecture hints

---

## Priority Order

### Priority 1 — Foundation Models

1. Establish the Phase 1 implementation boundary
2. Add a typed personality profile model under the mind layer
3. Seed personality and archetype at entity creation time
4. Add a typed long-term motive model under the mind/narrative layer
5. Seed initial motives at entity creation time
6. Add a typed belief record model for other entities
7. Add a typed threat-estimate submodel with explicit confidence handling
8. Add a belief-refresh service for observation-to-belief updates

### Priority 2 — Make the New State Affect Behavior

9. Wire personality bias into goal scoring
10. Wire long-term motives into goal scoring
11. Refresh belief records during the sensory/perception stage
12. Age and degrade beliefs during appraisal/memory maintenance
13. Replace selected omniscient decision paths with belief-based decision inputs

### Priority 3 — Make It Visible

14. Extend entity inspection schemas with personality, motives, and important beliefs
15. Add decision-driver explanation fields for personality, motives, and beliefs

### Priority 4 — Prove It and Prevent Scope Drift

16. Add behavioral divergence tests for same-class entities with different personalities
17. Add belief-update and belief-decay tests
18. Add inspection-schema tests for personality, motives, beliefs, and decision drivers
19. Explicitly defer relationships, rumors, routines, inheritance, and regional consequence from Phase 1

---

## Suggested Delivery Sequence

### Pass 1 — Data and API scaffolding

- personality profile model
- motive model
- belief record model
- threat estimate/confidence model
- spawn-time seeding
- inspection schema expansion

### Pass 2 — Belief update mechanics

- belief-refresh service
- perception-stage belief refresh
- appraisal-stage stale decay

### Pass 3 — Decision integration

- personality goal-score bias
- motive goal-score bias
- selected belief-based decision-path migration

### Pass 4 — Explainability and tests

- decision-driver explainability fields
- divergence tests
- belief update/decay tests
- inspection contract tests

---

## Success Criteria for Phase 1

Phase 1 is successful when:

- same-class entities can behave differently under the same conditions because personality and motives differ
- entities use belief rather than exact hidden truth in at least a few important decision paths
- beliefs strengthen through observation and weaken with staleness
- a chosen-entity inspection view can clearly show who the entity is, what it wants, what it believes, and why it chose its action
- observers can follow one entity and see more than class, stats, and combat log

---

## Non-Goals for Phase 1

The following are explicitly deferred:

- full relationship graph
- rumor or shared-knowledge systems
- daily/weekly routine systems
- household/social anchoring systems
- public reputation systems
- inheritance/successor systems
- regional consequence simulation
- formula refinement work that does not change visible behavior

---

## Priority Plan

What you must change in mindset or assumptions:
Phase 1 is not about adding more lore-shaped data. It is about adding persistent subjective state that actually changes decisions and becomes visible in inspection.

What actions you must take immediately:
Implement typed personality, motive, belief, and threat models first; seed them at spawn; add a dedicated belief-refresh service; migrate a few important decision paths to beliefs; expose all of that in chosen-entity inspection; then prove it with behavior and inspection tests. This completes Phase 1.

What you must stop or eliminate:
Stop letting AI silently reason from exact hidden truth in the exact places where this phase claims to add perceptual realism. Stop adding future-stage placeholder systems. Stop treating inspect-only flavor as completed behavior work.

The consequences and opportunity cost if you fail to change:
You will get a richer schema and the same old simulation. The entity panel will look more sophisticated, but the world will still feel fake because the actors will remain interchangeable and secretly omniscient.
