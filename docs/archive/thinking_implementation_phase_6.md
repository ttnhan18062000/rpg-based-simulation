[Phase 6] - Engine Integration, Presentation, Replay, and Operational Observability

[Phase Description]
Phase 6 is the integration phase that makes the strategic system real across the engine, not just real inside AI code. The earlier phases give entities strategic state, appraisal, uncertainty, social contracts, and event-driven consequence loops. Phase 6 is about wiring that state into the existing simulation surfaces that already exist in the source: town/building handlers, decoupled world systems, immutable snapshots, replay recording, FastAPI state inspection, CLI inspection, event telemetry, and metrics. The source already has all of those seams: building visit handlers drive town behavior, the world loop runs with a `SystemManager` and `SystemContext`, `Snapshot` already carries world registries, `EngineManager` serves immutable snapshots to the API, `ReplayRecorder` serializes tick logs, `EntityPresenter` and `AIPresenter` shape inspection data, and `EntityInspector` already renders narrative and reputation information. Phase 6 is where the strategic layer becomes visible, operable, debuggable, and stable across those boundaries.

The hard truth is that the current integration surfaces still expose mostly tactical and narrative information, not strategic continuity. The API already serves `/state`, `/inspect/{entity_id}`, timeline, static data, and frontend visualization; the presenters already expose goal scores, beliefs, bonds, routines, turning points, and reputation; and replay currently records only tick actions plus a slim entity snapshot of id, kind, position, hp, and AI state. That means the engine is observable, but not yet for the layer you are building. If Phase 6 is skipped or done loosely, the project will have a strategic brain that cannot be inspected properly, cannot be replayed meaningfully, and cannot be validated at runtime.

[Phase technical implementation]
Phase 6 should integrate the strategic layer into four concrete engine surfaces:

1. **Building and interaction surfaces**
   Guild, class hall, blacksmith, inn, and home handlers already exist and already produce tactical or knowledge-rich outcomes. They should become standardized strategic producers and consumers rather than isolated logic islands.

2. **World systems and registries**
   The engine already has decoupled systems, a `SystemContext`, world history, scars, regional consequences, social registry, and group registry inside snapshots. Strategy should hook into those systems and registries rather than bypass them.

3. **Presentation and operational surfaces**
   API presenters, inspection schemas, CLI inspector, event telemetry, and metrics all already exist. They need to expose strategic state, consequence traces, contract state, leads, blockers, and current project/objective data as first-class explainability surfaces.

4. **Replay and determinism surfaces**
   Replay recording currently serializes a very thin per-tick view. That is not enough for validating strategic continuity. Strategic state transitions, concerns, project mutations, contracts, and major leads/blockers need replay-visible representation.

[Phase important notes]
The biggest mistake here is to treat Phase 6 as UI polish. It is not. It is architectural completion. The current engine already commits to immutable snapshots for server reads and worker safety, and already uses presenters instead of letting domain models leak directly into the API. Strategy has to respect those same patterns. If strategic data is only available by crawling internal fields or debug-printing Python objects, the implementation is not finished.

The second mistake is duplicating logic across surfaces. Buildings should not each invent separate knowledge or strategy side channels; API presenters should not each re-derive strategy independently; replay should not guess at strategic meaning from action reasons; and metrics should not be added ad hoc without a stable vocabulary. Phase 6 is about centralizing those semantics and then projecting them outward cleanly.

[Phase acceptance criteria]
At the end of Phase 6, strategic state and strategic changes are integrated with building handlers, world systems, snapshots, API inspection, CLI inspection, replay, event telemetry, and metrics. A developer can trace a strategic change from producer to authoritative update to snapshot to API/CLI output to replay log, and can verify that the layer is deterministic and operationally observable instead of trapped inside the AI pipeline.

## Task

[ ] (checkbox) - [Task 1] - Standardize building handlers as strategic producers and consumers

[Task Description]
The source already has dedicated handlers for guild, class hall, blacksmith, inn, and home interactions, and those handlers already perform meaningful logic: guild visits reveal intel and add goals, class hall visits learn skills and perform breakthroughs, blacksmith visits learn recipes and expose missing materials, home visits store items and manage hunger/rest. These are exactly the right integration surfaces for strategic state, but right now they still behave mostly as localized tactical routines.

[Task technical implementation]
Refactor building handlers so each one uses a shared strategic integration contract:

- consume current project/objective/blockers/leads/contracts from `AIContext`
- emit strategic updates in addition to tactical updates
- stop encoding durable strategic meaning only in `reason` strings or `goals_add`

Concrete building responsibilities:

- **Guild**: produce leads, quest-backed obligations, candidate zones, warnings, and brokered party opportunities
- **Class Hall**: produce capability blockers, advancement opportunities, training objectives, and verified class-growth milestones
- **Blacksmith**: produce resource blockers, crafting upgrade opportunities, material-source leads, and equipment-improvement project support
- **Inn**: produce rumor propagation, party recruitment, debt settlement, negotiation opportunities, and shared warnings
- **Home**: produce storage/maintenance plus rebuild, recovery, home-attachment, and household-pressure updates when appropriate

Use the strategic knowledge ingestion and consequence services from prior phases instead of re-embedding logic in each handler.

[Task possible affected files]

- `src/ai/states/town.py` or equivalent town handler module
- `src/ai/brain.py`
- `src/core/logic/strategic_knowledge_ingestion.py`
- `src/core/logic/strategic_consequence_service.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not let buildings remain separate mini-engines. The point of Phase 6 is to unify the semantics they already expose.

[Task check list]

- [ ] Audit all building handlers for strategic outputs
- [ ] Replace prose-only durable meaning with typed updates
- [ ] Route handler knowledge into shared strategic services
- [ ] Make inn/home part of strategy, not only routine
- [ ] Preserve current tactical usability while enriching strategy

[Task acceptance criteria]
Every major town/building handler can now both consume strategic context and emit typed strategic consequences rather than only local tactical effects.

---

[ ] (checkbox) - [Task 2] - Integrate strategic state into the decoupled world-system layer

[Task Description]
The engine already has a decoupled `System` / `SystemContext` architecture and world-tier systems such as the `RegionalConsequenceSystem`. The snapshot already carries strategic-ish world registries including region control, war status, faction aggression, social registry, group registry, world history, scar registry, and regional consequence registry. Strategy should plug into this existing world-system substrate rather than remain an entity-only concern.

[Task technical implementation]
Introduce or extend systems so strategic world pressures are produced and maintained centrally. Likely additions:

- `StrategicWorldIntegrationSystem`
- `ContractLifecycleSystem`
- `ProjectOpportunitySystem`
- `SettlementPressureSystem`

Responsibilities may include:

- surfacing world-level strategic pressures to entities
- managing global or regional opportunity records
- updating shared obligations from town raids, wars, and regional instability
- syncing contract-backed group/project state with world registries
- broadcasting world events into strategic concern generation at system level

Use `SystemContext.emit`, `world_history`, and existing registries rather than building parallel global state.

[Task possible affected files]

- `src/systems/infrastructure/base.py`
- `src/systems/infrastructure/manager.py`
- `src/systems/world/...` new or extended system modules
- `src/core/models/world_state.py`
- `src/core/models/snapshot.py`

[Task important notes]
Do not push every strategic world effect back into `AIBrain`. The system layer exists specifically to avoid that kind of leakage.

[Task check list]

- [ ] Identify world-level strategic pressures needing system ownership
- [ ] Add or extend systems to maintain them
- [ ] Reuse `SystemContext` and world registries
- [ ] Avoid duplicating entity-local logic in systems
- [ ] Sync outputs into snapshot-visible state

[Task acceptance criteria]
Strategic world pressures and shared strategic registries are managed by the world-system layer rather than reconstructed ad hoc inside entity AI.

---

[ ] (checkbox) - [Task 3] - Extend snapshot contents so strategy is fully readable by workers and API consumers

[Task Description]
`Snapshot` is the engine’s authoritative read-only decision surface for worker threads and API presentation. It already includes entities, grid, buildings, resources, regions, social registry, group registry, world history, scars, and regional consequence data. Phase 6 needs to ensure that the strategic data introduced in prior phases is fully present, immutable, and exposed at the right level for both AI and API consumers.

[Task technical implementation]
Audit snapshot generation and entity freezing so the following are safe and visible:

- `mind.strategic` full state per entity
- any shared strategic world registries added in Phase 6
- contract registries or party registries if stored at world level
- strategic debug traces needed by presenters and inspector

Add explicit snapshot fields only for genuinely shared world strategy data. Do not duplicate entity strategy outside entities unless multiple actors need global shared access. Preserve immutability and avoid mutable aliasing between live world state and snapshots.

[Task possible affected files]

- `src/core/models/snapshot.py`
- `src/core/models/world_state.py`
- `src/engine/world_loop.py`
- snapshot creation helpers

[Task important notes]
Do not assume entity strategy is safe just because entity objects are already in snapshots. Nested strategic structures need the same immutability discipline as other aspect data.

[Task check list]

- [ ] Verify entity strategic state is snapshot-visible
- [ ] Add shared strategic world registries where needed
- [ ] Prevent mutable aliasing
- [ ] Ensure AI and API consumers can read the same snapshot structures
- [ ] Keep snapshot schema coherent

[Task acceptance criteria]
The immutable snapshot contains all strategic state needed for worker decision-making and for inspection/presentation without hidden live-world dependencies.

---

[ ] (checkbox) - [Task 4] - Extend API schemas and presenters to expose strategic state directly

[Task Description]
The API already serves state and inspection endpoints through `WorldPresenter`, `EntityPresenter`, `AIPresenter`, and `EntityInspectionSchema`. Right now those surfaces expose tactical goals, motives, beliefs, social bonds, routines, turning points, reputation, and combat history, but not the strategic layer being built. That is an integration gap, not a cosmetic gap.

[Task technical implementation]
Extend API schemas with strategic sections such as:

- `StrategicStateSchema`
- `DirectiveSchema`
- `ProjectSchema`
- `ObjectiveSchema`
- `ConcernSchema`
- `LeadSchema`
- `BlockerSchema`
- `ContractSchema`
- `StrategicDecisionTraceSchema`

Update:

- `EntityPresenter.to_full_schema(...)`
- `EntityPresenter.to_inspection_schema(...)`
- `AIPresenter.get_explanation(...)`
- `WorldPresenter.to_world_state_response(...)`

Expose at least:

- current project and objective
- directives
- active/suspended projects
- open concerns
- key leads/blockers
- contract/party state
- consequence trace summary
- strategic drivers for the current decision

This should be done with presenters, not by leaking raw model dumps into route handlers. The source already follows that separation.

[Task possible affected files]

- `src/api/schemas.py`
- `src/api/presenters/entity_presenter.py`
- `src/api/presenters/ai_presenter.py`
- `src/api/presenters/world_presenter.py`
- `src/api/routes/state.py`

[Task important notes]
Do not shove everything into one giant blob. The API should distinguish strategic state from tactical explanation and from narrative history.

[Task check list]

- [ ] Add strategic schemas
- [ ] Extend entity and world presenters
- [ ] Expose current project/objective and strategic trace
- [ ] Keep presenter-based separation of concerns
- [ ] Ensure `/inspect` and selected-entity state expose the same core strategic view

[Task acceptance criteria]
API consumers can read strategic state and strategic reasoning directly through typed schemas instead of reverse-engineering it from memory logs or action reasons.

---

[ ] (checkbox) - [Task 5] - Upgrade CLI inspector to render strategic continuity and consequence traces

[Task Description]
The CLI inspector already shows general info, biological needs, personality, public reputation, likely choices, social bonds, narrative history, and turning points. That is a solid explainability baseline, but it still stops short of the new strategic layer. Phase 6 should make the inspector a first-class diagnostic surface for strategy.

[Task technical implementation]
Extend `EntityInspector.inspect_full(...)` with new sections:

- directives
- current project / objective
- active and suspended projects
- open concerns
- leads and blockers
- contracts / party state
- recent strategic consequence chain
- resumption conditions for dormant unfinished business

Also add a compact cause-trace display:
`interpreted event -> turning point / concern -> project mutation -> current objective`

Reuse the same structured data prepared for the API where possible, instead of maintaining two different explainability models.

[Task possible affected files]

- `src/ui/cli/inspector.py`
- possibly shared presenter helpers under `src/api/presenters/...` or new shared inspection utilities

[Task important notes]
Do not let CLI and API drift into separate truth models. One strategic explanation vocabulary should serve both.

[Task check list]

- [ ] Add strategic sections to CLI inspector
- [ ] Add current project/objective display
- [ ] Add concern/lead/blocker/contract display
- [ ] Add causal consequence traces
- [ ] Reuse shared formatting/data builders where practical

[Task acceptance criteria]
The CLI inspector can show an entity’s strategic continuity as clearly as it already shows reputation and turning points.

---

[ ] (checkbox) - [Task 6] - Extend replay recording to capture strategic state changes, not just actions

[Task Description]
`ReplayRecorder` currently records tick number, applied actions, and a slim alive-entity snapshot with id, kind, position, hp, and AI state. That is far too thin to validate strategic continuity or debug strategic regressions. If replay cannot show project changes, concern activations, contract lifecycle, or major leads/blockers, then the new layer cannot be validated after the fact.

[Task technical implementation]
Extend replay serialization so each tick can optionally include:

- strategic deltas per entity
- current project/objective summaries
- concern creation/resolution
- contract creation/breach/dissolution
- major lead/blocker changes
- important consequence events or strategic trace snapshots

Keep full dumps bounded. Prefer delta-oriented logging:

- only strategic records that changed this tick
- only top-level current commitment summaries for stable context
- references to event IDs or project IDs instead of repeated full payloads when possible

Also consider versioning replay format because the current replay schema is minimal and static.

[Task possible affected files]

- `src/utils/replay.py`
- `src/actions/base.py`
- `src/core/models/strategy.py`
- any replay readers or tooling that consume replay files

[Task important notes]
Do not inflate replay into a full world dump per tick unless absolutely necessary. Keep it deterministic and inspectable, not enormous and useless.

[Task check list]

- [ ] Add strategy-aware replay format versioning
- [ ] Record per-tick strategic deltas
- [ ] Record current commitment summaries
- [ ] Record contract and concern lifecycle changes
- [ ] Keep payloads bounded and deterministic

[Task acceptance criteria]
Replay logs become sufficient to reconstruct and debug strategic continuity across ticks instead of only showing local action traces.

---

[ ] (checkbox) - [Task 7] - Extend event telemetry and history so strategic changes are externally visible

[Task Description]
The engine already has an `EventBus`, a `TelemetryBridge` that converts typed domain events into REST event-log entries, and a world-history recorder that writes higher-level world events. Phase 6 should make strategic changes visible through those same operational channels instead of requiring internal inspection only.

[Task technical implementation]
Add strategic event classes or telemetry mappings for:

- project started / suspended / resumed / completed / abandoned
- concern activated / resolved
- contract offered / accepted / breached / completed
- major lead discovered / verified / contradicted
- directive acquired / transformed
- town defense obligation triggered
- major rebuild or revenge pivot

Then:

- publish those events from authoritative application or consequence services
- bridge them through `TelemetryBridge` into event log entries
- optionally record them into world history when they are globally meaningful

This allows the frontend timeline and REST event stream to expose strategy as ongoing simulation behavior, not hidden model state.

[Task possible affected files]

- `src/core/data/events.py`
- `src/systems/infrastructure/event_system.py`
- `src/utils/event_log.py`
- `src/core/logic/strategic_consequence_service.py`
- `src/ai/strategy/...` services

[Task important notes]
Do not flood the event stream with every microscopic strategic edit. Emit only meaningful lifecycle changes that are useful to an observer.

[Task check list]

- [ ] Define strategic telemetry-worthy event kinds
- [ ] Publish them from authoritative state changes
- [ ] Bridge them into REST/timeline events
- [ ] Record globally meaningful ones into history when appropriate
- [ ] Keep event volume disciplined

[Task acceptance criteria]
Major strategic lifecycle changes appear in event telemetry and history instead of being visible only through direct entity inspection.

---

[ ] (checkbox) - [Task 8] - Add strategy-aware operational metrics

[Task Description]
The source already exposes Prometheus metrics for hero classes, gold circulation, building durability, quest status, crafted items, shop transactions, calamities, errors, invalid actions, and state transition failures. That means the engine already accepts operational measurement as a first-class concern. Phase 6 should add strategic metrics so you can tell whether the new layer is actually active and stable at runtime.

[Task technical implementation]
Add metrics such as:

- active projects total by type/status
- concern count by kind
- contracts active / breached / completed
- lead verification / contradiction counts
- blocker counts by type
- project interruption counts by cause
- strategic decision thrash rate
- project completion vs abandonment rates
- rebuild/defense concern persistence in raid-heavy regions

Update metrics in authoritative application or stable system layers, not in speculative AI code. This keeps them consistent with real state transitions.

[Task possible affected files]

- `src/utils/metrics.py`
- `src/systems/gameplay/action_system.py`
- `src/core/logic/strategic_consequence_service.py`
- `src/ai/strategy/...` state application paths

[Task important notes]
Do not add vanity metrics. Add only metrics that help detect incoherence, dead code paths, or pathological churn.

[Task check list]

- [ ] Define strategy-relevant counters/gauges
- [ ] Update them from authoritative transitions
- [ ] Track interruption and breach rates
- [ ] Track completion vs abandonment
- [ ] Track blocker/lead churn where useful

[Task acceptance criteria]
Operational dashboards can reveal whether strategic systems are active, coherent, and healthy instead of forcing every validation effort through manual inspection.

---

[ ] (checkbox) - [Task 9] - Align EngineManager and state routes with strategic payload expectations

[Task Description]
`EngineManager` is the live bridge between the running world loop and the API, and `/api/v1/state` plus `/api/v1/inspect/{entity_id}` are the primary frontend-facing read surfaces. Phase 6 has to ensure that strategic state moves through that bridge cleanly and efficiently.

[Task technical implementation]
Audit the following:

- snapshot publication cadence and payload size for added strategic fields
- selected-entity full schema vs slim entity schema
- whether strategic state should be included only in `selected_full` and `/inspect` or partially surfaced in slim world state
- event-log and timeline richness once strategic events are added
- frontend compatibility with richer `EntityInspectionSchema`

A practical split is:

- **world state / slim**: only lightweight strategic markers such as current project tag, concern flag, contract/party flag
- **selected full / inspect**: full strategic state and consequence trace
- **timeline / events**: only lifecycle-level strategic events

This matches the current design of `WorldPresenter`, which already distinguishes slim entity lists from full selected entity output.

[Task possible affected files]

- `src/api/engine_manager.py`
- `src/api/routes/state.py`
- `src/api/presenters/world_presenter.py`
- `src/api/presenters/entity_presenter.py`
- frontend consumers if present in repo

[Task important notes]
Do not dump full strategic state for every entity on every `/state` poll. That is wasteful and unnecessary. The current split between slim and selected views exists for a reason.

[Task check list]

- [ ] Define slim vs full strategic payload strategy
- [ ] Audit snapshot-to-route serialization cost
- [ ] Keep `/inspect` as the rich strategic surface
- [ ] Keep timeline/event views lifecycle-oriented
- [ ] Preserve frontend compatibility

[Task acceptance criteria]
The live API can expose strategic state without turning the main polling path into an overloaded debug dump.

---

[ ] (checkbox) - [Task 10] - Add end-to-end tests for strategic integration across engine surfaces

[Task Description]
Phase 6 is where isolated subsystems can appear correct while the integrated engine still fails. You need end-to-end tests that prove a strategic change can be produced, applied, surfaced, replayed, and inspected consistently across the whole stack.

[Task technical implementation]
Add integration tests that cover flows such as:

- guild visit creates strategic lead -> lead appears in strategic state -> lead visible in `/inspect` and CLI inspector -> lead change appears in replay/event stream if configured
- blacksmith visit creates resource blocker -> blocker visible in strategy presenter -> blocker influences later project/objective selection
- town raid creates concern and project suspension -> concern visible in API and inspector -> replay captures strategic delta -> metrics increment appropriately
- contract accepted -> tactical group instantiated -> contract visible in inspect -> breach updates social/reputation and telemetry
- selected entity view shows strategic trace while slim state only exposes compact markers

Also add stability tests around snapshot publication and replay serialization format.

[Task possible affected files]

- `tests/api/test_strategic_inspection_routes.py`
- `tests/integration/test_building_to_strategy_pipeline.py`
- `tests/integration/test_strategy_replay_and_events.py`
- `tests/integration/test_contract_group_surface_consistency.py`
- `tests/integration/test_snapshot_strategy_visibility.py`

[Task important notes]
Do not end Phase 6 with only unit tests. This phase is about pipeline integrity across surfaces. Unit tests alone will miss the actual failure mode.

[Task check list]

- [ ] Add end-to-end API inspection tests
- [ ] Add replay integration tests
- [ ] Add event telemetry integration tests
- [ ] Add building-to-strategy integration tests
- [ ] Add contract/group surface consistency tests
- [ ] Add snapshot visibility and payload-shape tests

[Task acceptance criteria]
A strategic change can be traced end-to-end through authoritative application, snapshot publication, presenter output, inspection surfaces, replay, and telemetry without semantic drift.

---

Priority Plan

What must change in mindset or assumptions
Stop treating integration and observability as optional last-mile cleanup. In this engine, they are part of the design contract. The source already proves that snapshots, presenters, routes, replay, events, and metrics are first-class architecture, not afterthoughts. Strategy has to show up there or it is not really part of the engine.

What actions must be taken immediately
Do Tasks 1 through 4 first: standardize building integration, hook strategy into the world-system layer, ensure snapshot visibility, and extend API schemas/presenters. Then do Tasks 5 through 9 so CLI inspection, replay, telemetry, metrics, and live API payloads all align. Finish with Task 10 before claiming the architecture is complete.

What must stop or be eliminated
Stop leaving durable strategic meaning in `reason` strings, goal strings, or hidden internal fields. Stop assuming replay and event logs are “good enough” just because actions are recorded. Stop exposing only tactical explanations while the real strategic layer stays invisible.

The consequences and opportunity cost if this fails
You will have built a strategic architecture that cannot be validated, debugged, replayed, or surfaced coherently. That means every future bug will look like “AI weirdness” instead of a traceable state transition, and the most expensive part of the system will remain the least trustworthy.
