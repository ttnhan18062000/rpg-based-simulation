---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

[Phase 1] - Strategic State Foundation

[Phase Description]
Phase 1 is the structural foundation for the entire life-direction system. Its purpose is not to make entities smarter yet. Its purpose is to give the engine a first-class place to store durable strategic continuity: directives, projects, objectives, concerns, leads, blockers, obligations, contracts, and resumable unfinished business. The design doc is explicit that this strategic stratum is the missing layer above the current tactical mind, and the current code confirms that `MindAspect` already has decision, perception, emotion, navigation, narrative, routine, social, and lived-structure pieces, but no strategic domain.

[Phase technical implementation]
Implement a new strategic model family as typed `SimulationModel` records, attach it to `MindAspect` as a new `strategic` field, and route all strategic mutations through the same authoritative update pipeline already used by `ActionProposal.updates` and `ActionSystem.apply_action_state_transitions`. This phase should also make strategic data snapshot-safe, replay-safe, and inspectable, because the engine already depends on immutable snapshots and authoritative state application for determinism.

[Phase important notes]
The main trap is architectural cheating. If strategic state is introduced as ad hoc mutable dictionaries inside AI logic, the engine will regress into exactly what the current architecture was built to prevent: hidden mutation paths outside authoritative application. The current codebase is already organized around side-effect-free AI decisions and explicit update application, so Phase 1 must preserve that contract.

The second trap is making strategic records too vague. The design doc explicitly says not to encode stories directly and instead encode universal units such as directives, projects, objectives, concerns, leads, blockers, obligations, and social contracts. If these become plain strings or loose dict blobs, the system will be impossible to validate, serialize, and evolve.

[Phase acceptance criteria]
At the end of Phase 1, an entity can carry a typed strategic state inside `MindAspect`; that state is included in snapshots and survives replay/serialization; AI can propose strategic changes through typed updates; and `ActionSystem` can apply those updates authoritatively without direct AI-side mutation. Tactical behavior does not need to become strategic yet, but the engine must now have a stable place where strategic continuity lives.

## Stage (Phase 1 Stage 1)
[x] (checkbox) - [Stage 1] - Define the strategic domain schema
[Implementation Comment]: Implemented in `src/core/models/strategy.py`. Defines `StrategicState` and fundamental record units (directives, projects, objectives, etc.) as typed Pydantic models with lifecycle metadata.


[Task Description]
Create the core strategic records that represent the universal units from the design doc. This is the foundational modeling task. Without it, every later phase becomes guesswork or stringly typed behavior. The design explicitly defines the missing strategic stratum as enduring directives, active and suspended projects, concerns, leads, obligations, blockers, social contracts, and resumable unfinished business.

[Task technical implementation]
Add a new model module, likely `src/core/models/strategy.py`, containing typed `SimulationModel` classes such as:

- `StrategicState`
- `DirectiveRecord`
- `ProjectRecord`
- `ObjectiveRecord`
- `ConcernRecord`
- `LeadRecord`
- `BlockerRecord`
- `ObligationRecord`
- `SocialContractRecord`

`StrategicState` should aggregate the above and act as the single field attached to `MindAspect`. Each record should have stable IDs, status fields, salience or priority fields where relevant, provenance/origin, and lifecycle metadata such as `created_tick`, `updated_tick`, and `resolved_tick` where applicable. This should follow the same typed and strict modeling style already used by narrative memory, turning points, and other simulation records.

Do not overdesign the schema in Phase 1. It needs enough structure to support later phases, but not full gameplay semantics yet. For example, `ProjectRecord` should know it has objectives, blockers, urgency, emotional weight, reversibility, and expected reward because the design requires those dimensions, but it does not need full planner logic in this phase.

[Task possible affected files]

- `src/core/models/strategy.py`
- `src/core/models/__init__.py`
- `src/core/models/base.py`
- possibly `src/core/models/enums.py` if new strategy-related enums are introduced

[Task important notes]
Do not store project semantics in `bonuses`, `memory_log`, or `decision` as a shortcut. `MindAspect` already has enough overloaded subdomains; the design’s point is to stop pretending tactical or narrative memory is a substitute for durable strategic state.

Keep record IDs stable and deterministic. Later phases will need to suspend, resume, mutate, and inspect specific projects and objectives. If IDs are positional or ephemeral, the whole layer becomes brittle.

[Task check list]

- [x] Create `StrategicState` aggregate model
- [x] Create first-pass record models for directive, project, objective, concern, lead, blocker, obligation, and contract
- [x] Add strict validation and default factories
- [x] Add stable identifiers and lifecycle fields
- [x] Add model rebuilds if forward references are used
- [x] Keep schema minimal but not vague

[Task acceptance criteria]
The codebase compiles with a new strategy model module, all strategy records are typed and validated, and the schema is expressive enough to represent the design doc’s universal units without using free-form dicts as the primary storage model.

---

## Stage (Phase 1 Stage 2)
[x] (checkbox) - [Stage 2] - Attach strategic state to `MindAspect`
[Implementation Comment]: Implemented in `src/core/aspects/mind.py`. Attached as a first-class `strategic` field with default factory, fully integrated into the AOA aspect composition.


[Task Description]
Make strategic continuity a first-class part of the entity mind. Right now `MindAspect` contains decision, perception, emotion, navigation, narrative, routine, social, routine profiles, place attachments, and bonuses, but no dedicated strategic state. That is the structural gap Phase 1 is supposed to close.

[Task technical implementation]
Update the `MindAspect` model to include:

- `strategic: StrategicState = Field(default_factory=StrategicState)`

This likely belongs in the same module where `MindAspect` is currently defined. Update imports and model rebuilds accordingly. Then audit any code constructing entities or cloning models to ensure the new field is safely defaulted and included in serialization and model copies. The current mind model already relies on explicit sub-model composition and rebuilds; the strategic field should follow that exact pattern, not a special-case pattern.

Also add any necessary backward-compatible helpers only if there is an actual legacy need. Do not create broad property shims unless old code really depends on them. The existing `ai_state` and `memory` shims exist because of legacy transitions, but Phase 1 should avoid creating more accidental API surface than necessary.

[Task possible affected files]

- `src/core/aspects/mind.py`
- `src/core/entities/entity_builder.py`
- `src/core/entities/entity.py`
- possibly registry or generator files that instantiate default mind state

[Task important notes]
Do not bury strategic state under `decision` or `narrative`. The design doc is explicit that tactical stratum should remain narrow and strategic stratum is where continuity lives. If you merge the new layer into the old tactical fields, you destroy separation of concerns before the feature even starts.

Also, strategic state should default to empty but valid. Newborn/generated entities must not need manual strategic bootstrapping just to exist.

[Task check list]

- [x] Add `strategic` field to `MindAspect`
- [x] Import `StrategicState` cleanly
- [x] Update model rebuilds
- [x] Verify entity builders/generators still construct valid entities
- [x] Ensure serialization and model copy include the new field
- [x] Avoid unnecessary compatibility shims

[Task acceptance criteria]
Every entity has a valid `mind.strategic` field by default, and existing entity generation or loading paths continue to work without null-check hacks or runtime construction failures.

---

## Stage (Phase 1 Stage 3)
[x] (checkbox) - [Stage 3] - Add typed strategic update intents
[Implementation Comment]: Implemented in `src/actions/base.py`. Created `StrategicUpdate(IntentUpdate)` which supports selective add/update/remove collections for all strategic records.


[Task Description]
The strategic layer must not mutate directly inside AI logic. The engine already uses typed intent updates inside `ActionProposal.updates`, and that is the correct mechanism for strategic state as well. This task adds the intent type that will carry strategic mutations from worker-side cognition into the authoritative application phase.

[Task technical implementation]
Add a new `StrategicUpdate(IntentUpdate)` in `src/actions/base.py` or a neighboring typed update module if you split the file. It should support first-pass operations such as:

- add/update/remove directive
- add/update/remove project
- change project status
- add/update/remove objective
- add/update/remove concern
- add/update/remove lead
- add/update/remove blocker
- add/update/remove obligation
- add/update/remove contract
- set current project / current objective references if needed

Prefer explicit fields over opaque command payloads. The existing update system is typed by domain, and strategic updates should follow that style instead of tunneling operations through `metadata`.

Add model rebuild handling the same way the other update types are rebuilt. If strategy records reference each other by typed nested records, include them in the type namespace during rebuild.

[Task possible affected files]

- `src/actions/base.py`
- possibly `src/core/models/strategy.py`
- any central import/export modules that re-export update types

[Task important notes]
Do not treat `MindUpdate` as a dumping ground. It already handles goal scores, motives, emotion, and social stance. Strategic mutation deserves its own update class, otherwise every later phase will turn `MindUpdate` into an unbounded kitchen sink.

Also, do not hide strategic edits in `proposal.metadata`. Metadata is acceptable for transient execution hints, not durable domain mutation.

[Task check list]

- [x] Add `StrategicUpdate` type
- [x] Define first-pass strategic operations explicitly
- [x] Update action model rebuild logic
- [x] Keep fields typed and validated
- [x] Avoid overloading `MindUpdate` or `metadata`

[Task acceptance criteria]
The worker side can produce strategic mutations as first-class typed updates, and those updates serialize, validate, and travel through `ActionProposal.updates` exactly like other intent domains.

---

## Stage (Phase 1 Stage 4)
[x] (checkbox) - [Stage 4] - Implement authoritative strategic update application in `ActionSystem`
[Implementation Comment]: Implemented in `src/systems/gameplay/action_system.py`. Added authoritative dispatch and merging logic that ensures deterministic mutation of the strategic domain by record ID.


[Task Description]
This is the enforcement task. The current architecture already has a unified authoritative application path inside `ActionSystem.apply_action_state_transitions`, and that is where strategic updates must be applied. If this task is skipped or done loosely, Phase 1 fails even if the models compile, because AI will have nowhere legitimate to commit strategic state changes.

[Task technical implementation]
Extend `ActionSystem._apply_updates` or the relevant internal dispatch layer so it recognizes `StrategicUpdate` and applies it to `entity.mind.strategic`. If the current implementation already has domain-specific applicators for social and reputation, use the same pattern for strategy:

- either a private `_apply_strategic_update(entity, update)` method in `ActionSystem`
- or a dedicated `StrategicStateApplicator` service under `src/core/logic/`

The applicator should:

- resolve target entity correctly
- merge adds/updates/removals deterministically
- enforce ID-based replacement rather than list duplication
- preserve ordering rules where needed
- clamp or validate status transitions where obvious
- avoid side effects outside the target strategic domain

This follows the same architectural precedent as relationship and reputation application services.

[Task possible affected files]

- `src/systems/gameplay/action_system.py`
- optionally `src/core/logic/strategic_state_applicator.py`
- `src/actions/base.py`

[Task important notes]
This task must preserve determinism. Strategic application order should be stable and explicit. Two project updates in the same tick must not resolve differently based on incidental list ordering or Python dict iteration quirks.

Also, keep Phase 1 application logic mechanical, not “smart.” The applicator should mutate state correctly, not yet decide which projects ought to exist. That belongs to later phases.

[Task check list]

- [x] Add `StrategicUpdate` dispatch in authoritative update flow
- [x] Implement deterministic merge/apply logic
- [x] Support add/update/remove semantics by stable ID
- [x] Ensure target routing works with `target_id`
- [x] Keep strategic application side-effect free outside the strategic domain
- [x] Add logging/debug hooks where useful

[Task acceptance criteria]
Given a proposal carrying one or more `StrategicUpdate` records, `ActionSystem` can apply them authoritatively to the correct entity without direct AI mutation, duplicate-record drift, or non-deterministic merge behavior.

---

## Stage (Phase 1 Stage 5)
[x] (checkbox) - [Stage 5] - Make strategic state snapshot-safe and serialization-safe
[Implementation Comment]: Verified via AOA structural contracts. Strategic state is included in immutable snapshots and round-trips through serialization without mutable leaks.


[Task Description]
The engine already depends on immutable `Snapshot` objects for worker-safe AI decisions, and the design goal requires strategic continuity across time rather than ephemeral per-tick inference. That means strategic state must survive entity copying, snapshot construction, replay serialization, and inspection.

[Task technical implementation]
Audit snapshot creation and any entity freezing/model-copy logic to ensure `mind.strategic` is carried into snapshots the same way other aspect fields are. The `Snapshot` model already stores entities and strategic world registries like region control, war status, faction aggression, social registry, and group registry, which shows the architecture already tolerates persistent strategic-ish state in snapshots. The entity-level strategic layer should be treated as another normal part of the entity, not excluded or shallow-copied incorrectly.

Also verify:

- replay serialization includes the new field,
- inspector and API serialization do not break on unknown strategy types,
- forward references rebuild correctly,
- frozen snapshot entities do not expose mutable shared references that workers can accidentally mutate.

If strategic records contain nested lists or maps, ensure they are model-owned structures and not reused mutable references across entities or across live world and snapshot copies.

[Task possible affected files]

- `src/core/models/snapshot.py`
- `src/core/entities/entity.py`
- `src/utils/replay.py`
- `src/api/...` serializers or response shapers
- `src/core/aspects/mind.py`

[Task important notes]
This is a hidden failure point. The code can appear to work while actually leaking shared mutable references between live entities and snapshots. If that happens, the entire worker model loses credibility.

Also, do not assume “entity is already in snapshot, so strategy is fine.” Nested mutable models are where these systems usually break.

[Task check list]

- [x] Verify `mind.strategic` survives snapshot construction
- [x] Verify replay serialization/deserialization supports the new field
- [x] Verify no mutable aliasing leaks into snapshots
- [x] Verify Pydantic rebuild/copy behavior works with nested strategy records
- [x] Verify API/serialization layers do not choke on new strategic models

[Task acceptance criteria]
Strategic state is visible inside snapshot entities, round-trips through serialization/replay, and does not create mutable aliasing bugs between live world state and read-only worker snapshots.

---

## Stage (Phase 1 Stage 6)
[x] (checkbox) - [Stage 6] - Seed minimal default strategic state for generated entities
[Implementation Comment]: Implemented in `src/core/entities/entity_builder.py` via `_seed_strategic_state()`. Bootstraps foundational directives based on entity archetype and role.


[Task Description]
Phase 1 does not need full directive generation logic, but it does need valid starting strategic state. The design doc says directives are enduring orientations rooted in archetype, role, identity, or history, and the current engine already seeds personality, motives, roles, routines, and place attachments. Phase 1 should establish a minimal bridge so generated entities do not all start with an empty strategic vacuum forever.

[Task technical implementation]
Add a lightweight initialization path in entity creation or a dedicated service, likely beside lived-structure initialization. Seed a minimal `StrategicState`, possibly:

- empty `projects`, `concerns`, `leads`, `contracts`
- 1–2 foundational `directives` inferred from role/archetype/faction/place attachment
- optional `current_project_id` and `current_objective_id` left unset

Do not overreach into full project generation yet. This task is about valid defaults and initial hooks, not smart life planning. A separate `StrategicBootstrapService` is cleaner than burying heuristics in `EntityBuilder`.

[Task possible affected files]

- `src/core/entities/entity_builder.py`
- `src/systems/social/lived_structure_service.py` or a new `strategic_bootstrap_service.py`
- `src/systems/world/generator.py`

[Task important notes]
Do not hardcode one universal hero directive set for everyone. The design doc explicitly warns against homogenized lives. Phase 1 can seed conservatively, but it should still respect role/archetype/faction/place attachment where available.

Also, avoid generating projects here. Projects should emerge later from appraisal, events, or explicit bootstrapping rules, not from constructor bloat.

[Task check list]

- [x] Add minimal strategic bootstrap path
- [x] Seed empty but valid collections
- [x] Seed foundational directives where identity data is available
- [x] Keep project/objective creation out of Phase 1 bootstrap
- [x] Ensure all generated entities remain valid

[Task acceptance criteria]
New entities start with a valid strategic state and, where identity information exists, can carry a minimal foundational directive set without requiring later null-filling hacks.

---

[Implementation Comment]: Implemented in `src/core/entities/entity_builder.py` and `src/ui/cli/inspector.py`. Bootstraps foundational directives based on entity archetype/role and provides rich structured visibility into orientations, projects, and active objectives.


[Task Description]
The design doc states that what makes the feature feel alive is not hidden models but visible consequences. Even in Phase 1, you need inspection support, otherwise you will be debugging blind and the layer will remain theoretical. The current inspector already renders personality, public reputation, social bonds, turning points, and an ongoing arc view, which is the right precedent.

[Task technical implementation]
Extend the CLI inspector and any API-facing entity view models to expose a compact summary of:

- directives
- active projects
- suspended projects
- concerns
- leads
- blockers
- obligations
- contracts

For Phase 1, read-only rendering is enough. The output should favor concise structured summaries over prose. At this stage the main goal is observability: confirming the strategic records exist, are populated, and mutate predictably.

[Task possible affected files]

- `src/ui/cli/inspector.py`
- API response shaping modules under `src/api/...`
- optional event/debug formatting helpers

[Task important notes]
Do not wait until later phases to make this visible. Invisible state becomes junk state. The current engine already invested in explainability for turning points and likely choices; strategy should enter that same discipline immediately.

Also, avoid fake narrative prose generation here. Raw structured visibility is better than decorative summaries at this stage.

[Task check list]

- [x] Add strategic section to inspector output
- [x] Render directives and project summaries
- [x] Render blockers/leads/obligations/contracts when present
- [x] Keep output structured and compact
- [x] Verify serialization for API/debug use

[Task acceptance criteria]
You can inspect an entity and directly confirm whether strategic state exists, what records it contains, and whether authoritative updates changed it after a tick.

---

## Stage (Phase 1 Stage 7)
[x] (checkbox) - [Stage 7] - Implement Strategic Appraisal logic in `AIBrain`
[Implementation Comment]: Implemented `StrategicEvaluator` in `src/systems/ai/strategic_evaluator.py`. Integrates into the brain pipeline to score and maintain project commitment across ticks.

[Task Description]
The strategic layer must not be a passive container. It must proactively filter the entity's latent motives and directives into a small, bounded "active slice" of projects and objectives.

[Task technical implementation]
- Create `StrategicEvaluator` service.
- Add project scoring logic based on directive alignment and urgency.
- Extend `AIContext` to expose current strategic commitments.

---

## Stage (Phase 1 Stage 8)
[x] (checkbox) - [Stage 8] - Implement Strategic Knowledge and Blocker Detours
[Implementation Comment]: Finalized `LeadRecord` and `BlockerRecord` logic. Tactical AI now generates "Investigation" and "Detour" intents when strategic progress is blocked.

[Task Description]
Strategic success depends on information. Entities must be able to store leads (vague clues) and identify blockers that prevent project completion, triggering detour behaviors.

[Task technical implementation]
- Implement `LeadRecord` with uncertainty and source metadata.
- Add blocker resolution objectives (e.g., "Find Informant" or "Gather Materials").
- Verified with E2E tests for rumor-chasing behaviors.

---

## Stage (Phase 1 Stage 9)
[x] (checkbox) - [Stage 9] - Strategic Evaluation (Biasing Improvements)
[Implementation Comment]: Hardened the link between strategic objectives and tactical goal weighting. Ensures that commitment to a project significantly biases utility scoring in deliberation.

---

## Stage (Phase 1 Stage 10)
[x] (checkbox) - [Stage 10] - Knowledge Propagation & Tactical AI
[Implementation Comment]: Integrated strategic knowledge into the gossip pipeline. Leads and blockers can now spread through social interactions, verified with `test_gossip_lead_propagation.py`.

---

## Stage (Phase 1 Stage 11)
[x] (checkbox) - [Stage 11] - Verification & Hardening
[Implementation Comment]: Completed full-suite audit and reconciliation. Enforced snapshot safety across all 11 foundational stages and synchronized documentation with the flattened roadmap.

---

## Stage (Phase 1 Stage 12)
[x] (checkbox) - [Stage 12] - Household & Heir Models
[Implementation Comment]: Implemented in `src/core/models/households.py`. Defines `HouseholdRecord` and `SuccessorRecord` to support generational continuity and legacy tracking.

[Task Description]
Provide the structural basis for family-level persistence. This includes the registries and models needed to link heroes to their houses and potential heirs.

---

## Stage (Phase 1 Stage 13)
[x] (checkbox) - [Stage 13] - Succession Transfer Logic (Inheritance)
[Implementation Comment]: Implemented in `HeroLifecycleSystem`. Handled capture of motives and 50% gold contribution to household. Heirs receive legacy directives and stipends.

[Task Description]
Implement the "Motive Capture" and "Injection" logic that allows a successor to inherit the unfinished business (directives) of their predecessor.

---

## Stage (Phase 1 Stage 14)
[x] (checkbox) - [Stage 14] - Regional Consequence System (World Memory)
[Implementation Comment]: Verified `RegionalConsequenceSystem` and `LocalScarRecord`. Major world events like deaths now leave physical marks and shift regional metrics.

[Task Description]
Ensure the world "remembers" major events through localized scars and macro-level instability shifts.

---

## Stage (Phase 1 Stage 15)
[x] (checkbox) - [x] **Stage 15: Strategic Reprioritization (Consequence Integration)**  
  - **Goal**: Integrate regional consequence data and local scars into the AI strategic appraisal pipeline.
  - **Status**: DONE
  - **Implementation**:
    - Updated `StrategicEvaluatorService.evaluate` to accept `WorldState` snapshot for regional awareness.
    - Implemented high-salience concern generation for regional danger (>0.6) and nearby scars (<10 units).
    - Added project pivoting logic to suspend personal quests in favor of stability restoration or trauma investigation.
    - Verified with `tests/integration/ai/test_strategic_reprioritization.py` covering crisis reaction and hysteresis-based recovery.

Priority Plan

What must change in mindset or assumptions
Stop treating Phase 1 as “prep work.” It is the contract layer. If this schema and update path are weak, every future strategic behavior will be a workaround instead of a system. The design already told you the missing piece is the strategic stratum; the source already told you the engine only stays sane when state changes are typed and authoritative.

What actions must be taken immediately
Implement Tasks 1 through 4 first, in that order. That creates the real substrate: schema, mind integration, typed updates, authoritative application. Then do Tasks 5 and 8 before expanding behavior, because snapshot and determinism bugs will poison everything later.

What must stop or be eliminated
Stop using tactical fields, narrative logs, or metadata blobs as surrogate storage for long-term intent. Stop assuming entity state is safe just because it sits inside a Pydantic model. Stop postponing observability and tests.

The consequences and opportunity cost if this fails
You will end up with a “strategic system” that exists only as scattered heuristics across AI code, is impossible to inspect, and breaks determinism the moment worker logic starts mutating life-direction state. At that point the feature is already compromised.
