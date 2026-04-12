# Technical Implementation Conventions

This codebase already has a strong architectural spine. The right goal is not to “make it cleaner” in the abstract. The goal is to preserve the parts that already make it maintainable: typed state models, immutable snapshots for decision-making, authoritative state application, deterministic ordering, decoupled systems, and presenter-based read surfaces. If new work ignores those patterns, the project will get more features and less reliability at the same time.

## 1. Architectural conventions

### 1.1 Keep decision-making read-only and state mutation authoritative

The source already separates “thinking” from “changing the world.” `WorkerPool` distributes decisions against an immutable `Snapshot`, while `ActionSystem.apply_action_state_transitions` is the authoritative pipeline that applies typed updates and side effects to the live world. That separation is the foundation of determinism, replayability, and safe parallelism. New features must preserve it. Never let AI handlers, building handlers, or helper services mutate live entity/world state directly when the change is meant to persist. Emit typed updates and let the authoritative layer apply them.

### 1.2 Model the domain with typed records, not prose or metadata blobs

The codebase already leans on `SimulationModel` and typed `IntentUpdate` subclasses as the main state and mutation vocabulary. Continue that discipline. If a concept matters strategically or mechanically, it should exist as a typed record with validation, not as a string in `reason`, a hand-waved dict in `metadata`, or an inspector-only narrative. This is especially important for directives, projects, objectives, concerns, leads, blockers, obligations, and contracts because the design explicitly defines those as the real units of continuity.

### 1.3 Preserve the layer boundaries: world, strategy, tactics, presentation

The design thinking file is clear that strategy and tactics are not the same layer, and the code already reflects similar separation in practice: systems own world-level processes, AI owns decision-making, typed updates own mutations, and presenters own read-model shaping for API/UI. Keep those boundaries sharp. Do not let tactical handlers become strategy engines, do not let presenters invent business logic, and do not let world systems reconstruct per-entity private cognition.

## 2. State and model conventions

### 2.1 Every durable concept needs a home in the model graph

`SimulationModel` is already built for deep copy, unfreezing, and safe snapshot isolation. Use that instead of ad hoc containers. New durable state should live in typed submodels attached to the right aspect or registry. Do not hide long-lived behavior in helper state, caches, or service instances. If it must survive ticks, it belongs in the entity, world, or a formal registry.

### 2.2 Prefer explicit lifecycle fields over implicit semantics

For any persistent record, add stable IDs and lifecycle metadata such as created, updated, resolved, suspended, expired, or superseded fields. The design requires unfinished business, suspended projects, contradiction tracking, and social contract memory. Those become unmaintainable if lifecycle is inferred indirectly from list membership or missing values.

### 2.3 Keep typed rebuilds centralized and predictable

The source already uses `model_rebuild()` to resolve forward references in complex model graphs. Follow that pattern. If you add new strategic or social records with circular references, rebuild them in one predictable place instead of scattering import-time fixes across the codebase. That keeps import behavior understandable and avoids fragile initialization bugs.

## 3. Mutation and update conventions

### 3.1 New behavior should flow through `IntentUpdate`-style updates

The existing architecture already uses `MindUpdate`, `PerceptionUpdate`, `NavigationUpdate`, `ProgressionUpdate`, `ReputationUpdate`, `WorldUpdate`, and similar typed updates. Follow that exact pattern for new strategic and contract domains. This keeps mutation composable, inspectable, and deterministic. It also avoids turning `metadata` into a hidden second update system.

### 3.2 Update generation should be functional; application should be mechanical

The clean split in `ActionSystem` is a good convention to preserve: generate updates based on current state, then apply them authoritatively. New services should mostly be pure or near-pure transformers that inspect context and return typed changes. The authoritative applicator should then do deterministic, ID-based merging or replacement. Do not mix policy, mutation, and event emission into one giant method.

### 3.3 Never use `reason` as storage

`reason` is for explanation. It is not state. The current source still exposes valuable information through prose strings in places, and that is exactly the kind of shortcut that becomes technical debt once systems need to reason over it later. If it matters after the current tick, promote it to a typed field or record.

## 4. Determinism conventions

### 4.1 Stable ordering is mandatory, not optional

The engine already sorts ready entities by `next_act_at` then entity ID, and presenters also sort timelines deterministically. Preserve that habit everywhere strategic ranking, contract resolution, candidate filtering, or replay output is involved. If two outcomes can be tied, define a stable tie-breaker. Otherwise debugging turns into superstition.

### 4.2 Use the existing deterministic randomness model

The source already treats randomness as domain-based and seed-driven. New logic should not introduce uncontrolled `random` calls in behavior code. If something must be probabilistic, route it through the engine’s deterministic RNG strategy so replay and distributed decision-making remain coherent.

### 4.3 Replay should reflect real authoritative outcomes

Replay currently records actions and a thin entity snapshot per tick. That is useful but too thin for strategic debugging. The convention going forward should be: anything that materially affects long-term behavior should either be reconstructible from replay or explicitly logged as a strategic delta. Otherwise regressions will be impossible to analyze.

## 5. AI and cognition conventions

### 5.1 The AI brain should orchestrate; services should specialize

`AIBrain` already runs a phased pipeline. Keep it as the coordinator, not the dumping ground. New strategic logic should live in focused services: candidate selection, objective derivation, blocker inference, recruitment negotiation, place-threat appraisal, consequence interpretation, and so on. That keeps the brain legible and makes testing realistic.

### 5.2 Tactical handlers should stay tactical

The design is explicit that objectives should map to local goals and state handlers, but remain abstract enough to survive interruption. That means movement, combat, rest, sleep, loot, and building visits should remain execution mechanisms. Do not bury project ownership or long-term identity change inside tactical state handlers.

### 5.3 Uncertainty should stay uncertain until evidence narrows it

The design explicitly rejects converting a vague lead into an exact coordinate. That needs to become a coding convention. Use hypotheses, candidate zones, trust-weighted leads, contradiction status, and search history. If a clue becomes exact the moment it is received, the investigation layer is fake.

### 5.4 Social cooperation must be explicit, not inferred from proximity

The design file says a party is a purposeful temporary social machine with purpose, reward logic, role expectations, fallback conditions, dissolution conditions, and memory of broken promises. The source already has group records and social bonds, but that is not enough by itself. The convention should be: if cooperation matters beyond the current moment, represent it as a contract or party record, not just nearby entities sharing a goal.

## 6. System and service conventions

### 6.1 Prefer decoupled systems for world-level processes

The codebase already has a `System` / `SystemContext` pattern and uses it for gameplay and world processes. Use that for shared pressures, regional consequences, contract lifecycles, or settlement-level strategic updates. Do not push every global concern into entity AI just because the AI can see it.

### 6.2 Services should have one kind of responsibility

A service should either interpret events, infer blockers, apply consequences, rank candidates, or present data. Once a service starts both mutating world state and generating narrative and choosing goals, it is already too large. The existing separation across `EventInterpreterService`, `SocialStateApplicator`, `KnowledgePropagationService`, and presenters is the right model.

### 6.3 Reuse shared strategic services from handlers instead of cloning logic

Guild, class hall, blacksmith, inn, and home are rich integration points. But they should call shared knowledge-ingestion, blocker, negotiation, or consequence services instead of each embedding their own variant of those rules. Otherwise the same semantic concepts will diverge by building type and become impossible to maintain. The design file already points to those buildings as recurring objective producers, so centralization matters.

## 7. Presentation and API conventions

### 7.1 Presenters are the only place that should shape read models

The API already uses presenters such as `EntityPresenter`, `WorldPresenter`, `EventPresenter`, and `SchedulerPresenter`. Keep using that pattern. Routes should not assemble strategic payloads directly from raw entities, and domain models should not be bent to frontend convenience. That separation is what keeps the internal model clean while still making the system explainable.

### 7.2 Explanations should be structured first, prose second

The source already exposes readable explanations and inspector summaries, but for maintainability the canonical form should be structured records: current project, current objective, concern list, blocker list, contract terms, strategic drivers, and consequence traces. Human-readable summaries can be derived from those. The reverse approach is brittle.

### 7.3 Keep slim and full views separate

The live API already distinguishes timeline/slim state from richer selected-entity or inspect views. Preserve that. Do not dump the full strategic graph for every entity on every world-state poll. Use lightweight markers in broad views and rich detail only in inspect/full-detail surfaces.

## 8. Replay, telemetry, and metrics conventions

### 8.1 Observability is part of the architecture

The source already has replay recording, an event bus, a telemetry bridge, event presentation, and metrics. Treat those as first-class extension points. New strategic lifecycle changes should be visible through at least one of: replay deltas, event telemetry, metrics, or inspection. Hidden state is unmaintainable state.

### 8.2 Emit lifecycle events, not noise

The telemetry bridge currently maps strongly typed domain events into event-log messages. Follow that pattern for meaningful strategic changes: project started, suspended, resumed, completed, concern activated, contract accepted, breach recorded, major lead verified. Do not emit every microscopic internal score change.

### 8.3 Metrics should detect churn, dead paths, and instability

The codebase already uses metrics for health, errors, world state, and gameplay systems. Strategic metrics should be equally pragmatic: interruption rate, concern count, blocker mix, contract breaches, completion vs abandonment, thrash rate. Avoid vanity counters. Instrument transitions that help detect incoherence.

## 9. Naming and readability conventions

### 9.1 Name by domain meaning, not by implementation accident

Use names like `ConcernRecord`, `DirectiveMutationService`, `ProjectSuspensionReason`, `CandidateZoneRecord`, `ContractConsequenceService`. Avoid vague names like `manager2`, `state_helper`, `info_cache`, or `temp_goal_logic`. The design vocabulary is already strong. Reuse it consistently.

### 9.2 Prefer small, explicit data transformations

A clean method should usually do one of these:

- read state and rank options
- transform evidence into typed records
- apply one kind of update
- shape one kind of API view

When a method mixes all four, readability collapses. The source already shows both good separation and some monolithic pressure points. Learn from the separation, not the sprawl.

### 9.3 Keep comments architectural, not apologetic

Good comments explain why a boundary exists, why a deterministic tie-breaker matters, or why a lead must remain vague. Bad comments explain line-by-line obvious Python. The source’s stronger comments are the ones that preserve architectural invariants such as authoritative updates, snapshot isolation, and deterministic scheduling.

## 10. Testing conventions

### 10.1 Test by layer

Use three levels:

- model tests for validation, copying, serialization, rebuilds
- service tests for strategic reasoning and update generation
- integration tests for authoritative application, snapshots, presenters, replay, and telemetry

That matches the architecture. If you test only at one level, you will miss either correctness or system drift.

### 10.2 Prefer deterministic fixtures over impressionistic simulation runs

Because the engine is explicitly built around snapshots, tie-breaking, and deterministic ordering, your tests should assert on stable outputs under fixed inputs. “Looks good in the sim” is not a test. It is an anecdote.

### 10.3 Test anti-pattern boundaries

Write tests that prove the architecture is not being violated:

- AI cannot mutate live state directly
- snapshot state is isolated
- replay contains the needed deltas
- vague leads do not become exact too early
- public reputation and private consequences can diverge
- contracts affect later recruitment and trust

Those are the failures that will quietly rot the codebase if left unchecked.

## 11. Important anti-patterns to ban

Do not add durable behavior through `reason` strings, ad hoc `metadata`, or inspector-only summaries.

Do not mutate live entity or world state inside AI decision code, building handlers, or negotiation helpers when the change should be authoritative.

Do not collapse strategy into tactical goal scoring. The design explicitly rejects that flattening.

Do not collapse vague knowledge into exact targets before verification.

Do not treat groups as contracts. Tactical grouping and negotiated cooperation are separate layers.

Do not merge private narrative and public reputation into one score.

Do not expose raw domain models directly from API routes. Use presenters and schemas.

Do not add replay, metrics, and telemetry last. They are how you prove the system is working.

## 12. Recommended implementation checklist for every new feature

Before adding a feature, answer these questions:

What is the durable state record?
How is it represented as a typed model?
How does AI observe it through snapshot/context?
How are changes emitted as typed updates?
Where are those updates applied authoritatively?
How is deterministic ordering preserved?
How is it exposed in presenter/inspector surfaces?
How is it visible in replay, telemetry, or metrics?
What unit and integration tests prove the layer boundaries were preserved?

If you cannot answer those, the feature is not designed yet. It is just being coded.

Priority Plan

What must change in mindset or assumptions
Stop optimizing for “adding behavior quickly.” Optimize for preserving the architecture that already makes the engine survivable: immutable snapshots, authoritative updates, deterministic ordering, typed models, decoupled systems, and presenter-based read surfaces. That is the real leverage in this codebase.

What actions must be taken immediately
Write these conventions into the project docs, enforce them in code review, and make “typed durable state + authoritative update path + inspectability” the minimum bar for every strategic feature. Add missing strategic replay, presenter, and telemetry support early, not after the behavior layer is already sprawling.

What must stop or be eliminated
Stop using prose as state, stop using tactical shortcuts as strategic infrastructure, stop letting helpers mutate live state, and stop shipping features that cannot be inspected or replayed coherently.

The consequences and opportunity cost if this fails
You will end up with a richer-looking simulation whose core behavior is harder to reason about, harder to test, harder to replay, and easier to break. That is not progress. That is entropy with more files.
