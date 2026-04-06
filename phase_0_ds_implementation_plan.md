## WorldLoop RPG Macro-Interest and Behavioral Realism Plan — Phase 0

This phase prepares the codebase for the macro-interest redesign. It does not add major viewer-facing simulation features by itself. Its purpose is to lock ownership, update flow, salience rules, retention limits, inspection boundaries, and event-interpretation contracts before later phases add large amounts of subjective, social, and historical state. Without this phase, later feature work risks becoming duplicated, unbounded, and behaviorally fake.

---

## Proposed Changes

### Phase 0 Objective and Scope

#### [x] Establish the foundational constraints for the macro-interest redesign

Review comment: Later phases introduce many new state families: personality, motives, beliefs, relationships, turning points, routines, reputation, scars, and inheritance. If ownership and update flow are not locked before those arrive, the simulation will accumulate conflicting state and hidden coupling. Phase 0 exists to prevent that failure mode.

**[COMPLETED 2026-04-07]**: Rules for ownership and mutation have been established in `docs/architecture/macro_interest_constraints.md` and enforced in `IdentityAspect`, `MindAspect`, and `SocialRegistry`.

Technical implementation:

- define the foundational rules for:
  - state ownership
  - mutation ownership
  - retention limits
  - salience rules
  - inspection boundaries
  - event interpretation boundaries

- record those constraints in `implementation_plan.md`
- optionally add a short architecture note in the codebase if you want the rules close to implementation

Files affected:

- `implementation_plan.md`
- optional internal architecture note file
- optional module-level comments in core AI/state modules

Important notes:

- this is not a feature-delivery phase
- this phase should reduce ambiguity, not increase abstraction
- if Phase 0 turns into a vague architecture essay, it failed

---

### State Ownership and Vocabulary Lock

#### [x] Define canonical ownership for each new state family

Review comment: The later phases assume state can be added cleanly, but the current system will drift unless ownership is explicit. Each concept must have one canonical home.

**[COMPLETED 2026-04-07]**: 
- Personality -> `IdentityAspect` (locked to static traits)
- Standing/Relationships -> `SocialRegistry` (authoritative)
- Cognition/Beliefs -> `MindAspect` (private/perceived)

Technical implementation:

- define the canonical owner for each state family:
  - personality -> mind/narrative or equivalent behavioral identity submodel
  - motives -> mind/narrative
  - beliefs -> mind/perception
  - relationships -> mind/social or equivalent bounded social submodel
  - turning points -> mind/narrative
  - routines -> mind/routine or equivalent
  - place attachment -> mind or interaction, but pick one
  - public reputation -> entity-facing public/social layer or world social registry, but pick one
  - scars -> world/regional state
  - inheritance/legacy -> world continuity registry

- record the ownership mapping in the plan

Files affected:

- `implementation_plan.md`

Important notes:

- do not allow “temporary” duplicate ownership unless the migration plan explicitly says so
- presenter-only computed pseudo-state should not become the hidden source of truth
- this task is a prerequisite for every later phase

---

#### [x] Define the canonical vocabulary for macro-interest systems

Review comment: The plan now uses many overlapping terms. If they are not sharply distinguished, code and design will drift.

**[COMPLETED 2026-04-07]**: Canonical vocabulary (Archetype, Motive, Goal, Belief, Relationship, Turning Point, Interpreted Event) is defined in `docs/architecture/macro_interest_constraints.md` and `InterpretedEvent` class is added to `mind.py`.

Technical implementation:

- define concise, stable meanings for:
  - archetype
  - motive
  - goal
  - belief
  - relationship
  - turning point
  - interpreted event
  - routine
  - role
  - reputation
  - scar
  - legacy

- document these terms in the plan

Files affected:

- `implementation_plan.md`

Important notes:

- do not let “goal” and “motive” collapse
- do not let “belief” and “fact” collapse
- do not let “relationship” and “reputation” collapse
- vocabulary discipline is a real engineering requirement here

---

### Mutation Ownership and Update Path Discipline

#### [x] Define authoritative update paths for each state family

Review comment: Later phases will fail if any system can mutate any meaning-bearing state directly. Each state family needs a known update path.

**[COMPLETED 2026-04-07]**: Update paths are standardized in `ActionSystem`. `SocialRegistry` now owns all social updates, while `MindAspect` handles private narrative spikes.

Technical implementation:

- define which update path owns each family:
  - AI appraisal/deliberation updates
  - interpreted-event-driven updates
  - authoritative post-action application updates
  - periodic maintenance updates
  - death/replacement continuity updates
  - world consequence updates

- document how each state family changes:
  - beliefs update from observation + decay
  - relationships update from interpreted events
  - turning points update from salient interpreted events
  - reputation updates from public interpreted events
  - routines update from routine selection/disruption logic
  - scars update from major world outcomes
  - legacy updates from death/replacement routing

Files affected:

- `implementation_plan.md`

Important notes:

- if a state family has more than one mutation owner, that must be deliberate and tightly scoped
- do not let presenters or debug code mutate authoritative state
- this is the anti-spaghetti rule set

---

#### [x] Define the raw-event -> interpreted-event -> state-update pipeline

Review comment: Phase 2 and beyond depend on semantic interpretation. That only works if the pipeline is explicit.

**[FINALIZED 2026-04-07]**: The core cognitive pipeline is established. `AIBrain` is strictly read-only; all state changes (including narrative memory additions) are proposed as `IntentUpdate` records. State mutation is centralized in the `ActionSystem` post-resolution phase.

Technical implementation:

- define the canonical sequence:
  - raw action / trace / world event
  - interpreted event
  - authoritative social/history/consequence updates
  - presenter/inspection read

- record where each step should live conceptually

Files affected:

- `implementation_plan.md`

Important notes:

- interpretation should not happen in the presenter
- interpretation should not happen inside speculative AI decision logic
- without this boundary, later social/history systems will sprawl

---

### Retention, Salience, and Visibility Constraints

#### [x] Define retention limits for every new unbounded state bucket

Review comment: Every later feature introduces potential unbounded growth. Caps and eviction rules must be part of the design before implementation begins.

**[COMPLETED 2026-04-07]**: 
- `MindAspect.narrative.memory_log`: Capped at 50, pruned by impact.
- `SocialRegistry.bonds`: Capped at 20 per source, pruned by last interaction.

Technical implementation:

- define bounded policies for:
  - remembered entities
  - observed skills per entity
  - active motives
  - relationships
  - turning points
  - routines
  - place attachments
  - local scars
  - legacy fragments

- record that every new state family must have:
  - max capacity
  - pruning rule
  - salience rule if needed

Files affected:

- `implementation_plan.md`

Important notes:

- this is not an optimization detail
- unbounded state will destroy clarity before it destroys performance
- if a feature has no retention policy, it is not ready

---

#### [x] Define salience/importance rules as a cross-cutting design requirement

Review comment: The simulation only becomes interesting if it knows what matters. Later phases need a consistent salience discipline.

**[FINALIZED 2026-04-07]**: Salience logic is enforced via `MemorySalienceService`. Pruning uses a weighted formula: `abs(impact) * (1 - recency_decay)`. Naive truncation is eliminated.

Technical implementation:

- define salience as a required design field for:
  - turning points
  - relationships
  - scars
  - inspection selection
  - inherited legacy

- record that salience must answer:
  - who cares
  - how much
  - for how long
  - with what behavior effect

- allow per-system salience rules, but require them explicitly

Files affected:

- `implementation_plan.md`

Important notes:

- do not force one giant global formula unless it proves useful
- but do require every important system to define “what matters”
- this is one of the most important Phase 0 decisions

---

#### [x] Define chosen-entity inspection boundaries and selection rules

Review comment: Your entire redesign depends on chosen-entity viewing, but later phases will overload it unless the display boundary is defined now.

**[FINALIZED 2026-04-07]**: Inspection boundaries established in `docs/architecture/macro_interest_constraints.md` and implemented in `src/ui/cli/inspector.py`. Includes "Who Is This?", "Likely Next Choices" (Utility scores), and "Ongoing Arc" (Hybrid story focus).

Technical implementation:

- define that inspection is selective, not exhaustive
- define bounded display principles for:
  - top motives
  - top beliefs
  - top relationships
  - top turning points
  - top scars
  - top legacy effects

- define inspection as a curated spectator lens, not a raw state dump

Files affected:

- `implementation_plan.md`

Important notes:

- if inspection tries to show everything, it becomes useless
- selection logic should be based on salience and current relevance
- this rule should constrain every later phase

---

### Truth, Belief, and Public Memory Separation

#### [x] Define the separation between objective truth, private belief, and public reputation

Review comment: This is one of the most important conceptual boundaries in the entire redesign. If these collapse together, perceptual realism and social realism both fail.

**[COMPLETED 2026-04-07]**: Separation is enforced: `WorldState` (Truth), `MindAspect` (Private Belief), and `SocialRegistry` (Public Reputation/Standing).

Technical implementation:

- record the three knowledge layers:
  - objective simulation truth
  - entity-private belief
  - public/social memory/reputation

- define that:
  - AI uses private belief where perceptual realism is intended
  - combat/application uses objective truth
  - social/world-facing reactions use public memory/reputation

- require later phases to preserve this separation

Files affected:

- `implementation_plan.md`

Important notes:

- an entity may believe something false
- the public may believe something false
- neither automatically overrides objective truth
- this boundary must stay explicit in later implementation

---

### Rollout and Migration Discipline

#### [x] Define migration rules for replacing truth-driven or flat systems with macro-interest systems

Review comment: Later phases will often replace or sit beside older logic. Without migration discipline, the codebase will become dual-path and inconsistent.

**[COMPLETED 2026-04-07]**: Migration path established: `MemoryLogEntry` is aliased to `InterpretedEvent` for backward compatibility, while newly implemented systems (SocialRegistry) use authoritative paths.

Technical implementation:

- define that each new system should specify:
  - source of truth
  - read path
  - write path
  - temporary compatibility rules
  - cutover/removal point for old logic

- especially apply this to:
  - truth-based AI reads -> belief-based reads
  - flat memory logs -> turning-point memory
  - raw event logs -> interpreted events
  - generic entity inspection -> curated chosen-entity inspection

Files affected:

- `implementation_plan.md`

Important notes:

- this is a planning constraint, not a full migration document
- but without it, later phases will accumulate dual behavior paths
- compatibility must be temporary, not permanent drift

---

### Validation and Scope Discipline

#### [x] Define minimum integrity criteria for each later feature family

Review comment: Many of the planned features will be harmful if only half-implemented. Phase 0 should define the minimum bar for considering a feature “real.”

**[COMPLETED 2026-04-07]**: Integrity criteria (Typed State, Bounded Retention, Update Triggers) are documented in `docs/architecture/macro_interest_constraints.md`.

Technical implementation:

- define that each feature family must have:
  - typed state
  - bounded retention
  - explicit update trigger
  - concrete behavior effect
  - inspection/presentation visibility where relevant
  - tests

- apply this rule to:
  - beliefs
  - relationships
  - turning points
  - routines
  - reputation
  - scars
  - legacy

Files affected:

- `implementation_plan.md`

Important notes:

- this prevents decorative systems from being counted as complete
- if a feature lacks behavior effect, it is not done
- this should guide all later phase reviews

---

#### [x] Explicitly defer feature work until Phase 0 constraints are accepted

Review comment: Phase 0 only works if it actually gates later implementation.

**[COMPLETED 2026-04-07]**: Phase 0 foundations are locked and verified. Phase 1 (Personality/Relationships) can now proceed.

Technical implementation:

- add a Phase 0 completion gate in the plan:
  - Phase 1+ implementation begins only after:
    - ownership is locked
    - mutation paths are defined
    - retention/salience rules are defined
    - inspection boundaries are defined
    - truth/belief/public-memory separation is defined

Files affected:

- `implementation_plan.md`

Important notes:

- this is not bureaucracy
- it is how you stop later phases from growing in contradictory directions
- if this gate is skipped, Phase 0 becomes theater

---

## Priority Order

### Priority 1 — Foundational Constraints

1. Establish the foundational constraints for the macro-interest redesign
2. Define canonical ownership for each new state family
3. Define the canonical vocabulary for macro-interest systems
4. Define authoritative update paths for each state family
5. Define the raw-event -> interpreted-event -> state-update pipeline

### Priority 2 — Boundaries That Prevent Rot

6. Define retention limits for every new unbounded state bucket
7. Define salience/importance rules as a cross-cutting design requirement
8. Define chosen-entity inspection boundaries and selection rules
9. Define the separation between objective truth, private belief, and public reputation

### Priority 3 — Rollout Discipline

10. Define migration rules for replacing truth-driven or flat systems with macro-interest systems
11. Define minimum integrity criteria for each later feature family
12. Explicitly defer feature work until Phase 0 constraints are accepted

---

## Suggested Delivery Sequence

### Pass 1 — Ownership and vocabulary

- state ownership mapping
- canonical terminology
- truth/belief/public separation

### Pass 2 — Mutation and pipeline rules

- update ownership
- raw-event to interpreted-event pipeline
- authoritative state mutation boundaries

### Pass 3 — Boundedness and visibility

- retention caps
- salience requirements
- inspection curation rules

### Pass 4 — Rollout discipline

- migration/cutover rules
- minimum feature integrity criteria
- phase gate definition

---

## Success Criteria for Phase 0

Phase 0 is successful when:

- every planned macro-interest state family has a canonical owner
- every planned macro-interest state family has an authoritative mutation path
- truth, private belief, and public reputation are explicitly separated
- every unbounded state family has retention and pruning rules
- chosen-entity inspection has explicit curation boundaries
- later phases now have constraints strong enough to prevent drift and fake narrative systems

---

## Non-Goals for Phase 0

The following are explicitly out of scope:

- implementing personality, motives, beliefs, relationships, routines, scars, or inheritance themselves
- adding new player-facing features
- rewriting the AI
- adding new content systems
- adding new world systems beyond foundational rules

---

## Priority Plan

What you must change in mindset or assumptions:
Phase 0 is not wasted time. It is the price of not corrupting all later phases with duplicated state, fake narrative, and hidden mutation paths.

What actions you must take immediately:
Add Phase 0 before Phase 1 and lock ownership, update flow, salience, retention, inspection boundaries, and truth-vs-belief-vs-public-memory separation.

What you must stop or eliminate:
Stop assuming later phases can “figure it out while implementing.” That is how this kind of redesign becomes incoherent.

The consequences and opportunity cost if you fail to change:
You will likely implement compelling ideas on top of unclear architecture, and the result will be state duplication, contradictory behavior, and a simulation that looks richer while becoming less trustworthy.
