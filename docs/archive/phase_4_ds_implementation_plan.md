---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

## WorldLoop RPG Macro-Interest and Behavioral Realism Plan — Phase 4

This phase moves from present-day lived structure into durable historical continuity and world consequence. Phase 1 made entities subjectively distinct. Phase 2 made events socially meaningful. Phase 3 made entities feel like they lived somewhere and belonged to groups. Phase 4 makes the world remember across deaths, recover imperfectly from damage, and carry consequences forward through households, successors, places, and regions. The core goal is to stop the simulation from feeling episodic. Actions should leave scars, recovery paths, inheritances, and altered local conditions that remain legible over time. The current codebase already has useful anchors for this: homes/buildings, storage, quests, factions, camps, world events, calamity/boss systems, typed updates, and inspection/introspection support.

---

## Proposed Changes

### Phase 4 Objective and Scope

#### [x] Establish the Phase 4 implementation boundary [TCK-20260409-PH4-STG1-CORE-MODELS]

Review comment: Phase 4 must stay focused on continuity and consequence. The correct slice is: successor/inheritance systems, local scars and recovery, regional consequence state, and long-horizon inspection of continuity. It is not the phase for adding a full economy sim, massive civilization management, or content-bloat quest trees.

Technical implementation:

- define the Phase 4 scope in `phase_4_implementation_plan.md`
- add a short internal design note near world-state/home/building/social-history modules describing the new responsibilities:
  - succession
  - inheritance
  - local scars
  - recovery
  - regional consequence
  - continuity inspection

- explicitly defer:
  - large-scale economy simulation
  - full settlement production chains
  - political diplomacy systems
  - global history generation beyond the scope of lived entities/regions

Files affected:

- `phase_4_implementation_plan.md`
- likely small comments/docstrings in:
  - `src/core/models/world_state.py`
  - `src/core/entities/entity.py`
  - building/home-related modules
  - any inspection presenter modules

Important notes:

- do not let Phase 4 become “simulate a whole kingdom”
- this phase is about persistence of consequence at the entity/household/local-region level
- success means lives and places now outlast single episodes

---

### Successor and Inheritance Foundations

#### [x] Add a typed successor/inheritance model for post-death continuity

Review comment: Right now death risks erasing too much identity and consequence. Phase 4 needs a typed continuity model that can transfer selected remnants of a life into a successor, home, household, or faction memory. Existing generation/home concepts make this feasible.

Technical implementation:

- add a typed `InheritanceRecord` or `SuccessorRecord` model with fields like:
  - `source_entity_id`
  - `successor_entity_id`
  - `inheritance_kind`
  - `tick`
  - `gear_transferred`
  - `reputation_transferred`
  - `motive_fragments`
  - `relationship_legacy`
  - `home_or_household_id`
  - `notes_tags`

- decide the stable storage location:
  - likely world/social-history registry rather than inside the dead entity

- add support for “no direct successor” cases where continuity flows to house/faction memory instead

Files affected:

- likely new file:
  - `src/core/models/continuity.py`

- `src/core/models/world_state.py`
- `src/core/entities/entity.py` only if living entities need successor references
- presenter/inspection modules later in this phase

Important notes:

- do not try to transfer every field from a dead entity
- inheritance must be selective and meaningful
- this system exists to preserve legible continuity, not to serialize corpses into descendants

---

#### [x] Define inheritance channels for gear, reputation, motives, and unresolved history

Review comment: “Inheritance” is too vague unless the transfer channels are explicit. Phase 4 needs clear rules for what can persist: heirlooms, house reputation, faction memory, grudges, unfinished arcs, and local notoriety.

Technical implementation:

- define explicit inheritance channels:
  - item/gear inheritance
  - home/storage inheritance
  - public reputation carryover
  - turning-point legacy tags
  - unresolved motive fragments
  - inherited fear/resentment targets in limited form

- implement each as typed transfer rules, not ad hoc mutation
- support partial degradation during transfer so inheritance is not exact cloning

Files affected:

- continuity model/service module
- item/storage/home modules
- reputation/social-memory modules from earlier phases
- motive/turning-point models in mind state

Important notes:

- inheritance should distort and compress, not copy perfectly
- “legacy of a life” is more interesting than “same state but new ID”
- keep inheritance bounded and selective

---

#### [x] Add successor assignment and fallback continuity routing

Review comment: Many entities will not have a clean biological or household successor. Phase 4 needs explicit routing rules for where continuity goes: direct successor, household, home, faction, town, or public memory.

Technical implementation:

- on qualifying death or replacement:
  - attempt direct successor assignment if that system exists
  - otherwise route legacy to:
    - household/home registry
    - faction/town memory
    - local public history

- define a priority order for legacy routing
- implement this in the authoritative death/replacement path, not in UI code

Files affected:

- likely death/application paths in:
  - `src/actions/combat.py`
  - `src/systems/gameplay/action_system.py`
  - world replacement/spawn systems

- continuity module
- world-state model

Important notes:

- this must hook into the authoritative life/death pipeline
- do not hide continuity routing inside presenters or helper-only logic
- fallback routing is mandatory or most deaths will still erase meaning

---

### Household, Home, and Persistent Local Anchors

#### [x] Add a typed household/home continuity model

Review comment: If continuity only attaches to individuals, the world still resets too fast. Homes and households should hold memory, storage, legacy status, and continuity hooks so places can remain meaningful when occupants change. Existing home storage/house concepts are the correct foundation.

Technical implementation:

- add a `HouseholdRecord` or equivalent with fields like:
  - `household_id`
  - `home_building_id`
  - `current_members`
  - `former_members`
  - `stored_heirlooms`
  - `household_reputation`
  - `legacy_tags`
  - `local_status`

- connect existing home buildings/storage to this record instead of treating them only as containers
- allow the household/home to become a continuity sink for inherited value

Files affected:

- building/home modules
- `src/core/models/world_state.py`
- possibly new `src/core/models/households.py`
- entity builder/generator if entities need household assignment

Important notes:

- this does not require full family simulation in Phase 4
- the point is persistent local anchor, not genealogy complexity
- household continuity should remain legible and compact

---

#### [x] Make home loss, damage, and recovery persist as meaningful local scars

Review comment: A home/post/camp being damaged should not just be a temporary numeric event. It should alter safety, attachment, routine stability, and continuity. Existing building and raid structures are the right foundation.

Technical implementation:

- extend building/home state to track:
  - damage severity
  - recovery stage
  - occupancy disruption
  - safety impact
  - legacy significance

- connect this to place attachments and routine disruption added in Phase 3
- use typed updates or centralized world mutation paths for these state changes

Files affected:

- building models and systems
- world object/world state modules
- AI/place/routine modules that read safety/attachment values
- inspection presenter modules

Important notes:

- damage should have medium-term impact, not just instant repair or permanent ruin by default
- visible local scars are one of the clearest forms of historical memory
- this is where “the world remembers” becomes spatially legible

---

### Local Scars, Recovery, and Medium-Term Consequence

#### [x] Add a typed local-scar model for medium-term world consequences

Review comment: The world needs consequences that persist long enough to matter but not forever clog the simulation. Phase 4 needs a first-class model for scars like recent raid damage, fear zones, supply disruption, boss devastation, or contested territory stress.

Technical implementation:

- add a `LocalScarRecord` model with fields like:
  - `scar_id`
  - `location_id` or region coordinates
  - `scar_kind`
  - `severity`
  - `created_tick`
  - `recovery_progress`
  - `behavioral_effects`
  - `public_visibility`

- store scars in world state or regional state, not on individual entities
- define bounded retention and cleanup behavior

Files affected:

- likely new file:
  - `src/core/models/local_scars.py`

- `src/core/models/world_state.py`
- any region/building/world-object systems that need to read scars

Important notes:

- scars are world-facing state, not just remembered events
- keep effects interpretable and bounded
- do not make every combat encounter create a scar; this is for meaningful local aftermath

---

#### [x] Add recovery mechanics for places, households, and regions

Review comment: Consequence without recovery produces dead accumulation. Recovery without consequence produces amnesia. Phase 4 needs explicit recovery tracks for damaged homes, scarred locations, disrupted routines, and regional danger.

Technical implementation:

- create recovery logic for:
  - damaged homes/buildings
  - local scar severity reduction
  - household stability recovery
  - safety normalization over time

- recovery can be influenced by:
  - successful defense
  - repair actions
  - time
  - faction presence
  - quest outcomes later in the phase

- place recovery updates in world/system tick paths, not in presentation logic

Files affected:

- building/world object systems
- world/system manager tick modules
- local scar models/services
- possibly routine/place-attachment systems if recovery changes behavior

Important notes:

- recovery should be neither automatic instant reset nor permanent freeze
- use staged recovery where possible
- partial recovery is often more interesting than all-or-nothing resolution

---

#### [x] Route major outcomes into local scars and recovery state

Review comment: Scar and recovery systems only matter if authoritative outcomes feed into them. Boss attacks, raids, building sabotage, repeated deaths, or liberation/defense events should leave local traces.

Technical implementation:

- hook into authoritative post-action or post-event paths to create/update scars from:
  - raids
  - boss/calamity events
  - sustained local combat
  - building destruction
  - local defense victories

- feed these effects into world state through a centralized mutation path
- reuse event interpretation output where possible to avoid duplicate logic

Files affected:

- `src/systems/gameplay/action_system.py`
- world/event systems
- local scar module
- building/world object systems
- possibly calamity/raid systems

Important notes:

- do not scatter scar creation across random action handlers
- one authoritative path keeps the world consequence layer trustworthy
- tie scar creation thresholds to meaningful events, not minor noise

---

### Regional Consequence and World-Memory State

#### [x] Add a typed regional consequence model for safety, pressure, and control shifts

Review comment: The world should not only remember at the single-building level. Regions should also retain medium-term state: safer, more dangerous, more contested, recently defended, recently devastated. Phase 4 needs a bounded regional consequence layer.

Technical implementation:

- add a `RegionConsequenceRecord` model with fields like:
  - `region_id`
  - `danger_level`
  - `stability`
  - `recent_defense`
  - `recent_devastation`
  - `occupancy_pressure`
  - `control_bias`
  - `last_major_change_tick`

- store in world state, keyed by region or derived territory id
- link with existing region/grid/building/faction concepts where available

Files affected:

- `src/core/models/world_state.py`
- region/grid/world modules
- possibly new file:
  - `src/core/models/regions.py`
  - or a consequence-specific module

Important notes:

- keep the first version compact and behavior-focused
- this is not full territory management yet
- the point is to make regions feel changed by recent history

---

#### [x] Make regional consequence state affect routines, spawning, and local choices

Review comment: Regional consequence must alter behavior or it is dead state. Phase 4 requires the world-memory layer to influence where entities go, what they avoid, how safe home feels, and how the region behaves over time.

Technical implementation:

- integrate regional consequence into:
  - routine disruption / route choice
  - local danger estimates
  - group rallying behavior
  - spawn weighting for local threats or defenders where appropriate

- use bounded additive effects, not hard overrides in most cases
- let routine/place/group systems from Phase 3 read this state

Files affected:

- `src/ai/brain.py`
- routine/place/group helper modules from Phase 3
- generator/spawn systems
- regional consequence modules

Important notes:

- this is where “the region changed” becomes visible to observers
- avoid rewriting all AI around regions; add clear local pressure signals instead
- start with a few high-value integrations

---

#### [x] Add quest and defense outcome hooks into regional consequence

Review comment: Quests and defense actions should stop being just payout machines. If a region was defended, neglected, liberated, or repeatedly raided, that should register in world-memory state.

Technical implementation:

- connect quest completions/failures and defense outcomes to:
  - regional stability
  - danger
  - defense memory
  - local scar severity

- implement this in authoritative quest/world-update paths, not in UI logic
- keep consequence mapping explicit and data-driven where practical

Files affected:

- quest systems/modules
- world loop or post-quest application paths
- regional consequence module
- local scar/recovery systems

Important notes:

- do not overbuild a quest engine here
- just ensure the world state changes when quests matter
- this is a key bridge from gameplay tasks to persistent world memory

---

### Chosen-Entity and Continuity Inspection

#### [x] Extend chosen-entity inspection with inherited legacy, household continuity, and place scars

Review comment: Phase 4 only matters if observers can see continuity across lives and places. The chosen-entity panel should now answer: what was inherited, what household/place history exists here, and what scars still shape this life.

Technical implementation:

- extend inspection schemas to include:
  - inherited legacy summary
  - household/home continuity summary
  - important local scars affecting the entity
  - regional condition summary

- show bounded, high-relevance entries only
- tie each summary to stable typed models, not freeform blobs

Files affected:

- `src/api/schemas.py`
- inspection/introspection presenters
- possibly dedicated continuity query service modules

Important notes:

- this is continuity inspection, not a full savefile dump
- prioritize what is actively shaping the current life
- make inherited continuity feel readable and concrete

---

#### [x] Add continuity explanation output for “why this life started this way”

Review comment: Earlier phases explain why an entity acted or changed. Phase 4 should explain why this entity began with certain burdens, legacy, attachments, or expectations. That is the real payoff of inheritance.

Technical implementation:

- add a compact structured explanation layer for:
  - inherited item or role legacy
  - inherited local reputation
  - inherited household damage or status
  - inherited motive fragments or unresolved threats

- derive from successor/inheritance records and household continuity state
- surface it in chosen-entity inspection without generating full prose narratives in core code

Files affected:

- `src/api/schemas.py`
- continuity presenter/introspection modules
- continuity models/services

Important notes:

- keep this causal and structured
- the goal is “this life starts under the shadow of X,” not story text generation
- this is one of the strongest reasons to build continuity at all

---

### Testing and Validation

#### [x] Add inheritance and successor-routing tests

Review comment: Continuity systems will silently fail unless transfer routing is tested explicitly. Death/replacement is a critical boundary.

Technical implementation:

- add tests that verify:
  - direct successor inheritance works when available
  - fallback routing to household/home/faction/public memory works when no successor exists
  - inheritance channels transfer only allowed fields
  - inheritance is selective, not exact cloning

Files affected:

- new tests under continuity/world/ai integration directories
- helper fixtures for death/replacement scenarios

Important notes:

- test routing priority, not just presence of records
- this is the main integrity point of the phase

---

#### [x] Add local-scar creation and recovery tests

Review comment: Local scar systems can easily become dead data unless the full create -> persist -> recover loop is tested.

Technical implementation:

- add tests that verify:
  - major events create scars
  - minor events do not
  - scars affect relevant local state
  - recovery progresses under the right conditions
  - scars eventually reduce or clear according to policy

Files affected:

- tests for local scar modules
- integration tests involving raids/buildings/defense outcomes

Important notes:

- test thresholds and decay
- if scars never matter or never recover, the system is broken

---

#### [x] Add regional consequence and quest-hook tests

Review comment: Regional memory is only valuable if gameplay outcomes actually change it.

Technical implementation:

- add tests that verify:
  - defense/loss/liberation outcomes alter regional consequence fields
  - those fields influence at least one later routine/spawn/AI bias
  - quest outcomes feed into regional state through authoritative paths

Files affected:

- quest/world/region integration tests
- AI or generator tests for reading regional consequence

Important notes:

- prove behavior changes, not just field mutation
- at least one end-to-end case should show “region changed, so life changed”

---

#### [x] Add inspection-schema tests for inheritance, scars, and continuity explanation

Review comment: Continuity is a viewer-facing payoff, not just backend state, so its inspection surface must be tested as a stable contract.

Technical implementation:

- extend inspection tests to verify:
  - legacy summaries appear when relevant
  - household/home continuity appears
  - local scar summaries appear
  - continuity explanation output appears

- ensure outputs remain bounded and relevance-filtered

Files affected:

- `tests/api/test_introspection_api.py`
- presenter-specific tests

Important notes:

- test relevance selection
- this prevents the continuity layer from becoming invisible or overwhelming

---

### Scope-Control Restraints for Phase 4

#### [x] Explicitly defer large-scale economy simulation, diplomacy, and civilization-level management from Phase 4

Review comment: The main risk to Phase 4 is inflation into a grand-strategy project. This phase is about continuity and consequence at the lived-world level, not total world governance simulation.

Technical implementation:

- document deferred items in `implementation_plan.md`
- reject additions that require:
  - full production chains
  - market equilibrium systems
  - diplomacy engines
  - civilization-level control simulation

- keep the phase focused on continuity, scars, recovery, and regional memory

Files affected:

- `implementation_plan.md`

Important notes:

- do not let persistent consequence become an excuse to simulate everything
- the target is emotional and observational continuity, not maximal system breadth

---

## Priority Order

### Priority 1 — Continuity Core Models

1. Establish the Phase 4 implementation boundary
2. Add a typed successor/inheritance model for post-death continuity
3. Define inheritance channels for gear, reputation, motives, and unresolved history
4. Add successor assignment and fallback continuity routing
5. Add a typed household/home continuity model
6. Add a typed local-scar model for medium-term world consequences
7. Add a typed regional consequence model for safety, pressure, and control shifts

### Priority 2 — Authoritative Consequence Pipeline

8. Make home loss, damage, and recovery persist as meaningful local scars
9. Add recovery mechanics for places, households, and regions
10. Route major outcomes into local scars and recovery state
11. Make regional consequence state affect routines, spawning, and local choices
12. Add quest and defense outcome hooks into regional consequence

### Priority 3 — Make Continuity Visible

13. Extend chosen-entity inspection with inherited legacy, household continuity, and place scars
14. Add continuity explanation output for “why this life started this way”

### Priority 4 — Prove It and Prevent Scope Drift

15. Add inheritance and successor-routing tests
16. Add local-scar creation and recovery tests
17. Add regional consequence and quest-hook tests
18. Add inspection-schema tests for inheritance, scars, and continuity explanation
19. Explicitly defer large-scale economy simulation, diplomacy, and civilization-level management from Phase 4

---

## Suggested Delivery Sequence

### Pass 1 — Core continuity and consequence models

- inheritance/successor model
- household continuity model
- local scar model
- regional consequence model

### Pass 2 — Authoritative routing and recovery

- successor assignment and fallback routing
- home loss/damage persistence
- scar creation hooks
- recovery mechanics

### Pass 3 — Regional world-memory integration

- regional consequence updates
- quest/defense hooks
- AI/spawn/routine readers of regional state

### Pass 4 — Inspection and explanation

- continuity inspection schema
- inherited-legacy summaries
- scar/region summaries
- continuity explanation output

### Pass 5 — Tests and scope discipline

- successor-routing tests
- scar/recovery tests
- region/quest consequence tests
- inspection contract tests
- deferred-scope lock-in

---

## Success Criteria for Phase 4

Phase 4 is successful when:

- death no longer erases all consequence because meaningful parts of a life persist through successors, households, or public memory
- homes, posts, and local places can carry scars and recovery states that visibly affect future lives
- regions retain bounded medium-term memory of defense, devastation, and danger
- quest and defense outcomes now change local and regional world state beyond rewards
- chosen-entity inspection can show inherited burden, local historical context, and why this life began under specific conditions
- observers can follow continuity across lives and places instead of watching isolated episodes

---

## Non-Goals for Phase 4

The following are explicitly deferred:

- full market/economy simulation
- diplomacy and treaty systems
- civilization-level strategic management
- expansive global history generation
- full family-tree genealogy simulation
- broad political content systems
- total settlement micromanagement

---

## Priority Plan

What you must change in mindset or assumptions:
Phase 4 is not about adding more world state for its own sake. It is about making consequence persist across death, damage, and recovery so lives and places stop resetting emotionally.

What actions you must take immediately:
Implement inheritance/successor records, household continuity, local scars, and regional consequence first; hook them into authoritative death/event/quest paths; then expose the result in chosen-entity inspection with concise continuity explanations.

What you must stop or eliminate:
Stop letting deaths, raids, and defenses evaporate into logs. Stop assuming persistence means infinite accumulation. Stop expanding this phase into economy, diplomacy, or total world governance systems.

The consequences and opportunity cost if you fail to change:
You will still have an impressive moment-to-moment simulation, but it will remain episodic. Entities may differ, remember, and belong somewhere, yet the world will still fail to carry enough consequence forward for observers to care deeply across long stretches of time.
