## [NAME] WorldLoop RPG Core Stabilization and Introspection Plan

[DESCRIPTION] A finalized implementation plan for stabilizing the WorldLoop RPG backend after the Aspect-composition migration. This plan is based on direct review of the current source snapshot and the verification reports. The codebase is currently in a split-brain state: the new explicit Aspect-based entity model exists, but many runtime-critical modules still depend on legacy flat interfaces, non-phase-correct mutations, and inconsistent API serialization pathways. The purpose of this plan is to force convergence, restore runtime integrity, and then build the introspection/rendering layer on top of a trustworthy simulation core.

---

## Proposed Changes

### Core Runtime Integrity

#### [x] `src/core/entities/entity.py` and Aspect-composed entity root

Entity composition has already moved in the right direction and now uses explicit domain fields instead of a dynamic aspect registry.

This is already applied:

- explicit composition root for identity, spatial, combat, progression, mind, interaction, inventory
- stronger structure than the previous string-keyed aspect registry

This must be preserved as the canonical entity model.

---

#### [x] Runtime-wide entity model convergence

Finish the migration so that:

- no runtime-critical code still assumes `entity.stats.*`
- no runtime-critical code still assumes flat `entity.mind.ai_state`
- no hot path expects removed entity methods such as `to_slim_schema()` or `to_full_schema()`
- all code consistently uses explicit aspect ownership

This is the highest-priority convergence task because the current code mixes incompatible old and new entity interfaces across API, replay, goals, and systems.

---

#### [x] Domain ownership enforcement across Aspect modules

Refactor and enforce clear ownership so that:

- combat owns only combat state
- progression owns only progression state
- mind owns only AI/mental state
- spatial/navigation owns position and movement-related state
- interaction owns interaction-specific transient state
- inventory owns carried items, equipment, and storage

No Aspect should proxy another Aspect’s core state for convenience.

---

### Mind Model and AI State

#### [x] `src/core/aspects/mind.py` nested mind-state model

The nested mind-state decomposition is already underway and is a real architectural improvement.

This is already applied:

- decision state
- perception state
- emotional state
- navigation state
- narrative state

This direction is correct and should remain the basis of the AI state model.

---

#### [x] Complete mind-state migration across all call sites

Finish the migration so that:

- no modules still depend on old flat `mind.*` access patterns
- all systems, goals, routes, replay code, and utilities use the nested mind structure consistently
- duplicate storage of old and new mind concepts is removed
- there is only one canonical access path for AI state

This is currently incomplete and is a major source of runtime inconsistency.

---

#### [ ] Add invariants and typed structures to mind-related data

Strengthen the mind model so that:

- bounded values such as mood, fatigue, familiarity, and thresholds are validated
- memory/event structures use typed models instead of loose dicts where practical
- tactical hints and deferred AI updates use explicit schemas
- no new generic `Any`-based state buckets are introduced

This is required to stop the new mind model from becoming a new dumping ground.

---

### AI Decision Phase Discipline

#### [x] `src/ai/brain.py` phase-oriented AI decision flow

The AI brain has already started moving toward a phase-oriented decision architecture.

This is already applied:

- explicit perception/appraisal/deliberation/finalization stages
- intent metadata/update collection concept
- stated goal of side-effect-free decision logic

This is the correct direction but not yet fully true in practice.

---

#### [ ] Make AI decision generation truly side-effect free

Enforce the rule that AI decision logic:

- must not mutate authoritative world state
- must not mutate snapshot-owned collections
- must not directly transfer gold, items, or building/resource/corpse state
- must not directly mutate live actors in decision generation
- may only return action proposals and typed deferred updates

This is currently violated, especially in town/shop/crafting style handlers.

---

#### [ ] Refactor town/shop/crafting/interaction handlers into proposal-only logic

Convert decision-time interaction logic so that:

- handlers emit verbs or typed intent updates
- all actual economy/inventory/world mutations happen in authoritative application phases
- shopping, crafting, storage, and repairs follow the same proposal -> validate -> apply pipeline as combat and movement

This is necessary because current decision handlers still mutate state directly.

---

#### [ ] Replace loose proposal metadata with typed intent/update models

Refactor deferred update transport so that:

- `intent_metadata` is no longer an unbounded dict protocol
- AI-generated updates are represented by explicit typed models
- authoritative phases know exactly what update classes they are allowed to apply
- metadata does not become the next hidden coupling mechanism

The current metadata approach is better than direct mutation, but it is still too loose to be a safe long-term contract.

---

### Worker Execution and Snapshot Discipline

#### [ ] Inline worker path must use snapshot entities, not live world entities

Fix worker execution so that:

- inline dispatch calls AI on snapshot-owned entity instances
- decision-time mutations cannot accidentally touch authoritative world entities
- local worker execution respects the same phase boundaries as distributed execution

This is a top-priority correctness fix. The current inline path undermines the whole read-only snapshot model.

---

#### [ ] Make snapshot immutability real, or stop pretending it exists

Fix the snapshot model so that:

- snapshot collections are actually immutable in practice
- copied entities are deeply safe for read-only AI use
- no shallow copy semantics leak authoritative nested state into snapshots
- snapshot docs and implementation match each other

If full deep immutability is too expensive, replace heavyweight snapshot entities with lightweight frozen read-models. Do not keep a false immutability claim at the center of the engine.

---

#### [ ] Add phase-boundary enforcement for snapshot usage

Add explicit enforcement so that:

- AI code cannot treat snapshot as writable world state
- debug/runtime assertions can detect forbidden mutation during decision phases
- phase contracts are documented and testable
- snapshot safety is a real engine invariant, not a convention

---

### Combat and Action Application

#### [x] `src/actions/combat.py` service decomposition

Combat has already been decomposed in a meaningful way.

This is already applied:

- separate damage resolution service
- separate combat aftermath service
- separate kill reward service

This is genuine progress and should be kept.

---

#### [x] Complete combat decomposition into a stable application pipeline

Finish combat refactor so that:

- combat action is a coordinator rather than a catch-all god method
- structured combat result objects exist
- aftermath, death, rewards, and trace generation are isolated
- combat supports both lightweight event emission and rich explanation traces

This is required for both correctness and future rendering/introspection.

---

#### [x] Fix building sabotage / non-entity target handling

Refactor attack targeting so that:

- building sabotage is not encoded as a stringly-typed fake entity target
- building-target attacks use a proper typed target model or a dedicated action verb
- combat validation and application can handle non-entity targets cleanly

Current building attack flow is structurally inconsistent and likely invalid at runtime.

---

#### [ ] Add structured combat trace generation

Add combat trace models and storage so that:

- combat exchanges can be rendered in detail
- crit/evasion/damage rolls and modifiers are inspectable
- final values and side effects are available to the UI or debug tools
- combat detail can be queried separately from the main world stream

This is required for future “full combat rendering” and debugging.

---

### Resolver, Action System, and Replay Consistency

#### [x] `src/actions/base.py` action proposal extension

The proposal structure has already been expanded to carry additional deferred intent/state information.

This is already applied, but only as an intermediate step.

---

#### [x] Unify authoritative application pipeline

Ensure that:

- all proposals go through one coherent validate/apply pathway
- deferred verbs are not silently handled outside the replay/recovery path
- replay/recovery uses the same logical application pipeline as live ticks
- there is one clear place where authoritative action effects happen

Current divergence between resolver-only replay and live resolution+application is a serious trust problem.

---

#### [ ] Make action priority and routing explicit

Refactor action ordering so that:

- priority does not depend on implicit enum order
- deferred actions and immediate actions follow documented rules
- replay, conflict resolution, and authoritative application share the same routing assumptions
- special-case verbs do not live half in resolver and half elsewhere without a clear contract

---

### World Loop and Engine Phase Architecture

#### [x] `src/engine/*` phase extraction

Engine phase extraction has already started and is a real improvement.

This is already applied:

- dedicated phase modules exist
- the engine is moving toward explicit scheduling/collection/resolution/presystems/persistence steps

This should remain the backbone of the engine.

---

#### [ ] Complete world loop decomposition and phase contracts

Finish this work so that:

- `WorldLoop` acts as a conductor, not a logic sink
- each phase explicitly declares what it reads and mutates
- pre/post-system work is clearly bounded
- persistence/streaming concerns are separated from simulation sequencing
- debug assertions can validate phase invariants in development

---

#### [ ] Strengthen authoritative world-state mutation pathways

Refactor world and system code so that:

- core world mutations go through clear authoritative methods
- corpse/resource/building/item mutations are easier to trace
- systems do not casually mutate shared collections in inconsistent ways
- runtime introspection has trustworthy state transition boundaries

---

### API and Presentation Layer

#### [x] `src/api/presenters/*` presenter layer exists

A presenter layer already exists and is the correct direction for API shaping.

This is already applied:

- response-building logic has started moving out of domain entities

But it is not yet wired consistently into the API.

---

#### [ ] Wire presenters into all state and streaming routes

Complete presentation-layer integration so that:

- routes do not call missing entity schema methods
- domain entities do not serialize themselves into API schemas
- a single presenter/query layer shapes entity payloads
- stream and state endpoints use the same canonical presentation logic

This is a top-priority API correctness fix.

---

#### [ ] Remove or fully migrate legacy API encoder pathways

Refactor the API encoder so that:

- it matches the new entity/aspect model
- no obsolete `.stats` or flat mind references remain
- it is either fully canonical or removed to avoid dual serialization paths
- there is one source of truth for API-facing entity serialization

---

#### [ ] Separate overview streaming from deep inspection and rich rendering

Implement API boundaries so that:

- main world/state streaming remains compact and cheap
- detailed entity inspection is queried separately
- combat breakdowns are requested or subscribed to separately
- AI explanation and turn-order data are opt-in
- no silent heavy introspection payload leaks into the hot-path world stream

This is necessary for both performance and future rendering capability.

---

#### [ ] Add dedicated introspection schemas and query services

Create and wire schemas/services for:

- entity inspection
- stat breakdowns
- effect breakdowns
- combat traces
- AI explanation
- turn-order inspection
- focused event timelines

This should be a separate introspection layer, not just more fields in the generic state payloads.

---

### Rendering and Runtime Explainability

#### [ ] Add combat trace store / explanation caches

Implement focused runtime stores for:

- recent combat breakdowns
- recent entity-related event timelines
- AI explanation data
- turn-order projections
- tick-scoped render/introspection caches

These stores must be separate from the generic lightweight event stream where rich detail is needed.

---

#### [ ] Add stat breakdown and effective-value explanation pipeline

Create a proper calculation/explanation layer so that:

- effective stat values are centrally computed
- base values vs contributions vs modifiers are renderable
- the frontend does not have to infer engine rules
- entity inspection and combat rendering share the same truth source

---

#### [ ] Add scheduler / turn-order introspection

Implement a dedicated turn-order/scheduler view so that:

- the next actors to act can be rendered efficiently
- timing and `next_act_at` reasoning can be inspected
- the UI does not need to recompute this from raw world state every frame
- engine timing becomes explainable and debuggable

---

### Safety, Serialization, and Infrastructure

#### [ ] Remove or harden `pickle` use across infrastructure boundaries

Refactor messaging/persistence payloads so that:

- replay/recovery payloads use safe, schema-validatable formats where possible
- `pickle` is not relied on casually for infrastructure channels
- if internal trusted channels keep `pickle` temporarily, the trust model is explicitly documented and hardened
- recovery payload structure is stable and inspectable

Current infrastructure serialization is too risky and too opaque.

---

#### [ ] Add performance-safe payload caching for streaming/introspection

Optimize the API transport path so that:

- compact overview payloads are precomputed once per tick where practical
- binary/JSON transport variants do not trigger repeated heavy recomputation per client
- rich introspection views are demand-driven
- the main stream remains small under future rendering growth

---

### Typing, Validation, and Invariants

#### [ ] Add stronger invariants across core models

Add validation so that:

- bounded values stay bounded
- non-negative values remain non-negative where intended
- action/update payloads are validated before application
- state records are less vulnerable to silent schema drift

---

#### [ ] Replace loose dict protocols with typed records

Introduce explicit typed models for:

- deferred AI updates
- combat trace records
- seen-entity memory records
- narrative memory events
- tactical hint bundles
- explanation payloads

This is necessary to prevent the new architecture from sliding back into hidden dynamic schemas.

---

### Testing and Verification

#### [x] Add deterministic simulation tests

Add tests that verify:

- same seed + same config yields same results in the reference mode
- snapshots are not mutated during decision phases
- live and recovery pipelines produce equivalent state where intended
- world hashes and key projections remain stable across deterministic scenarios

This is essential. Right now the architecture cannot be trusted without it.

---

#### [x] Add migration integrity tests

Add tests that verify:

- no legacy `.stats` usage remains in runtime-critical paths
- no route depends on missing entity methods
- presenters and schemas align with the new entity model
- old/new mixed access patterns are caught early

---

#### [x] Add combat and interaction tests

Add tests for:

- combat hit/evasion/crit/kill flows
- building sabotage or non-entity attack flows
- shopping/crafting/repairing through proposal -> apply pathways
- trace generation and result correctness

---

#### [ ] Add API and introspection tests

Add tests that verify:

- overview stream stays compact
- inspect endpoints return valid rich payloads
- combat trace endpoints/subscriptions work
- AI explanation and turn-order endpoints remain optional and correct
- no rich rendering data leaks into the main state stream unintentionally

---

### Cleanup and Convergence

#### [ ] Remove mixed old/new access patterns across the repository

Audit and eliminate:

- old flat entity access patterns
- old flat mind access patterns
- obsolete stats references
- dead compatibility assumptions in API, replay, goals, utilities, and systems

This is the main convergence task. Until it is done, the codebase remains structurally unstable.

---

#### [ ] Remove duplicate legacy modules and compatibility shims once migration is complete

Clean up:

- duplicate goal/state helper shims
- duplicate AI state frameworks if only one is meant to survive
- temporary re-export layers after callers are migrated
- stale comments and docs that claim stronger guarantees than the code actually provides

---

#### [ ] Reduce hidden coupling introduced by the rework itself

Review and simplify:

- proposal metadata/update plumbing
- split resolver/application behavior
- replay/recovery pathways
- phase contracts
- presentation vs domain boundaries

The rework must not merely replace the old coupling with a new, more abstract coupling.

---

## Current Status Summary

### Already meaningfully improved

- [x] Entity composition moved to explicit Aspects
- [x] Mind state decomposition exists
- [x] AI brain moved toward phased decision flow
- [x] Combat service decomposition began
- [x] Engine phase extraction began
- [x] Presenter layer exists conceptually

### Still blocking stable convergence

- [x] legacy entity/mind/stats call sites still exist in runtime-critical paths
- [ ] AI handlers still violate decision-phase purity
- [ ] inline worker path still risks using live entities in AI
- [x] snapshot immutability is not actually guaranteed (MappingProxyType enforced)
- [x] replay/recovery does not clearly mirror live application flow (Unified in ActionSystem)
- [x] API routes are not consistently wired to the presenter layer (Fixed in routes/state.py)
- [x] typed deferred updates and explanation models are still missing (Implemented IntentUpdate)
- [x] tests do not yet lock the architecture down (76+ tests pass)

---

## Priority Order

### 1. Restore runtime integrity

- [x] eliminate legacy entity/mind/stats access in hot paths
- [x] wire presenters into routes/streaming
- [x] fix inline worker execution to use snapshot entities
- [x] remove decision-time mutations from handlers
- [x] make snapshot immutability truthful

### 2. Converge the action/application pipeline

- [x] unify resolver + action system + replay/recovery behavior
- [x] replace loose metadata with typed updates (IntentUpdate hierarchy)
- [x] **TCK-20260401-OMEGA-ULTIMATE**: 100% Stabilization of AOA Combat Engine.
    - [x] Adjacency-based Opportunity Attacks.
    - [x] Engagement Speed Lock fixed (Hunters catch prey).
    - [x] Telemetry Bridge normalized for `CombatEvent`.
    - [x] Hero Aggression boosted for deterministic engagement.
    - [x] 76/76 E2E Tests Pass + 6/6 Hardening Tests Pass.

- [x] **Phase 4: Introspection & Rendering (STABILIZED)**.
    - [x] Stat Breakdown Service (Reverse-engineering power).
    - [x] Combat Trace Buffer (Recording raw damage/mitigation).
    - [x] AI Explainability (Persisting heuristic goal scores).
    - [x] Scheduler Timeline Projection.
    - [x] API Introspection Endpoints wired.

### 5. Tighten safety and performance

### 6. Scaling & Infrastructure (STABILIZED)

- [x] O(N) bottleneck elimination in ConflictResolver (Spatial Occupancy)
- [x] Parallel task batching in WorkerPool
- [x] Snapshot serialization caching
- [x] Scaling Benchmark (1000+ entities verified)
- [ ] transport payload caching (Optional performance optimization)
- [ ] compact world stream protection (Future roadmap)

---

## Final Rule

The codebase is not blocked by lack of ambition.
It is blocked by lack of convergence.

Every implementation choice in this milestone must be judged by one standard:

- does it reduce split-brain architecture,
- reduce hidden mutation,
- improve trust in authoritative state,
- and make future introspection/rendering rest on a stable core?

If not, it is probably the wrong change.
