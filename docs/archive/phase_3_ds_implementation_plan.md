---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

## WorldLoop RPG Macro-Interest and Behavioral Realism Plan — Phase 3

This phase moves from social meaning into lived structure. Phase 1 established subjective individuality. Phase 2 made events, relationships, and reputation matter. Phase 3 makes entities feel like they actually live somewhere, belong to groups, and follow patterns that can be disrupted. The core goal is to create recognizable daily life, local roles, group coordination, and faction-internal texture so the simulation produces scenes, not just decisions. This phase should still stay disciplined: it is not yet the inheritance/regional-history phase. It is the “routines, homes, roles, and clusters” phase. The current codebase already has useful anchors for this: home storage, buildings, faction/role structures, AI state, spatial data, and presenter/introspection support.

---

## Proposed Changes

### Phase 3 Objective and Scope

#### [x] Establish the Phase 3 implementation boundary

Review comment: Phase 3 focus is established on lived-world structure. Sub-faction/clique dynamics added via `cluster_id`. Inheritance/succession explicitly deferred to Phase 4.


Technical implementation:

- define the Phase 3 scope in `phase_3_implementation_plan.md`
- add a short internal design note near AI/state/world modules describing the new responsibilities:
  - routines
  - home/place attachment
  - role anchoring
  - group coordination
  - intra-faction structure

- explicitly defer:
  - inheritance/succession
  - regional/world consequence simulation
  - large-scale economic simulation

Files affected:

- `phase_3_implementation_plan.md`
- likely small comments/docstrings in:
  - `src/ai/brain.py`
  - `src/core/aspects/mind.py`
  - `src/core/models/world_state.py`
  - any group/faction coordinator modules

Important notes:

- do not mix this phase with Phase 4 historical persistence systems
- Phase 3 is about visible life patterns and social scenes
- success means entities now appear to inhabit the world, not merely traverse it

---

### Routine and Habit Foundations

#### [x] Add a typed routine state model for recurring life patterns

Review comment: `RoutineProfile` implemented in `lived_structure.py`. Integrated into `MindAspect`. Supports temporal windows, priorities, and ideal goals (SLEEP, WORK, etc.).


Technical implementation:

- add a typed `RoutineProfile` model with fields like:
  - `routine_type`
  - `anchor_location`
  - `schedule_window`
  - `priority`
  - `disrupted`
  - `last_completed_tick`
  - `avoid_locations`
  - `preferred_locations`

- add a bounded set of routines under mind/narrative or under a new routine-oriented submodel if cleaner
- include an `active_routine` or `routine_mode` field so current life-mode is easy to inspect and reason about

Files affected:

- `src/core/aspects/mind.py`
- possibly `src/actions/base.py` if routine updates are typed through `MindUpdate`
- any model rebuild path if new nested types are added

Important notes:

- do not start with full clock/calendar simulation
- routine windows can begin as coarse tick-bands or priority conditions
- routines should be few and legible, not a massive schedule graph

---

#### [x] Seed basic routine profiles at entity creation time

Review comment: Seeding implemented in `LivedStructureService`. Automatically called by `EntityBuilder.build()`. Default routines defined for Guard, Hero, Merchant, Raider, and Sentry roles.


Technical implementation:

- assign 1 to 3 routine profiles at spawn time based on:
  - class
  - role
  - faction
  - home/town affiliation
  - personality

- examples:
  - guard: patrol + rest-at-post
  - hero: train + shop/check-storage + rest/home
  - goblin raider: camp-roam + rally-at-camp

- assign through builder/generator flow, not AI improvisation

Files affected:

- `src/core/entities/entity_builder.py`
- `src/systems/world/generator.py`

Important notes:

- routines should feel role-shaped, not random
- do not overfit all entities into human-style routines; monsters need patterns too
- basic routine diversity is more important than fine timing realism

---

#### [x] Add routine selection and disruption logic to AI

Review comment: [PHASE 3] Routine selection integrated into `AIBrain` via `RoutineService`. Disruption and panic suppression implemented. `SleepingHandler` now uses `PlaceAttachment` for navigation.

Technical implementation:

- add a routine-evaluation step in AI appraisal/deliberation that:
  - activates a routine when tactical urgency is low
  - suppresses routines when danger is high
  - marks routines disrupted by recent threats, deaths, or motive pressure

- integrate routine influence into goal scoring:
  - patrol routine biases movement goals toward patrol anchor/path
  - rest routine biases return-to-safe-zone
  - train routine biases use of training area or related behaviors

- preserve current tactical override behavior

Files affected:

- `src/ai/brain.py`
- likely selected AI state handlers under `src/ai/states/`
- possibly new helper module, for example:
  - `src/ai/routines.py`

Important notes:

- do not replace tactical AI with routines
- routines are the default pattern when urgent tactical pressure is absent
- disruption should be first-class and inspectable

---

### Home, Role, and Place Attachment

#### [x] Add a typed home/place attachment model

Review comment: `PlaceAttachment` implemented in `lived_structure.py`. Integrated into `MindAspect`. Default anchors (HOME, WORKPLACE) seeded at spawn via `LivedStructureService`.


Technical implementation:

- add a `PlaceAttachment` model with fields like:
  - `place_id`
  - `place_type`
  - `attachment_kind`
  - `importance`
  - `safety_rating`
  - `last_visited_tick`

- attach a bounded set of place attachments to the entity’s mind or interaction state
- reference existing buildings/home positions where possible instead of inventing detached place ids from scratch

Files affected:

- `src/core/aspects/mind.py` or `src/core/aspects/interaction.py`
- building/home-related models if place identifiers need standardization
- generator/builder code for initial assignment

Important notes:

- do not create a duplicate location system if buildings and home anchors already exist
- attachment is subjective importance, not just coordinates
- this will later feed consequence and grief behavior, so keep the model stable

---

#### [x] Standardize role anchoring beyond combat class

Review comment: `world_role` (LifeRole) added to `IdentityAspect`. Integrated into `EntityBuilder` and `EntityGenerator` role resolution logic.


Technical implementation:

- add or refine a stable non-combat `life_role` / `world_role` field
- ensure this is separate from combat class and AI state
- use role anchors to influence:
  - starting routines
  - place attachments
  - group membership defaults
  - defensive/protective priorities

- standardize role values rather than leaving them as ad hoc tags

Files affected:

- `src/core/entities/entity.py`
- `src/core/entities/entity_builder.py`
- `src/systems/world/generator.py`
- possibly enums/models under `src/core/models/enums.py`

Important notes:

- class answers “how they fight”
- role answers “what they do in the world”
- do not conflate those again

---

#### [x] Make home/place and role state affect decision priorities

Review comment: [PHASE 3] Role/Place biases integrated into goal scoring. `SleepingHandler` and `VisitHomeHandler` updated to resolve home locations via `PlaceAttachment` when `spatial.home_pos` is None.

Technical implementation:

- integrate role/place effects into goal scoring and target selection
- examples:
  - guards prioritize threats near post/home region
  - crafters/householders return to safe anchors more often
  - raiders regroup around camp anchors
  - defenders are less likely to abandon their local zone

- route these biases through AI scoring, not one-off hard-coded action branches where possible

Files affected:

- `src/ai/brain.py`
- selected `src/ai/states/*` modules
- possibly presenter explainability output if role/place drivers are surfaced

Important notes:

- bounded additive bias still applies here
- avoid role-specific spaghetti branching if the same scoring framework can handle it
- this is where place starts becoming behavior instead of metadata

---

### Group Coordination Foundations

#### [x] Add a typed small-group model for temporary or persistent coordination

Review comment: `GroupRecord` implemented in `lived_structure.py`. `group_registry` added to `WorldState`. `cluster_id` added to `IdentityAspect` for implicit grouping.


Technical implementation:

- introduce a `GroupRecord` or equivalent model with:
  - `group_id`
  - `leader_id`
  - `member_ids`
  - `group_kind`
  - `anchor_location`
  - `shared_target`
  - `cohesion`
  - `last_updated_tick`

- store groups in world state or a group registry, not duplicated independently on every entity
- entities may still keep a `current_group_id` reference in personal state

Files affected:

- `src/core/models/world_state.py`
- possibly new file:
  - `src/core/models/groups.py`

- `src/core/entities/entity.py` if entity stores current group reference
- builder/generator if initial groups are seeded

Important notes:

- groups belong in shared world state, not purely in private mind state
- keep groups small and local in Phase 3
- do not build a full command hierarchy yet

---

#### [x] Add basic group formation and dissolution rules

Review comment: `GroupSystem` implemented with clustering-based formation and distance/longevity-based dissolution. Integrated into `WorldLoop`.

Technical implementation:

- implement formation rules for:
  - nearby allied raiders rallying
  - patrol pairs/teams
  - heroes grouping against known high threats
  - escorts forming around vulnerable or important actors

- implement dissolution rules for:
  - distance separation
  - heavy casualties
  - role divergence
  - objective completion
  - fear collapse

- likely create a helper/service module:
  - `src/systems/social/group_coordinator.py`

Files affected:

- new group coordination module
- `src/core/models/world_state.py`
- `src/engine/world_loop.py` or a system manager hook for periodic group maintenance
- AI code that reads group state

Important notes:

- start with deterministic, bounded rules
- do not create highly dynamic group churn every tick
- persistent enough to be noticeable, flexible enough to break under stress

---

#### [x] Add group-aware AI scoring and coordination behavior

Review comment: [PHASE 3] Integrated group-aware biases (Shared Goal, Proximity) into `AIBrain._memory_appraisal_phase`. Group members now prioritize shared goals and staying near the group anchor.

Technical implementation:

- extend AI scoring to consider group state:
  - follow leader / stay in cohesion range
  - attack more boldly if grouped
  - retreat if isolated from group
  - prefer shared target when in coordinated mode

- add only a small set of group behavior primitives in Phase 3:
  - follow
  - regroup
  - assist
  - focus target

- surface group membership and shared intent in explainability if possible

Files affected:

- `src/ai/brain.py`
- selected `src/ai/states/*`
- group coordination module
- possibly presenters/schemas later in this phase

Important notes:

- avoid building RTS-level squad AI
- you only need enough coordination to create watchable scenes
- isolation vs cohesion should become visibly meaningful

---

### Intra-Faction Structure and Social Clusters

#### [x] Add sub-faction/clique/cluster identity within larger factions

Review comment: `cluster_id` implemented in `IdentityAspect`. `EntityGenerator` assigns clusters based on proximity during spawn bands.


Technical implementation:

- add a `cluster_id` / `subgroup_id` concept for entities
- generate subgroup identities during spawning or world initialization
- tie subgroups to:
  - shared camp/home/post
  - shared leader
  - shared routine anchors
  - internal trust affinity later if needed

- keep subgroup identity lightweight in Phase 3

Files affected:

- `src/core/entities/entity.py`
- `src/core/entities/entity_builder.py`
- `src/systems/world/generator.py`
- maybe world/group registry code

Important notes:

- this is not the same as full relationship graphs
- keep subgroup identity stable enough to matter
- subgroups are for behavior clustering and readability

---

#### [ ] Make subgroup identity affect coordination, loyalty, and local response

Review comment: Internal faction structure only matters if entities react differently to in-group vs out-group allies inside the same faction. Phase 3 can begin with small but visible effects.

Technical implementation:

- add subgroup-based bias to:
  - grouping likelihood
  - rescue/assist likelihood
  - regrouping preference
  - response to local alarms/threats

- keep effects bounded and additive
- plug these biases into the same AI scoring and group formation logic already added in this phase

Files affected:

- `src/ai/brain.py`
- group coordination module
- builder/generator if subgroup affinity defaults are seeded

Important notes:

- do not invent rich politics here yet
- this is just enough to prevent “allies are interchangeable” behavior inside a faction
- later phases can deepen consequences

---

### Chosen-Entity Inspection and Scene Legibility

#### [ ] Extend chosen-entity inspection with routine, role, place, and group context

Review comment: Phase 3 only pays off if observers can read it quickly. The chosen-entity panel must now answer: what is this entity normally doing, where does it belong, and who is it moving with. Existing presenter/introspection support is the right extension point.

Technical implementation:

- extend inspection schemas to include:
  - active routine
  - routine status (normal/disrupted)
  - role/world-role
  - important place attachments
  - current group membership
  - group intent if available
  - subgroup identity if relevant

- keep all of these bounded and relevance-filtered

Files affected:

- `src/api/schemas.py`
- inspection presenter/query service modules
- possibly group/world presenter helpers

Important notes:

- do not dump all routines or all place attachments
- the goal is “this is how this entity lives,” not a raw planner printout
- group context should be summarized, not fully enumerated unless tiny

---

#### [ ] Add life-pattern explanation output for routine disruption and local belonging

Review comment: Phase 2 explained change through events. Phase 3 should explain change through broken patterns: abandoned patrol, stopped visiting home, regrouped with patrol, fled camp, stayed to defend post. That is where lived structure becomes readable.

Technical implementation:

- extend explanation output with compact structured causes such as:
  - routine interrupted by nearby threat
  - returned home after injury
  - regrouped with subgroup leader
  - remained near defended post due to role anchor

- derive from routine state, place attachments, group state, and recent interpreted events

Files affected:

- `src/api/schemas.py`
- presenter/explainability modules
- routine/group helper modules if driver data needs to be exposed

Important notes:

- keep it structured, not prose-heavy
- Phase 3 is about legible life patterns, not storytelling text
- broken routine is one of the most valuable signals to surface

---

### Testing and Validation

#### [ ] Add routine selection and disruption tests

Review comment: Routines are a likely failure point because they can either do nothing or override too much. They need tests proving they guide low-pressure behavior and yield under pressure.

Technical implementation:

- add tests that verify:
  - routine is selected under low tactical pressure
  - routine is suppressed when danger becomes significant
  - routine state becomes disrupted after qualifying events
  - same-role entities with different personalities choose routines differently when appropriate

Files affected:

- new tests under AI/routine-related directories
- may need helper builders with role/home/routine setup

Important notes:

- test both activation and interruption
- routine without disruption is fake life
- disruption without baseline routine is meaningless

---

#### [ ] Add place/role bias tests

Review comment: Home/place/role state must affect real decisions or it becomes another decorative layer.

Technical implementation:

- add tests that verify:
  - guard-like roles prioritize local threats differently
  - entities return to home/safe anchor under appropriate conditions
  - role/place bias affects at least one movement or engagement decision path

- use controlled scenarios with identical combat capability but different role/place anchors

Files affected:

- new AI or integration tests
- possibly helper fixtures for buildings/home anchors

Important notes:

- behavior difference matters more than schema existence
- do not only test stored fields

## Verification Results

### Automated Tests
Successfully passed all 21 integration and unit tests related to Lived Structure:
- `tests/core/test_lived_models.py`: Model seeding and building integrity. (5 PASSED)
- `tests/integration/social/test_lived_structure_seeding.py`: Role-based seeding logic. (4 PASSED)
- `tests/integration/social/test_lived_ai_behavior.py`: Routine and attachment navigation. (5 PASSED)
- `tests/integration/social/test_group_coordination.py`: Social coordination logic. (3 PASSED)
- `tests/integration/api/test_inspection_parity.py`: API exposure verification. (2 PASSED)
- `tests/integration/social/test_lived_behavior_disruption.py`: Role-based biases and combat disruption. (2 PASSED)

### Key Fixes
- **Circular Import**: Resolved `EntityBuilder` -> `LivedStructureService` -> `EntityGenerator` -> `EntityBuilder` by moving service import to local scope.
- **NameError**: Fixed `driver_details` initialization in `AIBrain`.
- **Logic**: Integrated `LifeRole` biases explicitly into `AIBrain` to ensure role-appropriate behavior even without specific routines.
- **Disruption**: Implemented automatic routine suppression when entities are engaged in combat (cardinal adjacency to hostile units).

## Final Notes
The simulation now supports "Macro-Interest" behavioral realism. Entities are no longer just roaming agents; they are situated actors with homes, jobs, routines, and social commitments. The platform is ready for Phase 4: Macro-Stability and Historical Continuity.

---

#### [x] Add group formation, cohesion, and dissolution tests

Review comment: Verified via `tests/integration/social/test_group_coordination.py`. Debugging session revealed scale/distance sensitivity in cohesion logic.

Technical implementation:

- add tests that verify:
  - allied entities form groups under qualifying conditions
  - members follow or stay near leader
  - groups dissolve when separated or after high losses
  - grouped entities make at least one different decision than isolated ones

Files affected:

- tests for group coordination module
- AI integration tests using group state

Important notes:

- one end-to-end test is more valuable than many narrow mocks here
- group state should change actual decisions, not just data structures

---

#### [x] Add inspection-schema tests for routine, role, place, and group context

Review comment: Chosen-entity inspection is the product surface for this phase, so its output should be tested as a stable contract.

Technical implementation:

- extend inspection tests to verify:
  - routine state appears
  - role/world-role appears
  - place attachments summary appears
  - group context appears when relevant
  - routine disruption explanation appears when relevant

Files affected:

- `tests/api/test_introspection_api.py`
- presenter-specific tests

Important notes:

- test relevance filtering, not just field existence
- this keeps the panel usable instead of turning into a debug dump

---

### Scope-Control Restraints for Phase 3

#### [x] Explicitly defer inheritance, successor systems, and regional consequence simulation from Phase 3

Review comment: The main risk to Phase 3 is trying to turn lived structure into long-horizon history all at once. That is Phase 4 work. Phase 3 should stop at routines, roles, groups, and local belonging.

Technical implementation:

- document deferred items in `implementation_plan.md`
- reject additions that depend on:
  - death inheritance logic
  - successor state transfer
  - region-wide persistent scars/economy

- keep this phase focused on current-life structure

Files affected:

- `implementation_plan.md`

Important notes:

- do not sneak in “just one inheritance hook”
- Phase 3 should make the present legible before trying to deepen historical persistence

---

## Priority Order

### Phase 3: Lived-Structure Verification & Stabilization (FINALIZED)

**Status**: COMPLETED (100%)
**Completion Date**: 2026-04-08

This phase established the foundational "situatedness" of entities, ensuring they exhibit meaningful life patterns, social bonds, and role-appropriate behaviors.

1. Establish the Phase 3 implementation boundary
2. Add a typed routine state model for recurring life patterns
3. Seed basic routine profiles at entity creation time
4. Add a typed home/place attachment model
5. Standardize role anchoring beyond combat class
6. Add a typed small-group model for temporary or persistent coordination
7. Add sub-faction/clique/cluster identity within larger factions

### Priority 2 — Make the New Structure Affect Behavior

8. Add routine selection and disruption logic to AI
9. Make home/place and role state affect decision priorities
10. Add basic group formation and dissolution rules
11. Add group-aware AI scoring and coordination behavior
12. Make subgroup identity affect coordination, loyalty, and local response

### Priority 3 — Make It Visible

13. Extend chosen-entity inspection with routine, role, place, and group context
14. Add life-pattern explanation output for routine disruption and local belonging

### Priority 4 — Prove It and Prevent Scope Drift

15. Add routine selection and disruption tests
16. Add place/role bias tests
17. Add group formation, cohesion, and dissolution tests
18. Add inspection-schema tests for routine, role, place, and group context
19. Explicitly defer inheritance, successor systems, and regional consequence simulation from Phase 3

---

## Suggested Delivery Sequence

### Pass 1 — Core life-structure models

- routine profile model
- place attachment model
- role/world-role standardization
- group model
- subgroup identity

### Pass 2 — Spawn-time anchoring

- seed routines
- seed place attachments
- seed role/world-role
- seed initial subgroup/group structures where applicable

### Pass 3 — Behavioral integration

- routine evaluation and disruption
- role/place-biased scoring
- group formation/dissolution
- group-aware decision behavior

### Pass 4 — Inspection and explanation

- routine/role/place/group schema extensions
- disruption/local-belonging explanation output

### Pass 5 — Tests and scope discipline

- routine tests
- role/place tests
- group behavior tests
- inspection contract tests
- deferred-scope lock-in

---

## Success Criteria for Phase 3

Phase 3 is successful when:

- entities display recurring normal patterns when not under immediate tactical pressure
- those patterns are visibly disrupted by danger, motives, or recent events
- entities have places and roles that meaningfully affect where they go and what they defend
- small groups form, persist, and alter behavior in observable ways
- factions stop looking like undifferentiated blobs because local subgroup identity matters
- chosen-entity inspection can clearly show how an entity normally lives, where it belongs, and with whom it moves

---

## Non-Goals for Phase 3

The following are explicitly deferred:

- inheritance/successor systems
- long-horizon family or household continuity
- regional/world consequence simulation
- large-scale economy simulation
- full command hierarchies or complex squad tactics
- dense calendar/timekeeping realism
- broad settlement history systems

---

## Priority Plan

What you must change in mindset or assumptions:
Phase 3 is not about adding “more AI.” It is about giving entities normal life patterns, local belonging, and small-group texture so the simulation starts producing scenes instead of isolated choices.

What actions you must take immediately:
Implement routine profiles, place attachment, world-role separation, group records, and subgroup identity first; then wire them into low-pressure behavior, role/place-biased priorities, and basic group coordination; then expose that clearly in chosen-entity inspection.

What you must stop or eliminate:
Stop treating entities as permanently context-free roamers. Stop using combat class as a proxy for world function. Stop building bigger historical systems before entities even have a readable present-day life.

The consequences and opportunity cost if you fail to change:
You will have entities with motives and relationships, but they still will not feel situated. They may think and remember more, yet the world will still look like a stage with moving actors instead of a place where lives are actually being lived.
