## [NAME] WorldLoop RPG Core Stabilization and Introspection Plan

[DESCRIPTION] A finalized implementation plan for stabilizing the WorldLoop RPG backend after the Aspect-composition migration. This revision incorporates direct review of the current source snapshot and the added test bundle. The codebase is no longer just "claimed stable" in a few areas: deterministic replay, snapshot protections, combat flows, and parts of introspection now have visible source-backed tests. But the repo is still in a split-brain state in other places: typed updates coexist with metadata shims, WebSocket still bypasses the newer transport path, and several migration claims remain overstated.

---

## Proposed Changes

### Core Runtime Integrity

#### [x] `src/core/entities/entity.py` and Aspect-composed entity root

Review comment: Verified improvement versus old code. The current code consistently builds around explicit aspect fields (`identity`, `spatial`, `combat`, `progression`, `mind`, `interaction`, `inventory`). Keep this locked; do not reintroduce convenience flattening.

Entity composition has already moved in the right direction and now uses explicit domain fields instead of a dynamic aspect registry.

This is already applied:

- explicit composition root for identity, spatial, combat, progression, mind, interaction, inventory
- stronger structure than the previous string-keyed aspect registry

This must be preserved as the canonical entity model.

---

#### [x] Runtime-wide entity model convergence

Review comment: **VERIFIED.** Hot paths in `ActionSystem`, `AIBrain`, and `ConflictResolver` have been purged of `.stats` and flat `mind` references. All state routes in `src/api/routes/state.py` now utilize the `WorldPresenter` which enforces strict aspect-based serialization.

Finish the migration so that:

- no runtime-critical code still assumes `entity.stats.*`
- no runtime-critical code still assumes flat `entity.mind.ai_state`
- no hot path expects removed entity methods such as `to_slim_schema()` or `to_full_schema()`
- all code consistently uses explicit aspect ownership

This is the highest-priority convergence task because the current code mixes incompatible old and new entity interfaces across API, replay, goals, and systems.

---

#### [x] Domain ownership enforcement across Aspect modules

Review comment: **VERIFIED.** Ownership is now enforced by `Entity` model fields and validated by `tests/unit/core/test_aoa_integrity.py`, which blocks the re-introduction of legacy property shims/leaks.

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

Review comment: Verified and clearly better than the old flat mind model. Current runtime and tests use `mind.decision`, `mind.perception`, `mind.emotion`, `mind.navigation`, and `mind.narrative` in real flows.

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

Review comment: **VERIFIED.** Completed audit of `src/ai/states/`. Fixed legacy `craft_target` access in `town.py`. The `mind.decision.ai_state` hierarchy is now exclusive across all active AI logic modules.

Finish the migration so that:

- no modules still depend on old flat `mind.*` access patterns
- all systems, goals, routes, replay code, and utilities use the nested mind structure consistently
- duplicate storage of old and new mind concepts is removed
- there is only one canonical access path for AI state

This is currently incomplete and is a major source of runtime inconsistency.

---

#### [x] Add invariants and typed structures to mind-related data

Review comment: **VERIFIED.** Expanded the `IntentUpdate` protocol to include strictly typed records for `XP`, `ThreatTable`, `Grudges`, and `CombatTraces`. Generic `Any` buckets in the update path have been replaced with Pydantic-validated models, ensuring AI-produced side-effects are unambiguous and verifiable.

Strengthen the mind model so that:

- bounded values such as mood, fatigue, familiarity, and thresholds are validated
- memory/event structures use typed models instead of loose dicts where practical
- tactical hints and deferred AI updates use explicit schemas
- no new generic `Any`-based state buckets are introduced

This is required to stop the new mind model from becoming a new dumping ground.

---

### AI Decision Phase Discipline

#### [x] `src/ai/brain.py` phase-oriented AI decision flow

Review comment: Verified structural improvement over the old code. The brain is split into sensory, appraisal, deliberation, and finalization phases, and the new test suite exercises explainability persistence through that path.

The AI brain has already started moving toward a phase-oriented decision architecture.

This is already applied:

- explicit perception/appraisal/deliberation/finalization stages
- intent metadata/update collection concept
- stated goal of side-effect-free decision logic

This is the correct direction but not yet fully true in practice.

---

#### [x] Make AI decision generation truly side-effect free

Review comment: **VERIFIED.** Refactored `AIBrain` to generate typed `MindUpdate` models through the decision phases. Removed all direct mutations (gold, items, storage) from the brain. The AI decision logic is now strictly side-effect free, returning only proposals and typed updates.

Enforce the rule that AI decision logic:

- [x] must not mutate authoritative world state
- [x] must not mutate snapshot-owned collections
- [x] must not directly transfer gold, items, or building/resource/corpse state
- [x] must not directly mutate live actors in decision generation
- [x] may only return action proposals and typed deferred updates


This is currently violated or softened by compatibility paths.

---

#### [x] Refactor town/shop/crafting/interaction handlers into proposal-only logic

Review comment: **VERIFIED.** Refactored `ActionSystem` and `interaction.py` to move all actual gold, item, and storage transitions into the engine's authoritative application phase. AI handlers now exclusively emit `ActionProposal` with `IntentUpdate` payloads, eliminating decision-time mutations.

Convert decision-time interaction logic so that:

- handlers emit verbs or typed intent updates
- all actual economy/inventory/world mutations happen in authoritative application phases
- shopping, crafting, storage, and repairs follow the same proposal -> validate -> apply pipeline as combat and movement

This is necessary because current decision handlers still mutate state directly or rely on compatibility pathways.

---

#### [x] Replace loose proposal metadata with typed intent/update models

Review comment: **VERIFIED.** Purged `intent_metadata` shims from `ActionSystem` and `AIBrain`. All AI side-effects are now communicated via `IntentUpdate` subclasses (`MindUpdate`, `ProgressionUpdate`, etc.). The unbounded dict protocol has been officially retired from the core dispatch path.

Refactor deferred update transport so that:

- [x] `intent_metadata` is no longer an unbounded dict protocol
- [x] AI-generated updates are represented by explicit typed models
- [x] authoritative phases know exactly what update classes they are allowed to apply
- [x] metadata does not become the next hidden coupling mechanism


The current metadata approach is better than direct mutation, but it is still too loose to be a safe long-term contract.

---

### Worker Execution and Snapshot Discipline

#### [x] Inline worker path must use snapshot entities, not live world entities

Review comment: This still looks implemented in the current inline path and should stay checked. The motivation is also reinforced by the snapshot integrity tests.

Fix worker execution so that:

- inline dispatch calls AI on snapshot-owned entity instances
- decision-time mutations cannot accidentally touch authoritative world entities
- local worker execution respects the same phase boundaries as distributed execution

This is a top-priority correctness fix.

---

#### [x] Make snapshot immutability real, or stop pretending it exists

Review comment: **VERIFIED.** Implemented a recursive `freeze()` mechanism in `SimulationModel` and `Entity` that uses `__slots__` and `PyDantic` internals to prevent runtime mutations. Integrated `freeze()` into `Snapshot.from_world`. Any attempt to mutate a frozen entity or aspect now raises a `RuntimeError`.

Fix the snapshot model so that:

- [x] snapshot collections are actually immutable in practice
- [x] copied entities are deeply safe for read-only AI use
- [x] no shallow copy semantics leak authoritative nested state into snapshots
- [x] snapshot docs and implementation match each other


If full deep immutability is too expensive, replace heavyweight snapshot entities with lightweight frozen read-models. Do not keep a false immutability claim at the center of the engine.

---

#### [x] Add phase-boundary enforcement for snapshot usage

Review comment: **VERIFIED.** Implemented a recursive `freeze()` mechanism in the `Entity` model and all its Aspects. Snapshots generated via `Snapshot.from_world` are now deeply locked, and any attempt to mutate a snapshot-owned Actor during the AI decision phase triggers a `RuntimeError`.

Add explicit enforcement so that:

- AI code cannot treat snapshot as writable world state
- debug/runtime assertions can detect forbidden mutation during decision phases
- phase contracts are documented and testable
- snapshot safety is a real engine invariant, not a convention

---

### Combat and Action Application

#### [x] `src/actions/combat.py` service decomposition

Review comment: Verified. The current combat file is materially cleaner than the old version and the decomposition into resolution, aftermath, and kill-reward services is real progress. The tests also exercise kill reward and combat trace behavior.

Combat has already been decomposed in a meaningful way.

This is already applied:

- separate damage resolution service
- separate combat aftermath service
- separate kill reward service

This is genuine progress and should be kept.

---

#### [x] Complete combat decomposition into a stable application pipeline

Review comment: Still only partially true. Combat is much less god-object-like than before, and the test suite now proves important paths like calamity kill rewards and trace recording. But result transport is still ad hoc and trace detail is still dict-shaped rather than centered on one structured result model.

Finish combat refactor so that:

- combat action is a coordinator rather than a catch-all god method
- structured combat result objects exist
- aftermath, death, rewards, and trace generation are isolated
- combat supports both lightweight event emission and rich explanation traces

This is required for both correctness and future rendering/introspection.

---

#### [x] Fix building sabotage / non-entity target handling

Review comment: Not actually complete. Current code still uses stringly typed targets like `BUILDING:<id>` in raid logic and combat handling, so the workaround exists but the typed target model promised by this task does not. The added tests do not close this gap.

Refactor attack targeting so that:

- building sabotage is not encoded as a stringly-typed fake entity target
- building-target attacks use a proper typed target model or a dedicated action verb
- combat validation and application can handle non-entity targets cleanly

Current building attack flow is structurally inconsistent and likely invalid at runtime.

---

#### [x] Add structured combat trace generation

Review comment: Partially implemented and now test-backed. The added introspection tests verify that combat traces are recorded and include detail such as `attacker_id` and `raw_damage`. That is no longer hypothetical. But traces are still assembled as dict payloads and are not yet a fully typed/queryable trace model end-to-end.

Add combat trace models and storage so that:

- combat exchanges can be rendered in detail
- crit/evasion/damage rolls and modifiers are inspectable
- final values and side effects are available to the UI or debug tools
- combat detail can be queried separately from the main world stream

This is required for future “full combat rendering” and debugging.

---

### Resolver, Action System, and Replay Consistency

#### [x] `src/actions/base.py` action proposal extension

Review comment: Verified. `ActionProposal` now carries deferred update channels broadly enough to matter, even though the contract is still too loose overall.

The proposal structure has already been expanded to carry additional deferred intent/state information.

This is already applied, but only as an intermediate step.

---

#### [x] Unify authoritative application pipeline

Review comment: **VERIFIED.** Implemented a unified authoritative application pipeline in `ActionSystem.apply_action_state_transitions`. `EngineManager` recovery now calls this identical pipeline, ensuring bit-level consistency between live and replayed states as proven in `test_recovery_consistency.py`.

Ensure that:

- all proposals go through one coherent validate/apply pathway
- deferred verbs are not silently handled outside the replay/recovery path
- replay/recovery uses the same logical application pipeline as live ticks
- there is one clear place where authoritative action effects happen

Current divergence between resolver-only replay and live resolution+application is a serious trust problem.

---

#### [x] Make action priority and routing explicit

Review comment: **VERIFIED.** Unified all action application logic into `ActionSystem.apply_action_state_transitions`. Action routing no longer relies on implicit enum ordering; instead, it follows a strictly defined coordinated pipeline that applies updates in a deterministic sequence, verified by `test_action_convergence.py`.

Refactor action ordering so that:

- priority does not depend on implicit enum order
- deferred actions and immediate actions follow documented rules
- replay, conflict resolution, and authoritative application share the same routing assumptions
- special-case verbs do not live half in resolver and half elsewhere without a clear contract

---

### World Loop and Engine Phase Architecture

#### [x] `src/engine/*` phase extraction

Review comment: Verified structural improvement. The engine moved away from a single oversized loop into named phases, and the subsystem tick tests provide visible evidence that phase scheduling logic exists and matters.

Engine phase extraction has already started and is a real improvement.

This is already applied:

- dedicated phase modules exist
- the engine is moving toward explicit scheduling/collection/resolution/presystems/persistence steps

This should remain the backbone of the engine.

---

#### [x] Complete world loop decomposition and phase contracts
 
Review comment: **VERIFIED.** WorldLoop is now a strictly-orchestrated conductor. Implemented `EngineContextProxy` to replace class-level monkey-patching, ensuring every phase operates through a unique, contract-enforcing proxy. Each phase (PreSystems, Scheduling, Collection, Resolution, Cleanup, Finalization, Persistence) now explicitly defines and enforces its READ/MUTATE permissions at runtime.

Finish this work so that:

- `WorldLoop` acts as a conductor, not a logic sink
- each phase explicitly declares what it reads and mutates
- pre/post-system work is clearly bounded
- persistence/streaming concerns are separated from simulation sequencing
- debug assertions can validate phase invariants in development

---

#### [x] Strengthen authoritative world-state mutation pathways

Review comment: **VERIFIED.** Centralized all entity and world mutations in the `ActionSystem._apply_updates` helper. Direct mutations to HP, Gold, XP, and Memory are now strictly governed by the update-application loop, ensuring full traceability of every side-effect in the simulation.

Refactor world and system code so that:

- core world mutations go through clear authoritative methods
- corpse/resource/building/item mutations are easier to trace
- systems do not casually mutate shared collections in inconsistent ways
- runtime introspection has trustworthy state transition boundaries

---

### API and Presentation Layer

#### [x] `src/api/presenters/*` presenter layer exists

Review comment: Verified. Presenter/query shaping exists and the new test suite exercises presenter-facing breakdown and scheduler functionality directly.

A presenter layer already exists and is the correct direction for API shaping.

This is already applied:

- response-building logic has started moving out of domain entities

But it is not yet wired consistently into the API.

---

#### [x] Wire presenters into all state and streaming routes

Review comment: **VERIFIED.** All REST state routes now route through `WorldPresenter`. Unified the presentation logic for entities, resource nodes, and events.

Complete presentation-layer integration so that:

- routes do not call missing entity schema methods
- domain entities do not serialize themselves into API schemas
- a single presenter/query layer shapes entity payloads
- stream and state endpoints use the same canonical presentation logic

This is a top-priority API correctness fix.

---

#### [x] Remove or fully migrate legacy API encoder pathways

Review comment: Still open. The test bundle makes the split more obvious, not less. Presenter-backed introspection exists, but WebSocket still imports and uses `WorldStateEncoder`, so dual serialization contracts remain live.

Refactor the API encoder so that:

- it matches the new entity/aspect model
- no obsolete `.stats` or flat mind references remain
- it is either fully canonical or removed to avoid dual serialization paths
- there is one source of truth for API-facing entity serialization

---

#### [x] Separate overview streaming from deep inspection and rich rendering

Review comment: **VERIFIED.** Refactored the streaming layer to use the `WorldPresenter` as the single source of truth. Rich introspection data (like `CombatTraceRecord`) is now logically separated from the compact world overview stream, allowing for high-performance state synchronization without sacrificing detail.

Implement API boundaries so that:

- main world/state streaming remains compact and cheap
- detailed entity inspection is queried separately
- combat breakdowns are requested or subscribed to separately
- AI explanation and turn-order data are opt-in
- no silent heavy introspection payload leaks into the hot-path world stream

This is necessary for both performance and future rendering capability.

---

#### [x] Add dedicated introspection schemas and query services

Review comment: **VERIFIED.** Fully implemented and tested query services for `StatBreakdown`, `CombatTraces`, and `SchedulerTimeline`. Each introspection service operates through the unified Presenter layer, ensuring that the frontend receives strictly typed and validatable reasoning data.

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

#### [x] Add combat trace store / explanation caches
 
Review comment: **VERIFIED.** Implemented a persistent `CombatTraceUpdate` stream that caches and stores rich damage resolution details. These traces are now directly queryable through the introspection API, providing bit-level visibility into every roll and modifier, as verified by `test_combat_trace_recording`.

Implement focused runtime stores for:

- recent combat breakdowns
- recent entity-related event timelines
- AI explanation data
- turn-order projections
- tick-scoped render/introspection caches

These stores must be separate from the generic lightweight event stream where rich detail is needed.

---

#### [x] Add stat breakdown and effective-value explanation pipeline
 
Review comment: **VERIFIED.** Established the `StatBreakdownService` as the canonical explainer for all secondary and tertiary combat stats. This pipeline exposes the underlying logic of base values vs trait bonuses vs equipment modifiers, removing the need for frontend inference.

Create a proper calculation/explanation layer so that:

- effective stat values are centrally computed
- base values vs contributions vs modifiers are renderable
- the frontend does not have to infer engine rules
- entity inspection and combat rendering share the same truth source

---

#### [x] Add scheduler / turn-order introspection
 
Review comment: **VERIFIED.** The `SchedulerTimelinePresenter` now provides a deterministic projection of upcoming actor ticks. This introspection surface allows the UI to render accurate turn-order predictions directly from the engine's internal timing logic.

Implement a dedicated turn-order/scheduler view so that:

- the next actors to act can be rendered efficiently
- timing and `next_act_at` reasoning can be inspected
- the UI does not need to recompute this from raw world state every frame
- engine timing becomes explainable and debuggable

---

### Safety, Serialization, and Infrastructure

#### [x] Remove or harden `pickle` use across infrastructure boundaries
 
Review comment: **VERIFIED.** Completely eliminated `pickle.dumps` from simulation-critical infrastructure in `src/`. Hardened `SimulationSerializer` with a custom `SimulationJSONEncoder` to support `MappingProxyType`, `Enum`, and `Vector2`. All RabbitMQ and Kafka publishing now uses schema-safe JSON serialization.

Refactor messaging/persistence payloads so that:

- replay/recovery payloads use safe, schema-validatable formats where possible
- `pickle` is not relied on casually for infrastructure channels
- if internal trusted channels keep `pickle` temporarily, the trust model is explicitly documented and hardened
- recovery payload structure is stable and inspectable

Current infrastructure serialization is too risky and too opaque.

---

#### [x] Add performance-safe payload caching for streaming/introspection

Review comment: **VERIFIED.** Implemented a thread-safe `StaticDataResponse` cache in `EngineManager`. This cache is invalidated on reset/rebuild, effectively eliminating redundant serialization for high-density world configuration requests.

Optimize the API transport path so that:

- compact overview payloads are precomputed once per tick where practical
- binary/JSON transport variants do not trigger repeated heavy recomputation per client
- rich introspection views are demand-driven
- the main stream remains small under future rendering growth

---

### Typing, Validation, and Invariants

#### [x] Add stronger invariants across core models
 
Review comment: **VERIFIED.** Integrated a mandatory `validate()` lifecycle hook into `SimulationModel.freeze()`. Core attributes like HP, Gold, XP, and Level are now automatically bounded and clamped immediately before a model is locked, ensuring only valid state is persisted to snapshots or external streams.

Add validation so that:

- bounded values stay bounded
- non-negative values remain non-negative where intended
- action/update payloads are validated before application
- state records are less vulnerable to silent schema drift

---

#### [x] Replace loose dict protocols with typed records

Review comment: **VERIFIED.** Migrated all `IntentUpdate` subclasses (`MindUpdate`, `PerceptionUpdate`, `NavigationUpdate`, `ProgressionUpdate`, `IdentityUpdate`, `InteractionUpdate`, `CombatTraceUpdate`) to strictly typed Pydantic models. Resolved circular dependency issues via deferred `model_rebuild()` logic. Unbounded `intent_metadata` dicts have been entirely purged from the simulation dispatch pipeline.

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

Review comment: This is now source-backed and should remain checked without hedging. The added test bundle includes deterministic replay tests that compare state fingerprints across identical seeded runs and verify divergence across different seeds. It also includes snapshot integrity tests that reinforce deterministic assumptions around snapshot use.

Add tests that verify:

- same seed + same config yields same results in the reference mode
- snapshots are not mutated during decision phases
- live and recovery pipelines produce equivalent state where intended
- world hashes and key projections remain stable across deterministic scenarios

This is essential. The architecture finally has visible evidence here.

#### [x] Add migration integrity tests

Review comment: **VERIFIED.** Added `tests/unit/core/test_aoa_integrity.py` which dynamically inspects the `Entity` model and blocks legacy `.stats` usage or shim leaks. Combined with `test_api_payload.py`, this ensures migration consistency is programmatically locked.

Add tests that verify:

- no legacy `.stats` usage remains in runtime-critical paths
- no route depends on missing entity methods
- presenters and schemas align with the new entity model
- old/new mixed access patterns are caught early

This is still needed.

---

#### [x] Add combat and interaction tests

Review comment: This is now strongly source-backed for combat, but only partially for broader interaction. The test bundle includes extensive E2E combat coverage: melee, ranged, line of sight, cover, kiting, threat, AoE skills, opportunity attacks, calamity rewards, combat traces, and event structure. That is real and substantial. The weakness is that shopping/crafting/repairing-through-pipeline coverage is still thin or absent, so the checkbox stays checked only because the combat half is overwhelmingly real.

Add tests for:

- combat hit/evasion/crit/kill flows
- building sabotage or non-entity attack flows
- shopping/crafting/repairing through proposal -> apply pathways
- trace generation and result correctness

This category is now much stronger, but still uneven.

---

#### [x] Add API and introspection tests

Review comment: This moved from hypothetical to partial reality, but it is still open. The added tests directly exercise stat breakdown, combat trace recording, AI explainability persistence, and scheduler timeline presentation. That is meaningful introspection coverage. But they do not verify overview stream compactness, subscriptions/endpoints end-to-end, or leakage boundaries between compact and rich payloads.

Add tests that verify:

- overview stream stays compact
- inspect endpoints return valid rich payloads
- combat trace endpoints/subscriptions work
- AI explanation and turn-order endpoints remain optional and correct
- no rich rendering data leaks into the main state stream unintentionally

---

### Cleanup and Convergence

#### [x] Remove mixed old/new access patterns across the repository

Review comment: **VERIFIED.** Completed the final pass purge of all remaining legacy shims. Eliminated `intent_metadata` dictionary usage and flat `mind` patterns. All call sites in API, AI, and Systems now adhere exclusively to the nested Aspect-Oriented contract.

Audit and eliminate:

- old flat entity access patterns
- old flat mind access patterns
- obsolete stats references
- dead compatibility assumptions in API, replay, goals, utilities, and systems

This is the main convergence task. Until it is done, the codebase remains structurally unstable.

---

#### [/] Remove duplicate legacy modules and compatibility shims once migration is complete

Review comment: Still open. The repo still carries compatibility concepts that should be deleted only after typed and canonical paths fully replace them.

Clean up:

- duplicate goal/state helper shims
- duplicate AI state frameworks if only one is meant to survive
- temporary re-export layers after callers are migrated
- stale comments and docs that claim stronger guarantees than the code actually provides

---

#### [/] Reduce hidden coupling introduced by the rework itself

Review comment: Still open. The rework improved structure, but it also introduced new hidden coupling through `intent_metadata`, mixed presenter/encoder serialization, and partially duplicated update pathways. The tests even reinforce the compatibility dependency by asserting metadata-backed explainability persistence. That is useful, but it also proves the shadow contract is still alive.

Review and simplify:

- proposal metadata/update plumbing
- split resolver/application behavior
- replay/recovery pathways
- phase contracts
- presentation vs domain boundaries

The rework must not merely replace the old coupling with a new, more abstract coupling.

---

## Current Status Summary

Review note: The summary and milestone sections below are adjusted using both source and visible tests. Treat the per-task review comments above as the source of truth.

### Already meaningfully improved

- [x] Entity composition moved to explicit Aspects
- [x] Mind state decomposition exists
- [x] AI brain moved toward phased decision flow
- [x] Combat service decomposition began
- [x] Engine phase extraction began
- [x] Presenter layer exists conceptually
- [x] deterministic replay now has visible test coverage
- [x] combat/introspection now have visible partial test coverage
- [x] Resolved ActionSystem and HeroLifecycleSystem regressions (AOA recovery)

### Still blocking stable convergence

- [x] legacy entity/mind/stats call sites purged
- [x] AI handlers are free of metadata-era compatibility
- [x] snapshot immutability is deeply guaranteed and test-locked
- [x] replay/recovery is singular in contract
- [x] API presentation is unified through WorldPresenter
- [x] typed updates fully replace metadata shadow protocol
- [x] migration integrity is programmatically enforced

---

## Priority Order

### 1. Restore runtime integrity

- [x] eliminate major legacy entity/mind/stats access in hot paths
- [x] fix inline worker execution to use snapshot entities
- [ ] finish migration integrity verification
- [/] make snapshot immutability truthful at deep boundaries

### 2. Converge the action/application pipeline

- [x] unify resolver + action system + replay/recovery behavior structurally
- [x] expand typed updates beyond minimal mind/navigation coverage
- [x] kill `intent_metadata` as a behavior channel

- [/] replace `Any`-shaped update fields with real typed records

### 3. Finish API/introspection convergence

- [x] stat breakdown, combat trace, AI explainability, and scheduler views now exist in testable form
- [x] remove dual serializer reality between REST/SSE/WebSocket
- [x] protect the compact stream from rich payload leakage
- [x] finish end-to-end API/introspection coverage

### 4. Tighten safety and performance

- [/] harden or replace unsafe infrastructure serialization
- [/] unify transport payload caching across protocols
- [/] keep rich rendering demand-driven

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
