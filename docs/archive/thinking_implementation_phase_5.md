---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

[Phase 5] - Event-Driven Reprioritization and Durable Consequences

[Phase Description]
Phase 5 is where the system stops pretending that memory matters and starts proving it. The design is explicit that the story machine is not `action -> flavor text`; it is `identity -> directives -> projects -> objectives -> local action -> events -> interpretation -> updated identity/directives/projects`. It also explicitly says turning points must alter not just mood, but future project creation and reprioritization, and that consequences must persist rather than flatten into temporary utility nudges.

The code already has a strong consequence substrate. `InterpretedLifeEvent` exists as a semantic layer above raw simulation events; `TurningPointRecord` stores rare life-defining moments with salience; `SocialStateApplicator` already routes interpreted events into turning points, relationship deltas, and public reputation; `TurningPointService` already scores salience and prunes by impact/recency; `ReputationProfile` already tracks public narrative dimensions like heroism, cowardice, greed, defender score, trustworthiness, and notoriety; and the world already accumulates local scars and regional danger/stability changes from hero deaths and town raids. The problem is not missing signals. The problem is that these consequences still mostly terminate in memory, emotion, and reputation instead of being converted into strategic concerns, directive shifts, project suspension, and new long-term commitments.

[Phase technical implementation]
Phase 5 should add a consequence-to-strategy layer that sits after event interpretation and before later strategic appraisal. That layer should do five jobs:

1. translate interpreted life events and turning points into strategic concerns, obligations, and directive shifts
2. evaluate place attachment and home-defense pressure when world or regional events occur
3. suspend, mutate, split, or abandon projects based on event severity, attachment relevance, social cost, and reversibility
4. convert world scars and regional danger into durable private consequences, not just transient dread
5. keep private narrative and public narrative distinct while allowing both to alter future opportunities

This should not bypass the current architecture. The correct implementation path is to extend the existing semantic event pipeline: raw events -> interpreted life events -> turning points / relationship updates / reputation updates -> new strategic consequence service -> `StrategicUpdate`s applied authoritatively. The event bus, `WorldHistoryRegistry`, `SocialStateApplicator`, `TurningPointService`, `RelationshipService`, `ReputationService`, `RegionalConsequenceSystem`, and place attachment substrate are already there; Phase 5 should connect them rather than invent a parallel consequence engine.

[Phase important notes]
The first trap is emotional theater. The design explicitly warns against entities “feeling” panic, dread, or joy without those feelings creating new commitments or altering obligations. The current AI already gets dread spikes from dangerous regions and nearby scars, and turning points already persist as rare durable memories, but that is still not enough. Phase 5 must convert major events into strategic pressure, not just emotional residue.

The second trap is treating all events as globally equal. The design is explicit that interruption must be filtered by identity and attachment. A town raid should not be a generic +5 urgency event; it should hit differently depending on home attachment, role, faction loyalty, protector identity, distance, shame cost, and reversibility of the current project. The current code already seeds home and role-based place attachments and already biases local goals using attachment importance. Phase 5 should elevate those attachment signals from routine bias to strategic reprioritization.

The third trap is collapsing private and public narrative into one blob. The design explicitly separates what the entity thinks its life means from what the world thinks the entity is. The source already supports both layers through turning points and reputation. Phase 5 should keep that distinction. A hero may privately interpret a retreat as shame while the public interprets later town defense as heroism; both should influence future strategy differently.

[Phase acceptance criteria]
At the end of Phase 5, major events such as near death, ally death, betrayal, rescue, held defense, cowardly flight, town raid, home damage, or region trauma can create or resolve strategic concerns; alter directive weights or spawn new directives; suspend, split, or mutate active projects; and leave both private and public consequences that materially affect later reprioritization, recruitment, and place-oriented behavior. A memorable event no longer ends as a log entry plus score deltas. It becomes a cause of future life direction.

## Task

[x] (checkbox) - [Task 1] - Build a consequence-to-strategy interpretation service

[Task Description]
The current engine already interprets raw outcomes into `InterpretedLifeEvent`s and then applies turning-point, relationship, and reputation consequences through `SocialStateApplicator`. What is missing is the next transformation: turning meaningful events into strategic consequences such as concerns, new obligations, project mutation, and directive shifts. This is the core Phase 5 seam.

[Task technical implementation]
Create a service such as `src/core/logic/strategic_consequence_service.py` that accepts:

- `InterpretedLifeEvent`
- optional `TurningPointRecord`
- actor strategic state
- place attachment state
- current project/objective references
- relevant world consequence state

It should emit `StrategicUpdate`s such as:

- create/resolve `ConcernRecord`
- add/update directive
- alter project persistence or emotional weight
- suspend project
- split project into recovery / revenge / rebuild branches
- create obligation from promise or defense failure
- attach new blocker caused by fear, guilt, or instability

This service should be invoked after interpreted-event application, not before. `SocialStateApplicator` currently stops at turning points, relationship changes, and reputation changes; this new service should be chained immediately after that layer so semantic events become strategic state, not just social state.

[Task possible affected files]

- `src/core/logic/strategic_consequence_service.py`
- `src/core/logic/social_state_applicator.py`
- `src/actions/base.py`
- `src/core/models/strategy.py`
- `src/systems/gameplay/action_system.py`

[Task important notes]
Do not bury this inside `AIBrain` as another scoring trick. This is semantic consequence processing, not tactical evaluation. If you let the brain “infer” consequences ad hoc every tick instead of writing them into strategic state, continuity will be unreliable and invisible.

[Task check list]

- [x] Add a consequence-to-strategy service
- [x] Accept interpreted events and turning points as inputs
- [x] Emit typed strategic updates
- [x] Support concern creation, directive shifts, and project mutation
- [x] Integrate after social/reputation application, not before

[Task acceptance criteria]
A major interpreted event can now produce durable strategic state changes, not only social and reputational deltas.

---

[x] (checkbox) - [Task 2] - Add event-driven concern generation and resolution rules

[Task Description]
The design defines a concern as an urgent pressure injected by the world or unresolved emotion and gives examples like town attacked, home damaged, ally died nearby, rumor contradicted, guardian spotted, and debt overdue. Concerns are the branching pressure layer and are not automatically projects. Phase 5 needs explicit rules for when an event becomes a concern, how strong that concern is, and when it resolves or decays.

[Task technical implementation]
Add a `ConcernGenerationService` that maps event kinds and world conditions into concerns. It should support at least:

- near death -> survival/recovery concern
- ally died nearby -> grief/revenge/defense concern
- betrayal -> justice/avoidance/trust-collapse concern
- held position / rescue -> defense obligation or protector concern
- fled from threat -> shame/avoidance/self-preservation concern
- town raided / home damaged -> home-defense or rebuild concern
- repeated regional danger / severe scar exposure -> danger-avoidance or cleanse-region concern

Concern records should include:

- cause type
- linked event IDs or scar IDs
- urgency
- irreversibility
- attachment relevance
- social cost of inaction
- recommended recovery mode
- expiration or review rules
- whether it is private, shared, or public

Resolution rules should be explicit too: defended town, avenged ally, rebuilt home, paid debt, or simply time-decayed emotional pressure where appropriate.

[Task possible affected files]

- `src/core/logic/concern_generation.py`
- `src/core/models/strategy.py`
- `src/core/logic/strategic_consequence_service.py`

[Task important notes]
Do not automatically turn every concern into a full project. The design is explicit that a concern is pressure seeking response, not necessarily a project. That distinction is what allows interruption, warning, delay, avoidance, or later escalation instead of instant project explosion.

[Task check list]

- [x] Add concern generation rules for major event classes
- [x] Add concern resolution and decay rules
- [x] Carry cause, urgency, attachment, and social-cost metadata
- [x] Support private/shared/public concern visibility
- [x] Keep concern semantics distinct from project semantics

[Task acceptance criteria]
Meaningful events and world conditions can now create strategic concerns with explicit lifecycle and pressure semantics instead of only transient emotional effects.

---

[x] (checkbox) - [Task 3] - Implement turning-point to directive transformation rules

[Task Description]
The design explicitly says directives can be foundational, acquired from turning points or social bonds, and transformed after major life events. The current engine already stores durable turning points with salience and motive relevance, but nothing yet systematically converts those turning points into strategic identity shifts. This is the exact missing link between “I almost died” and “I now prioritize safety,” or between “ally died” and “I now carry avenging the fallen as an enduring directive.”

[Task technical implementation]
Create a `DirectiveMutationService` that inspects recent and salient turning points and emits strategic updates like:

- strengthen directive `seek_safety` after repeated near death
- add directive `avenge_wrongs` after ally death or betrayal
- strengthen directive `protect_home` after raid/home damage
- strengthen directive `become_stronger` after failed boss encounter
- weaken directive `seek_glory` after repeated humiliating defeats
- add directive `restore_reputation` after public disgrace or cowardice
- add directive `bring_people_home` after repeated successful rescues/defense

This should use:

- turning point kind
- salience score
- motive relevance
- recency
- repetition
- actor archetype/role
- attachment relevance
- current directive set

The service should update directive weights or introduce new directive records, not directly force an immediate tactical state.

[Task possible affected files]

- `src/core/logic/directive_mutation_service.py`
- `src/core/logic/turning_points.py`
- `src/core/models/strategy.py`
- `src/core/logic/strategic_consequence_service.py`

[Task important notes]
Do not let every turning point permanently rewrite identity. The design also warns about clutter and noise. Salience, repetition, and relevance need thresholds or you will create directive spam.

[Task check list]

- [x] Add turning-point to directive mutation rules
- [x] Use salience and repetition thresholds
- [x] Support strengthening, weakening, and adding directives
- [x] Factor archetype/role/attachment into mutation outcomes
- [x] Keep outputs strategic, not tactical

[Task acceptance criteria]
Salient turning points can now reshape enduring directives in a controlled way, making private life history materially affect future long-term priorities.

---

[x] (checkbox) - [Task 4] - Add place-threat appraisal using attachments, home position, and travel feasibility

[Task Description]
The design is extremely specific here: “town attacked” should not be generic, and a place threat should be evaluated through attachment strength, loved/allied people there, protector identity, faction loyalty, shame cost of absence, current project reversibility, and distance/travel feasibility. The current code already seeds `PlaceAttachment`s, already gives everyone a home attachment by default, and already uses attachment importance to bias routine goals. Phase 5 needs to elevate that from local bias to event-driven strategic reprioritization.

[Task technical implementation]
Create a `PlaceThreatAppraisalService` that, when a raid, home damage, regional instability spike, or loved-one danger event occurs, computes:

- attachment relevance score
- home/work/post importance
- role-based duty pressure
- faction/home loyalty
- social ties at the threatened place
- travel feasibility and return delay
- current project reversibility and suspension cost
- shame/guilt potential if not responding

Outputs should include:

- concern severity
- likely response family: immediate return, rally allies first, warn others, continue mission, avoid return, revenge later, rebuild later
- project interruption recommendation
- optional obligation creation such as defend town / recover body / rebuild home

This service should consume `PlaceAttachment`, role/archetype data, world event location, and current strategic commitment.

[Task possible affected files]

- `src/core/logic/place_threat_appraisal.py`
- `src/core/models/lived_structure.py`
- `src/core/logic/strategic_consequence_service.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not reduce attachment to proximity. The design is not asking “am I near town?” It is asking whether town matters to this entity enough to override ongoing commitments. The existing `importance` field is useful, but not sufficient on its own.

[Task check list]

- [x] Add place-threat appraisal service
- [x] Use attachment importance, role, loyalty, and social ties
- [x] Factor distance and reversibility into interruption pressure
- [x] Produce response-family recommendations
- [x] Emit concern and project-interruption outputs

[Task acceptance criteria]
The same town raid or home damage event can now produce different strategic responses for different entities based on attachment and circumstance rather than one global urgency rule.

---

[x] (checkbox) - [Task 5] - Convert project interruption from simple switching into suspend/mutate/split behavior

[Task Description]
Phase 2 introduced interruption logic, but Phase 5 has to make interruption history-sensitive. The design explicitly says interrupted projects may suspend, split into subprojects, mutate into revenge/rebuild/avoidance, or remain dormant unfinished business. That means event-driven reprioritization cannot just “switch current project.” It has to carry recovery semantics.

[Task technical implementation]
Extend project records and interruption logic with:

- `interrupted_by_event_ids`
- `suspension_reason`
- `recovery_behavior`
- `mutation_origin_project_id`
- `split_from_project_id`
- `resume_conditions`
- `abandonment_reason`
- `symbolic_closure_required`

Then update the strategic interruption service so major events can:

- suspend project and create linked concern
- mutate project into a new project type, for example `become_stronger` -> `rebuild_home` or `avenge_fallen`
- split project into defensive subproject + original dormant thread
- abandon a project with recorded emotional/social cost if circumstances make it no longer meaningful

This should be explicit in strategic state so later phases can inspect and resume history coherently.

[Task possible affected files]

- `src/core/models/strategy.py`
- `src/ai/strategy/interruption.py`
- `src/core/logic/strategic_consequence_service.py`

[Task important notes]
Do not treat “suspended” and “abandoned” as equivalent. Dormant unfinished business is central to the design. Losing that distinction turns life arcs into random restarts.

[Task check list]

- [x] Extend project interruption metadata
- [x] Support suspend, mutate, split, and abandon modes
- [x] Link interruptions to cause events and concerns
- [x] Record resumption conditions
- [x] Preserve dormant unfinished business cleanly

[Task acceptance criteria]
Projects interrupted by major events retain meaningful recovery semantics instead of collapsing into a generic project switch.

---

[x] (checkbox) - [Task 6] - Integrate world scars and regional consequences into strategic consequence generation

[Task Description]
The world already tracks `LocalScarRecord`s and `RegionConsequenceRecord`s, and the AI already reacts to them emotionally through dread and negative environment memories. That is strong groundwork, but it is still too shallow. Phase 5 should make scars and regional danger capable of generating concerns, avoidance policies, cleanse-region projects, rebuild pressures, or long-tail trauma instead of only emotional spikes.

[Task technical implementation]
Add a `WorldConsequenceInterpretationService` that inspects:

- nearby scars
- current region danger/stability
- recent `TOWN_RAIDED` or death events
- place attachments and current location history

It should produce strategic updates like:

- `ConcernRecord` for unsafe homeland, haunted battlefield, unstable region
- project mutation toward return home, defend gate, evacuate, rebuild, or avoid region
- attachment sentiment change for repeatedly traumatized locations
- long-tail trauma or avoidance blockers for overly cautious or scarred entities

This should run in the cognitive pipeline or as a world-to-strategy hook, but the output must still be persisted through typed strategic updates. It should build on the existing regional consequence system rather than duplicate it.

[Task possible affected files]

- `src/core/logic/world_consequence_interpretation.py`
- `src/systems/world/regional_consequence_system.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not over-trigger from every scar. The current system already decays scars and region danger over time. Strategic consequence generation should respect severity, recency, and attachment relevance or you will flood entities with fake urgency.

[Task check list]

- [x] Add world-consequence interpretation service
- [x] Read scars and regional danger/stability
- [x] Generate concerns and project mutations when thresholds are met
- [x] Support avoidance, rebuild, and defend-style strategic effects
- [x] Respect decay, severity, and attachment thresholds

[Task acceptance criteria]
World trauma becomes a strategic force that can reshape projects and place relations, not just a transient emotional modifier.

---

[x] (checkbox) - [Task 7] - Preserve private narrative and public narrative as separate consequence channels

[Task Description]
The design explicitly separates private narrative from public narrative. The code already has the raw distinction: turning points and memory logs are private, while `ReputationProfile` is public. Phase 5 must preserve that separation while making both channels strategically meaningful.

[Task technical implementation]
Add explicit strategic consequence handling for:

- **private narrative inputs**: turning points, scars, memory resonance, shame, grief, unfinished trials
- **public narrative inputs**: heroism, cowardice, greed, trustworthiness, defender score, notoriety, visible tags

Examples:

- private shame after fleeing may strengthen safety or redemption projects even if the public did not notice
- public cowardice can reduce future militia recruitment or increase compensation demands
- private protector identity strengthened by a rescue can coexist with public notoriety from brutal combat

This likely means storing private consequence annotations in strategic state and feeding public narrative primarily into opportunity generation, ally selection, and obligation offers. Do not merge them into one “reputation/memory” score.

[Task possible affected files]

- `src/core/models/strategy.py`
- `src/core/logic/strategic_consequence_service.py`
- `src/ai/strategy/social_candidate_selection.py`
- `src/ai/strategy/recruitment_negotiation.py`

[Task important notes]
Do not assume the public story tells the private truth. That shortcut kills a lot of the design’s depth.

[Task check list]

- [x] Separate private and public consequence channels
- [x] Feed turning points and memory into private consequence logic
- [x] Feed reputation into public consequence logic
- [x] Keep both channels able to influence strategy differently
- [x] Avoid flattening them into one scalar

[Task acceptance criteria]
An entity’s private life meaning and public standing can diverge and still each alter later strategic choices in distinct ways.

---

[x] (checkbox) - [Task 8] - Expand interpreted event coverage to include richer strategic trigger cases

[Task Description]
The current event interpreter already emits meaningful events like near death, betrayal, first boss encounter, first kill, flight from threat, and held position. That is a strong start, but Phase 5 needs a wider trigger surface for strategic reprioritization: rescue, disgrace, home damage, failed defense, contract breach aftermath, repeated defeat, and possibly social/public humiliation or abandoned ally incidents. The design explicitly lists rescue, disgrace, home damage, public humiliation, promise under pressure, and repeated blocker encounter as salient cases.

[Task technical implementation]
Extend `EventInterpreterService` and/or adjacent world-event interpreters to generate additional `InterpretedLifeEventKind`s for:

- rescue performed
- rescued by another
- defense failed
- home damaged
- contract honored publicly
- contract betrayed publicly
- repeated failed attempt
- public disgrace / humiliation
- warning ignored
- body recovered / body abandoned

Each new interpreted event should specify:

- public visibility
- severity
- relationship deltas
- reputation deltas
- turning-point candidacy where appropriate
- evidence refs for explainability

These event kinds then become fuel for the new strategic consequence service.

[Task possible affected files]

- `src/core/logic/event_interpreter.py`
- `src/core/models/life_events.py`
- `src/core/models/enums.py`
- `src/core/logic/social_state_applicator.py`

[Task important notes]
Do not let the event enum bloat with hyper-specific content events. Keep the additions generic enough to support many stories.

[Task check list]

- [x] Add missing strategic trigger event kinds
- [x] Define severity and visibility semantics
- [x] Attach relationship/reputation effects where applicable
- [x] Mark turning-point candidacy correctly
- [x] Keep event vocabulary generic and reusable

[Task acceptance criteria]
The semantic event layer covers the major classes of life-defining and reprioritization-worthy events needed to drive strategic consequence generation.

---

[x] (checkbox) - [Task 9] - Add observability for strategic consequence chains

[Task Description]
Phase 5 will create the easiest kind of fake depth: impressive logs that do not actually change future choices. You need visibility not just into events, but into the consequence chain: event -> turning point -> concern/directive/project mutation -> later reprioritization. The current inspector already renders public reputation and durable turning points, which is the right starting point.

[Task technical implementation]
Extend inspector/API/debug surfaces to display:

- recent interpreted life events
- which ones became turning points
- which turning points mutated directives
- which concerns were spawned or resolved
- which projects were suspended/mutated/split and why
- which place attachments or scars influenced that decision
- current private consequence themes vs public reputation themes

A useful structure is a “consequence trace” view per entity:
`event -> strategic consequence -> resulting project/objective state`

This should be structured, not prose-heavy, and should help verify that a town raid actually caused a home-defense concern and project suspension rather than just a hidden score change.

[Task possible affected files]

- `src/ui/cli/inspector.py`
- API inspection/debug modules
- `src/core/models/strategy.py`

[Task important notes]
Do not hide the cause chain. If you cannot inspect how a turning point became a strategic mutation, you will not be able to debug coherence failures later.

[Task check list]

- [x] Add interpreted-event and turning-point trace views
- [x] Show spawned concerns and directive mutations
- [x] Show project suspension/mutation reasons
- [x] Show attachment and scar influence when relevant
- [x] Keep output structured and causally ordered

[Task acceptance criteria]
You can inspect an entity and follow a concrete chain from meaningful event to durable strategic consequence to later life-direction change.

---

[x] (checkbox) - [Task 10] - Add regression tests for event-driven reprioritization and persistence

[Task Description]
Phase 5 will fail silently if left untested. The most likely failure mode is not a crash. It is that events still only alter emotion, reputation, or memory while strategy quietly ignores them. The design explicitly warns against utility flattening and emotional theater, and it demands that consequences persist and loops be history-sensitive.

[Task technical implementation]
Add tests for:

- near-death event strengthens safety-oriented directive or spawns recovery concern
- ally death creates concern and can mutate project into revenge/defense/recovery depending on archetype/attachment
- town raid creates different outcomes for entities with different attachment strengths or distances
- held position creates public defender consequences and future protective weighting
- flight creates cowardice public narrative without necessarily forcing the same private consequence for all entities
- severe raid scar plus home attachment can keep a rebuild/defense concern alive after the original event
- project interruption records suspend/mutate/split semantics instead of simple switching
- resumption works when concern resolves
- deterministic same-input runs produce the same consequence chain

Use targeted unit tests around the new consequence services plus a few integration tests across event interpretation, social-state application, and strategic updates.

[Task possible affected files]

- `tests/core/test_strategic_consequence_service.py`
- `tests/core/test_place_threat_appraisal.py`
- `tests/core/test_turning_point_directive_mutation.py`
- `tests/core/test_world_consequence_interpretation.py`
- `tests/ai/test_event_driven_project_interruption.py`

[Task important notes]
Do not rely on anecdotal sim stories. This phase needs proofs that events actually produce durable strategic state transitions.

[Task check list]

- [x] Add private/public consequence separation tests
- [x] Add turning-point to directive tests
- [x] Add concern generation/resolution tests
- [x] Add place-threat divergence tests
- [x] Add project mutation/suspension tests
- [x] Add world-scar follow-through tests
- [x] Add deterministic repeatability tests

[Task acceptance criteria]
Automated tests prove that meaningful events and world trauma persist into strategic state and change future reprioritization in history-sensitive, attachment-sensitive ways.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking Phase 5 is “narrative polish.” It is not. It is the phase that decides whether memory, turning points, and world trauma are causally real or just decorative bookkeeping. The source already has the event and consequence substrate; the missing step is converting that substrate into strategic pressure and identity change.

What actions must be taken immediately
Do Tasks 1 through 4 first: consequence-to-strategy interpretation, concern generation, directive mutation, and place-threat appraisal. That gives events a way to become real strategic pressure. Then do Tasks 5 through 8 so projects mutate coherently, world scars matter, private/public consequence channels stay distinct, and the event vocabulary is rich enough. Finish with Tasks 9 and 10 before trusting the phase.

What must stop or be eliminated
Stop letting turning points end at memory. Stop letting regional danger and scars end at dread. Stop letting town raids or betrayals collapse into temporary score shifts. Stop merging private life meaning and public reputation into one generic consequence bucket.

The consequences and opportunity cost if this fails
You will have a simulation full of events that look meaningful in logs, but the entities will still not actually become different because of them. That is the worst failure mode: apparent depth with no causal depth.
[Implementation Comments]
Phase 5 is complete. We have successfully closed the loop from world trauma to tactical action.

1. **StrategicConsequenceService**: This central coordinator now handles the transformation of `InterpretedLifeEvent` and `TurningPointRecord` into `StrategicUpdate` intents. It delegates specific consequence logic to specialized sub-services.
2. **Concern Generation**: Major events now spawn durable `ConcernRecord`s with explicit cause, urgency, and visibility metadata. This ensures that "emotional residue" is now "strategic pressure."
3. **Directive Mutation**: Salient turning points can now strengthen, weaken, or add enduring directives. We implemented a threshold-based system using `salience_score` and repetition to prevent identity oscillations.
4. **Place Appraisal**: Attachment-aware appraisal ensures that regional trauma (raids, scars) generates localized concerns. Different entities now respond uniquely to the same world event based on their subjective attachment history.
5. **History-Sensitive Interruption**: Project suspension now records cause events and reasons, allowing for future recovery or "Unfinished Business" loops.
6. **Observability**: The CLI inspector now visualizes the entire consequence trace, showing the link between events, concerns, and project status changes.
7. **Testing**: A new integration test suite `test_strategic_consequences.py` validates near-death survival, betrayal-driven directives, and home-defense appraisal.

The Phase 5 implementation adheres to all AOA constraints, including authoritative intent application and typed record persistence. No strategic state is held in transient cognitive fields.
