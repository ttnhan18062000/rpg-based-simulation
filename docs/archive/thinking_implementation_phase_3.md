[Phase 3] - Uncertainty, Leads, and Blocker-Driven Investigation

[Phase Description]
Phase 3 turns strategic intent into actual investigation instead of fake omniscience. The design is explicit: uncertainty must create investigative behavior, not paralysis, and vague leads must not collapse into exact coordinates. A lead should remain uncertain, partial, and source-shaped; a blocker should create detours rather than dead ends; and the engine should be able to traverse the generic pattern of pursuit -> investigation -> blocker -> detour -> retry without authoring bespoke quest trees.

The current code already has the raw ingredients, but they are fragmented and too tactical. `BeliefService` already supports direct versus indirect knowledge, confidence, source confidence, directness, staleness, and gossip-style propagation, which is exactly the right substrate for uncertainty. But that substrate is still focused on entity beliefs, not on uncertain knowledge about places, materials, routes, candidate regions, or blockers. Meanwhile, the guild currently reveals terrain memory and adds string goals, the blacksmith exposes missing materials only through reason strings, the class hall exposes skill and breakthrough opportunities procedurally, and inn gossip copies beliefs between heroes. That means information exists, but it is not yet represented as durable strategic knowledge.

[Phase technical implementation]
Phase 3 should introduce a dedicated strategic knowledge layer built around typed leads, hypotheses, candidate zones, search history, contradiction handling, and blocker inference. It should not overload `BeliefRecord`, because `BeliefRecord` is already optimized for subjective entity perception. Instead, add a parallel set of strategic records under the Phase 1 strategic domain:

- `LeadRecord`
- `HypothesisRecord`
- `CandidateZoneRecord`
- `InvestigationRecord` or `SearchTraceRecord`
- `BlockerRecord` extensions for knowledge, capability, access, social, timing, and obligation blockers

Then add services that do four jobs:

1. ingest uncertain information from guilds, class halls, blacksmiths, quests, world observation, and gossip
2. convert that information into leads and hypotheses instead of exact targets
3. infer blockers when projects or objectives cannot proceed
4. spawn investigation or detour objectives that Phase 2 can select and Phase 2 tactical translation can execute

This phase should also refactor current intel-producing building handlers so they emit strategic leads/blockers, not only `terrain_memory`, `goals_add`, or reason strings. The guild is already revealing camp/resource locations and material hints; the blacksmith already knows what materials and gold are missing; the class hall already knows when a breakthrough is or is not possible. Those are precisely the producers that should be upgraded into structured strategic knowledge.

[Phase important notes]
The first trap is certainty collapse. Right now some systems leak highly usable information too directly. The guild reveals concrete terrain memory and material tips, inn gossip can copy full entity beliefs, and blacksmith/class-hall logic can immediately drive local actions. That is useful tactically, but if Phase 3 simply wraps those outputs in new names while preserving the same precision, the investigation layer will be fake. A vague clue must remain vague until it is narrowed through search, verification, consultation, or direct observation.

The second trap is using blocker records as static failure labels. The design is explicit that blockers are story fuel. Their job is to produce detours: gather more information, train, get money, recruit help, find another route, wait for a better time, or reinterpret the project. If the blocker system only says “not possible,” the feature is dead on arrival.

The third trap is overloading `BeliefRecord` until it becomes a garbage can. `BeliefRecord` already holds entity-facing fields like apparent role, faction, injury, reputation tags, threat estimate, confidence, directness, and source confidence. That should remain the subjective entity-perception layer. Leads and candidate zones are different objects with different lifecycle rules and must stay separate.

[Phase acceptance criteria]
At the end of Phase 3, an entity can receive uncertain information from buildings, NPC interactions, or gossip; store it as structured leads rather than raw prose or exact coordinates; track candidate zones and tested interpretations; infer blockers when a project cannot safely or confidently advance; and spawn detour or investigation objectives that preserve uncertainty until it is resolved by evidence. Guild intel, class-hall advice, blacksmith constraints, and inn gossip all feed the same strategic knowledge pipeline instead of each inventing their own one-off behavior.

## Task

[x] (checkbox) - [Task 1] - Define strategic knowledge models for leads, hypotheses, and candidate zones

[Task Description]
The current engine has strong subjective entity beliefs, but Phase 3 needs a second knowledge family for uncertain non-entity knowledge: possible regions, rumored materials, implied threats, partial routes, and unverified claims. The design explicitly says beliefs should cover things like “where might the flower be,” “which region is likely relevant,” “how strong is the guardian likely to be,” and “which guide is reliable,” and that a lead must carry source, certainty, freshness, directness, interpreted meaning, candidate places/entities/topics, and tested status.

[Task technical implementation]
Extend the Phase 1 strategy model module with:

- `LeadRecord`
- `HypothesisRecord`
- `CandidateZoneRecord`
- `SearchTraceRecord` or `InvestigationHistoryRecord`

`LeadRecord` should include:

- `lead_id`
- `subject`
- `source_type`
- `source_entity_id` or producer reference
- `certainty`
- `freshness_tick`
- `directness`
- `source_confidence`
- `semantic_tags`
- `interpreted_meaning`
- `related_project_ids`
- `tested`
- `contradicted`
- `candidate_zone_ids`
- `candidate_entity_ids`
- `candidate_topic_ids`

`CandidateZoneRecord` should include:

- zone identity or derived criteria
- region tags such as mountain, swamp, ruins, camp-adjacent
- confidence score
- supporting lead IDs
- contradiction count
- last_searched_tick
- search outcome summary

Keep them inside `StrategicState`, not in `PerceptionAspect`, because they serve durable strategic investigation rather than low-level sensing.

[Task possible affected files]

- `src/core/models/strategy.py`
- `src/core/aspects/mind.py`
- `src/actions/base.py`

[Task important notes]
Do not reuse `BeliefRecord` for this just because it already has confidence fields. That is lazy and wrong. `BeliefRecord` is for perceived entities; leads and candidate zones need very different identity, provenance, and lifecycle semantics.

[Task check list]

- [x] Add `LeadRecord`
- [x] Track `visited_tiles` in `CandidateZoneRecord`
- [x] Implement logic to "narrow" search space based on visited tiles
- [x] Update `InvestigateHandler` to use search history for tile selection
- [x] Prevent redundant checking of empty tiles
- [x] Resolve/Exhaust zones after sufficient searching

[Task acceptance criteria]
The engine can represent uncertain strategic knowledge as first-class typed records without abusing `BeliefRecord`, `terrain_memory`, or string goals.

---

[x] (checkbox) - [Task 2] - Extend blocker semantics from status flags to investigation and detour inputs

[Task Description]
The design says blockers are not failures; they are story fuel. A blocker should answer what type of blockage exists and what detour families are appropriate. The current code already exposes blocker-shaped information, but mostly as procedural branches or string reasons: blacksmith logic spells out missing materials and gold in a reason string, class-hall progression is gated by capability checks, and strategic continuity from Phase 2 can already suspend projects. What is missing is typed blocker inference that can be reused across projects and objective derivation.

[Task technical implementation]
Expand `BlockerRecord` to explicitly support:

- knowledge blocker
- capability blocker
- access blocker
- social blocker
- timing blocker
- obligation blocker
- environmental blocker
- confidence blocker

Add fields such as:

- `blocker_type`
- `subject_ref`
- `severity`
- `confidence`
- `evidence_refs`
- `spawned_from_project_id`
- `spawned_from_objective_id`
- `suggested_detour_types`
- `resolved`
- `superseded_by_blocker_id`

This schema should be rich enough that later services can say:

- location unknown -> spawn informational objective
- too weak -> spawn capability objective
- lack materials -> spawn gather or guild-info objective
- unsafe route -> spawn scout or escort objective
- trust too low -> spawn social objective

This is the backbone of branching detours.

[Task possible affected files]

- `src/core/models/strategy.py`
- `src/actions/base.py`
- possibly `src/core/models/enums.py`

[Task important notes]
Do not collapse all blockers into “cannot proceed.” That destroys the whole detour system. The blocker type has to carry enough semantics that later phases can generate the right next objective class.

[Task check list]

- [x] Add explicit blocker taxonomy
- [x] Add evidence/provenance fields
- [x] Add detour suggestions
- [x] Add lifecycle fields for resolution/supersession
- [x] Make blockers reference projects/objectives cleanly

[Task acceptance criteria]
A project or objective can now fail for typed reasons that can be reused to derive the correct detour behavior instead of only producing a stop condition.

---

[x] (checkbox) - [Task 3] - Build a strategic knowledge ingestion service

[Task Description]
Information currently enters the simulation through many narrow channels: direct observation, gossip propagation, guild intel, blacksmith crafting context, class-hall progression checks, and quest generation. Phase 3 needs one service that normalizes these into leads, candidate zones, and blockers instead of letting each subsystem leak ad hoc tactical effects.

[Task technical implementation]
Create something like `src/core/logic/strategic_knowledge_ingestion.py` that accepts producer-specific inputs and emits `StrategicUpdate`s. It should support at least these producer kinds:

- direct observation
- guild intel
- class-hall advice
- blacksmith crafting constraints
- inn gossip
- quest briefing
- world-event discovery

For each producer, map outputs into:

- one or more `LeadRecord`s
- optional `CandidateZoneRecord`s
- optional `BlockerRecord`s
- optional objective suggestions or tags

Examples:

- guild material hints become low-to-medium certainty leads tied to biomes or enemy families, not string goals
- guild camp/resource revelation becomes either candidate zones or verified map knowledge depending on source certainty
- blacksmith missing materials becomes capability/access/resource blockers plus related material leads
- class-hall “cannot breakthrough yet” becomes a capability blocker with missing thresholds or skill prerequisites
- inn gossip becomes indirect leads or indirect belief-linked leads with degraded confidence and directness.

[Task possible affected files]

- `src/core/logic/strategic_knowledge_ingestion.py`
- `src/actions/base.py`
- `src/core/models/strategy.py`
- `src/ai/brain.py`

[Task important notes]
Do not let every building handler invent its own quasi-strategy storage. That is how you end up with intel scattered across `terrain_memory`, `goals_add`, action reasons, and side-channel assumptions.

[Task check list]

- [x] Add ingestion service
- [x] Support all main knowledge producers
- [x] Emit typed strategic updates
- [x] Normalize source quality and directness
- [x] Attach leads and blockers to relevant projects/objectives where possible

[Task acceptance criteria]
Different knowledge sources now feed one coherent strategic knowledge pipeline instead of several unrelated tactical hacks.

---

[x] (checkbox) - [Task 4] - Refactor guild intel into structured leads and candidate-zone generation

[Task Description]
The guild is already an intel producer, but right now it mostly reveals concrete terrain memory, generates quests, and appends free-form string goals like “Guild tip: iron_ore — ...”. That is too eager and too shallow for Phase 3. The design explicitly says vague leads should become a hypothesis set and ranked search space, not exact quest-arrow knowledge.

[Task technical implementation]
Refactor `VisitGuildHandler` so its outputs are no longer dominated by:

- `PerceptionUpdate(terrain_memory=...)`
- `MindUpdate(goals_add=[...])`

Instead, route guild intel through the ingestion service:

- material hints become `LeadRecord`s with semantic tags like biome, enemy family, rarity, and activity type
- camp/resource info becomes candidate zones or verified knowledge entries with producer=`guild`
- quest acceptance remains quest logic, but quest briefings can also seed structured leads/objectives
- terrain revelation should distinguish between verified map disclosure and vague “reported region” knowledge

You do not have to remove terrain memory entirely. Some guild knowledge may legitimately be precise. But the handler must stop treating every hint as either raw terrain coordinates or a prose goal string.

[Task possible affected files]

- `src/ai/states/...` where `VisitGuildHandler` lives
- `src/core/logic/strategic_knowledge_ingestion.py`
- `src/core/gameplay/buildings.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not throw away the existing guild value. It already proves the world can feed structured info into the mind. The right move is to upgrade its outputs, not replace the whole behavior.

[Task check list]

- [x] Replace free-form guild tip strings with structured leads
- [x] Distinguish exact intel from vague intel
- [x] Convert camp/resource disclosure into candidate-zone or verified knowledge records
- [x] Keep quest generation intact while enriching strategic knowledge
- [x] Preserve deterministic behavior

[Task acceptance criteria]
A guild visit can produce reusable strategic leads and candidate zones instead of only direct terrain memory and prose goal strings.

---

[x] (checkbox) - [Task 5] - Refactor class-hall and blacksmith outputs into blockers and capability leads

[Task Description]
The class hall and blacksmith already encode valuable strategic knowledge, but only procedurally. The class hall knows when a skill or breakthrough is available, and the blacksmith knows what recipes exist, which materials are missing, and how much gold is lacking. Right now those facts drive immediate building behavior, but they do not become durable strategic knowledge. That is wasted leverage.

[Task technical implementation]
Refactor these handlers so they can emit:

- capability blockers
- resource blockers
- prerequisite leads
- objective suggestions

Examples:

- class hall says “breakthrough unavailable because thresholds unmet” -> create capability blocker plus objective suggestions like train attribute, gain level, or gather class-specific evidence
- class hall says “breakthrough possible” -> create or update a verified objective lead, not just immediate REST/building behavior
- blacksmith says “need iron_ore and 80g” -> create resource blocker, economy blocker, and material leads pointing to likely sources
- learning recipes at blacksmith can create capability opportunity leads tied to equipment improvement projects

The building handlers can still preserve immediate tactical behavior, but they should now also emit structured strategic knowledge into `mind.strategic`.

[Task possible affected files]

- `src/ai/states/...` where `VisitClassHallHandler` lives
- `src/ai/states/...` where `VisitBlacksmithHandler` lives
- `src/core/logic/strategic_knowledge_ingestion.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not keep missing requirements trapped in action `reason` strings. That is debugging text, not game state. If it matters strategically, it needs a record.

[Task check list]

- [x] Convert blacksmith missing-material outputs into blockers/leads
- [x] Convert class-hall unmet prerequisites into capability blockers
- [x] Emit opportunity leads for craft and breakthrough paths
- [x] Preserve current tactical building interactions
- [x] Attach outputs to relevant projects when possible

[Task acceptance criteria]
After visiting the blacksmith or class hall, the entity retains structured strategic knowledge about what is missing, what is possible, and what detours would unlock progress.

---

[x] (checkbox) - [Task 6] - Upgrade gossip propagation from entity-belief copying to strategic rumor propagation

[Task Description]
The current gossip system is useful but still too narrow. `KnowledgePropagationService` propagates salient `BeliefRecord`s with degraded directness and confidence, and inn-level social logic can directly copy memory records between heroes. That is a strong base for uncertainty, but Phase 3 needs rumor propagation for leads and partial strategic knowledge, not only entity sightings.

[Task technical implementation]
Extend knowledge propagation to support:

- lead sharing
- candidate-zone sharing
- blocker-relevant advice
- contradiction propagation
- source-chain tracking

Add methods such as:

- `share_lead(...)`
- `merge_indirect_lead(...)`
- `propagate_rumor(...)`

Lead propagation should:

- degrade certainty and directness
- retain source chain
- weight trustworthiness and relationship strength
- mark indirect provenance
- optionally cap how far specific rumors travel unless highly salient

This should integrate with the existing propagation system rather than replacing it. Entity belief sharing still matters; it just should not be the only form of socially transmitted knowledge.

[Task possible affected files]

- `src/core/logic/knowledge_propagation.py`
- `src/systems/social/knowledge_propagation_system.py`
- inn/social interaction systems
- `src/core/models/strategy.py`

[Task important notes]
Do not let rumors become perfect truth in transit. The current system already degrades confidence and directness for indirect beliefs. Lead propagation must preserve that logic or the whole uncertainty design collapses.

Also, avoid direct live mutation shortcuts in social systems. Keep the authoritative-update discipline where feasible.

[Task check list]

- [x] Clone `LeadRecord` during social sharing
- [x] Apply confidence degradation (multiplier 0.9)
- [x] Apply directness degradation (multiplier 0.8)
- [x] Track source entity and source type (gossip)
- [x] Factor in recipient trust in sharer for source confidence
- [x] Add deterministic repeatability tests

[Task acceptance criteria]
Entities can acquire uncertain strategic leads from other entities, and those leads retain indirect provenance and degraded reliability instead of turning into exact truth.

---

[x] (checkbox) - [Task 7] - Add blocker inference and detour spawning logic

[Task Description]
Once uncertain knowledge exists, the engine needs a consistent way to decide when a project is blocked and which detour family should be spawned. The design explicitly lists blocker types and detour families and frames “blocked ambition” as one of the core story grammar patterns. This is where Phase 3 stops being data modeling and starts becoming a real branching machine.

[Task technical implementation]
Create:

- `BlockerInferenceService`
- `DetourSuggestionService`

`BlockerInferenceService` should inspect current project/objective state against strategic knowledge and world constraints, then infer blockers such as:

- location unknown
- confidence too low
- materials missing
- gold insufficient
- route unsafe
- strength estimate too low
- social support missing
- obligation conflict active

`DetourSuggestionService` should convert each blocker into candidate objective classes:

- knowledge blocker -> ask expert, gather rumor, scout region, verify clue
- capability blocker -> train, level, learn skill, craft upgrade
- resource blocker -> gather funds, gather materials, seek guild tip
- social blocker -> recruit ally, restore trust, negotiate terms
- access blocker -> unlock route, obtain escort, find safer path

Outputs should become `StrategicUpdate`s that Phase 2 can choose among.

[Task possible affected files]

- `src/ai/strategy/blocker_inference.py`
- `src/ai/strategy/detour_suggestion.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not fold this into one giant evaluator method. Blocker inference and detour suggestion are reusable strategic mechanics, not one-off decision code.

[Task check list]

- [x] Implement `BlockerInferenceService` to detect stalled objectives
- [x] Implement `DetourSuggestionService` to map blockers to remedial objectives
- [x] Integrate services into `ObjectiveDerivationService`
- [x] Auto-spawn `INVESTIGATE` detours for `KNOWLEDGE` blockers
- [x] Auto-spawn `TRAIN` or `COLLECT` detours for `CAPABILITY`/`MATERIAL` blockers
- [x] Adhere to AOA authoritative update constraints

[Task acceptance criteria]
When a project cannot proceed, the engine can infer why and generate appropriate detour objectives instead of stalling or silently switching to unrelated behavior.

---

[x] (checkbox) - [Task 8] - Add hypothesis narrowing, contradiction tracking, and search history

[Task Description]
The design explicitly says a good lead system needs contradiction status, search history, derived candidate zones, and already-tested interpretations. Without this, investigation degenerates into repeated wandering or instant resolution. Phase 3 needs memory for “what have I already checked” and “which clue variants have failed.”

[Task technical implementation]
Add an investigation service that can:

- derive candidate zones from lead semantics
- mark a zone as searched
- record search outcome
- raise or lower confidence in remaining candidates
- mark contradictions when evidence invalidates a lead
- supersede or split hypotheses when stronger evidence arrives

Examples:

- “flower grows where snow never melts” -> candidate zones tagged high-altitude mountain / shrine / frozen biome
- searched zone has no relevant evidence -> reduce confidence or mark tested interpretation
- direct observation of guardian too strong -> capability blocker attached to current project
- second guild rumor contradicts earlier clue -> contradiction count increments and candidate ranking changes

This should integrate with objective derivation so “scout region” and “verify clue” can update the hypothesis state, not just move the entity around.

[Task possible affected files]

- `src/core/logic/investigation_service.py`
- `src/core/models/strategy.py`
- `src/ai/strategy/objective_derivation.py`
- exploration/scouting handlers

[Task important notes]
Do not let every failed search immediately invalidate the whole lead. Sometimes it should only demote one hypothesis or one candidate zone.

Also, do not store search history only as narrative prose. It needs machine-usable structure.

[Task check list]

- [x] Add candidate-zone derivation rules
- [x] Add search history recording
- [x] Add contradiction tracking
- [x] Add hypothesis reranking after evidence
- [x] Feed search outcomes back into strategic state
- [x] Integrate with scouting/verification objectives

[Task acceptance criteria]
Investigation becomes cumulative: searched locations, failed interpretations, contradictions, and newly confirmed evidence all reshape the remaining search space instead of being forgotten each tick.

---

[x] (checkbox) - [Task 9] - Prevent certainty collapse in tactical translation and path targeting

[Task Description]
This task protects the phase from self-sabotage. Even with good leads and blockers, the system can still fake investigation if tactical translation turns “possible mountain zone” into one exact move target the moment an objective is created. The design explicitly rejects that.

[Task technical implementation]
Update the objective-to-goal translation layer from Phase 2 so informational objectives can target:

- candidate zones
- search patterns
- likely witnesses or experts
- verification opportunities
- region classes rather than exact coordinates

Examples:

- `gather_rumor` biases inn, guild, or social contact targets
- `scout_candidate_zone` chooses a region anchor and search sweep behavior, not one magical exact tile
- `verify_clue` prefers sites, witnesses, or evidence-bearing entities
- `find_material_source` prefers biome or enemy-family searching before exact harvest target commitment

Exact path targets should only be emitted once evidence justifies them. Until then, tactics should operate on ranked approximations.

[Task possible affected files]

- `src/ai/strategy/objective_to_goal_mapper.py`
- movement/exploration state handlers
- `src/core/models/strategy.py`

[Task important notes]
Do not confuse “needs to act” with “must know precisely.” Tactical layers can work with approximations, anchors, and region search patterns.

[Task check list]

- [x] Add region/candidate-zone aware tactical translation
- [x] Support investigation-oriented movement/search behaviors
- [x] Delay exact coordinate commitment until evidence supports it
- [x] Preserve fallback tactical behavior under uncertainty
- [x] Keep translation deterministic

[Task acceptance criteria]
Investigation objectives produce approximate, evidence-sensitive tactical behavior instead of instantly collapsing into precise quest markers.

---

[x] (checkbox) - [Task 10] - Add observability and tests for uncertainty integrity

[Task Description]
Phase 3 is where it becomes very easy to lie to yourself. You can tell a story about rumors and investigation while the code is actually just producing target coordinates with extra steps. You need both inspection and tests that prove uncertainty is preserved, leads are tracked, blockers spawn detours, and evidence changes the search space over time. The design’s coherence depends on this.

[Task technical implementation]
Extend inspection/debug views to show:

- active leads
- candidate zones with confidence
- contradictions
- tested interpretations
- active blockers and their detour suggestions
- provenance for key rumors or clues

Add tests covering:

- guild hint produces lead, not only string goal
- blacksmith unmet recipe produces blocker records
- inn rumor propagation degrades certainty/directness
- search history updates candidate confidence after scouting
- contradiction updates do not erase all prior context
- tactical translation under uncertainty does not emit exact coordinates too early
- repeated evidence narrows candidates deterministically

Use targeted unit tests and a few bounded integration tests around building handlers and propagation systems.

[Task possible affected files]

- `src/ui/cli/inspector.py`
- API debug/inspection modules
- `tests/ai/test_leads_and_blockers.py`
- `tests/ai/test_investigation_service.py`
- `tests/social/test_rumor_propagation.py`
- `tests/ai/test_uncertain_tactical_translation.py`

[Task important notes]
Do not accept “it seems to work in the sim” as proof. This phase needs explicit anti-cheating tests.

[Task check list]

- [x] Add lead/blocker/candidate-zone debug views
- [x] Add rumor degradation tests
- [x] Add blocker-to-detour tests
- [x] Add search-history and contradiction tests
- [x] Add anti-certainty-collapse tactical tests
- [x] Add deterministic repeatability tests

[Task acceptance criteria]
You can prove, not merely assume, that uncertain knowledge remains uncertain until verified, blockers generate detours, and investigation history actually changes future behavior.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking “we already have beliefs, so Phase 3 is basically done.” That is false. You have entity-facing subjective perception and some gossip, but not a real uncertainty system for places, materials, candidate regions, contradictory clues, or blocker-driven detours.

What actions must be taken immediately
Do Tasks 1 through 5 first. That gives you the real substrate: knowledge models, blocker semantics, ingestion, and the refactoring of guild/class-hall/blacksmith outputs into strategic knowledge. Then do Tasks 6 through 9 so rumors, investigation, and tactical translation stop collapsing into certainty. Finish with Task 10 before calling the phase complete.

What must stop or be eliminated
Stop storing strategic knowledge in prose goal strings, action reasons, raw terrain reveals, and one-off handler logic. Stop allowing rumors to become exact truth on receipt. Stop treating blocked projects as dead ends instead of detour generators.

The consequences and opportunity cost if this fails
You will build a “story investigation” feature that only cosmetically differs from a quest-marker system. The player may see more words, but the entities will still know too much, forget too much, and branch too little. That wastes the strongest ingredients already present in the engine.

Phase 3 Implementation Complete. All tasks verified and all checklists satisfied. The strategic cognition engine now effectively manages uncertainty, blockers, and detours. Proceed to Phase 4.
