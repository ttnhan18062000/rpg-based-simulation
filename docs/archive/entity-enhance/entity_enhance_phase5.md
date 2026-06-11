---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Phase 5 — Information / Belief / Source-Trust Loop

Phase 1:

```text
world exposes options
```

Phase 2:

```text
entity understands itself
```

Phase 3:

```text
entity chooses adventure route family
```

Phase 4:

```text
entity judges combat risk and learns from combat
```

Phase 5:

```text
entity handles uncertain information:
ask, hear, observe, believe, doubt, verify, contradict, trust, distrust, and use information in future decisions
```

The current source already has a belief framework: `BeliefCycleSystem`, `BeliefEntry`, rumors, observations, certainty decay, `LeadCertainty`, source IDs, and strategic lead updates. The issue is that the cognition doc itself identifies the gap: belief logic exists, but current town/intel flow is still shallow, mostly guild-like information emission rather than complex information sharing, contradiction, or deception.

Current tests already cover basic guild intel emission, where a guild visit creates a strategic lead and concern from a high-trauma region. So Phase 5 should **not** duplicate that simple guild-intel test.

---

# Phase 5 goal

Phase 5 answers:

```text
How does an entity acquire uncertain world knowledge,
decide whether to trust it,
act on it,
verify it,
and update future trust/behavior when it is confirmed or contradicted?
```

Not:

```text
Can GuildIntelSystem emit one lead?
```

That already exists.

Not:

```text
Can BeliefCycleSystem create a vague rumor lead?
```

That already mostly exists.

Phase 5 is about **using information in the life loop**.

---

# Phase 5 success definition

Phase 5 is successful when the engine can produce a trace like:

```yaml
information_decision:
  entity_id: 1
  need: unknown_material_source
  query:
    kind: material_source
    subject: moon_resin
  considered_sources:
    - guide_hometown
    - guild_hometown
    - traveler_7
  selected_source: guide_hometown
  reason: "nearby, affordable, medium trust"

information_response:
  source_id: guide_hometown
  answer_kind: partial
  certainty: 0.55
  learned:
    - north_ruin_may_contain_clue
  still_unknown:
    - exact_moon_resin_source

belief_update:
  created_lead: lead_moon_resin_north_ruin
  certainty: VAGUE
  source_trust_pending: guide_hometown

future_effect:
  route_family: scout_location
  target: north_ruin
```

After contradiction:

```yaml
belief_contradiction:
  entity_id: 1
  source_id: guide_hometown
  subject: moon_resin
  old_claim: "north_ruin may contain clue"
  observed_result: "no clue found after search"
  effect:
    lead_certainty: EXHAUSTED
    source_trust_delta: -0.15
    new_route: ask_guild_or_traveler
```

---

# Task 1 — Define information-domain boundary

## Description

Do not put information logic directly into adventure, guild, blacksmith, or entity model.

Create a domain boundary:

```text
src/domains/information/
```

This layer should coordinate:

```text
information need
-> source selection
-> query
-> response
-> belief update
-> source trust update
-> future route impact
```

## Proposed service

```python
class InformationDecisionService:
    def evaluate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: InformationDecisionContext,
    ) -> InformationDecisionResult:
        ...
```

## Inputs

```text
KnowledgeModelComponent
NeedInterpretationComponent
Strategic blockers
Known information sources
Current location
Gold/cost
Source trust
Known leads
Personality traits
```

## Outputs

```text
selected source
query
expected cost
expected certainty
reason trace
proposed ActionIntent or StrategicUpdate
```

## Checklist

 - [x] Information logic is isolated under information domain.
 - [x] Service does not mutate state directly.
 - [x] Service does not reveal hidden world truth.
 - [x] Service consumes Phase 2 knowledge/unknowns.
 - [x] Service consumes Phase 1 `InformationProvider`.
 - [x] Service can output `ASK_INFORMATION` intent.
 - [x] Same input + same seed gives deterministic result.
 - [x] Existing guild-intel tests remain unchanged.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_boundary.py
```

Test cases:

```text
test_information_service_does_not_mutate_state
test_information_service_does_not_require_adventure_component
test_information_service_uses_known_unknowns_as_input
test_information_service_returns_query_and_trace
```

---

# Task 2 — Define information source model

## Description

Information sources must be structured, small, scoped, and not omniscient.

A guide should not contain all world facts.

A guild should not reveal all hidden dangers.

A blacksmith should know recipes/material requirements, but not necessarily exact rare-material locations.

## Proposed model

```python
@dataclass(frozen=True)
class InformationSourceProfile:
    source_id: str | int
    source_kind: str
    knowledge_scopes: tuple[str, ...]
    accuracy: float
    freshness: float
    bias: float = 0.0
    cost_gold: int = 0
    max_answers_per_query: int = 3
```

Example source kinds:

```text
guide
guild
blacksmith
shopkeeper
traveler
ally
rumor_board
map
ruin_clue
corpse_clue
enemy_observation
```

## Knowledge scopes

```text
common_resource_sources
rare_resource_hints
recipe_requirements
regional_danger
monster_habitat
quest_hints
service_locations
route_safety
ancient_lore
```

## Checklist

 - [x] Each source has explicit scope.
 - [x] Source cannot answer outside scope except unknown/rumor.
 - [x] Source answer count is capped.
 - [x] Source has accuracy/freshness/cost.
 - [x] Source can return partial answer.
 - [x] Source can return “unknown.”
 - [x] Source can return rumor-level answer.
 - [x] Source does not directly modify entity memory.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_source_profile.py
```

Test cases:

```text
test_blacksmith_knows_recipe_requirements_not_hidden_material_location
test_guide_knows_common_resource_source
test_guide_returns_partial_for_rare_material
test_source_outside_scope_returns_unknown
test_source_answer_count_is_capped
```

---

# Task 3 — Implement `InformationQueryRouter`

## Description

Given an information need, choose candidate sources.

Example:

```text
unknown material source: moon_resin
```

Possible sources:

```text
guide
guild
blacksmith
traveler
ruin clue
map
```

But the router should not query all sources globally.

It should choose scoped candidate sources based on:

```text
current town
known sources
nearby sources
source scope
cost
trust
urgency
```

## Proposed service

```python
class InformationQueryRouter:
    def route(
        self,
        entity: EntityState,
        query: InformationQuery,
        state: AuthoritativeState,
        budget: QueryBudget,
    ) -> tuple[InformationSourceCandidate, ...]:
        ...
```

## Candidate shape

```python
@dataclass(frozen=True)
class InformationSourceCandidate:
    source_id: str | int
    source_kind: str
    expected_relevance: float
    expected_certainty: float
    cost_gold: int
    distance_cost: float
    trust_score: float
    reason: str
```

## Checklist

 - [x] Router uses source scopes.
 - [x] Router uses current location/known town.
 - [x] Router uses source trust if available.
 - [x] Router filters unaffordable sources unless desperation rule applies.
 - [x] Router caps candidate count.
 - [x] Router does not scan all world objects.
 - [x] Router returns empty result with reason if no source exists.
 - [x] Router is deterministic.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_query_router.py
```

Test cases:

```text
test_material_source_query_routes_to_guide_and_guild
test_recipe_query_routes_to_blacksmith
test_regional_danger_query_routes_to_guild_or_guide
test_router_excludes_unaffordable_source_when_noncritical
test_router_caps_candidate_count
test_router_does_not_include_out_of_scope_source
```

---

# Task 4 — Implement `InformationResponseNormalizer`

## Description

Different sources may produce different response formats.

Normalize them into a common result:

```text
fact
lead
unknown
rumor
contradiction
```

## Proposed response model

```python
@dataclass(frozen=True)
class NormalizedInformationResponse:
    query: InformationQuery
    source_id: str | int
    answer_kind: str
    facts: tuple[KnowledgeFact, ...] = ()
    leads: tuple[LeadState, ...] = ()
    unknowns: tuple[UnknownFact, ...] = ()
    certainty: float = 0.0
    contradiction_targets: tuple[str, ...] = ()
    cost_paid_gold: int = 0
    reason: str | None = None
```

## Answer kinds

```text
KNOWN_FACT
PARTIAL_LEAD
RUMOR
UNKNOWN
CONTRADICTION
STALE
DECEPTIVE
```

Phase 5 can support `DECEPTIVE` as data shape but does not need complex malicious behavior yet.

## Checklist

 - [x] Provider response is normalized.
 - [x] Known fact becomes `KnowledgeFact`.
 - [x] Partial hint becomes `LeadState`.
 - [x] Unknown answer becomes `UnknownFact`.
 - [x] Rumor has lower certainty than observation.
 - [x] Contradiction references existing belief/lead/fact.
 - [x] Certainty is preserved.
 - [x] Source ID is preserved.
 - [x] Gold cost is recorded, but payment still uses existing law/transaction path.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_response_normalizer.py
```

Test cases:

```text
test_known_answer_normalizes_to_knowledge_fact
test_partial_answer_normalizes_to_lead
test_unknown_answer_normalizes_to_unknown_fact
test_rumor_answer_has_low_certainty
test_contradiction_response_references_existing_fact
```

---

# Task 5 — Connect information response to knowledge model

## Description

Phase 2 introduced `KnowledgeModelComponent`.

Phase 5 must now update it from real information responses.

But do not store everything.

Store only relevant, capacity-bounded, useful information.

## Update rules

```text
known fact -> KnowledgeFact
partial clue -> LeadState + optional uncertain KnowledgeFact
unknown -> UnknownFact
rumor -> low-certainty lead/fact
contradiction -> downgrade existing fact/lead
```

## Proposed service

```python
class InformationAssimilationService:
    def assimilate(
        self,
        entity: EntityState,
        response: NormalizedInformationResponse,
        current_tick: int,
    ) -> InformationAssimilationResult:
        ...
```

## Result

```python
@dataclass(frozen=True)
class InformationAssimilationResult:
    knowledge_update: KnowledgeModelComponent | None
    strategic_update: StrategicUpdate | None
    source_trust_update: SourceTrustEntry | None
    trace: Mapping[str, object]
```

## Checklist

 - [x] Relevant facts are stored.
 - [x] Irrelevant facts can be ignored.
 - [x] Unknowns are stored if tied to active need/blocker/project.
 - [x] Leads are added to strategic state where useful.
 - [x] Low-certainty rumor does not become confirmed fact.
 - [x] Contradiction downgrades or marks stale existing knowledge.
 - [x] Capacity limits apply.
 - [x] Assimilation is deterministic.
 - [x] Assimilation does not directly choose next action.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_assimilation.py
```

Test cases:

```text
test_known_material_source_updates_knowledge_fact
test_partial_material_hint_adds_lead_not_confirmed_fact
test_unknown_answer_records_unknown_when_relevant
test_low_certainty_rumor_does_not_override_precise_observation
test_contradiction_downgrades_existing_fact
test_irrelevant_answer_is_not_stored_when_memory_budget_full
```

---

# Task 6 — Implement contradiction detection

## Description

Contradiction is where belief becomes meaningful.

Example:

```text
Guide says moon_resin is in north_ruin.
Entity searches north_ruin and finds no clue.
```

That should not instantly mean guide lied. It means:

```text
claim confidence decreases
source trust may decrease slightly
entity may search alternative source
```

## Proposed service

```python
class BeliefContradictionService:
    def detect(
        self,
        entity: EntityState,
        observation: ObservationEvent,
        state: AuthoritativeState,
    ) -> BeliefContradictionResult:
        ...
```

## Contradiction types

```text
not_found_after_search
observed_different_location
source_answer_conflicts_with_observation
two_sources_disagree
expected_enemy_absent
expected_resource_depleted
claimed_safe_region_observed_dangerous
```

## Checklist

 - [x] Direct observation can contradict rumor.
 - [x] Direct observation should usually outweigh rumor.
 - [x] Failed search weakens but does not always fully refute.
 - [x] Multiple source disagreement creates uncertainty, not instant truth.
 - [x] Contradiction updates certainty/unknowns.
 - [x] Source trust update is proportional, not binary.
 - [x] Contradiction creates trace event.
 - [x] Service does not mutate state directly.

## TDD tests

```text
tests/unit/domains/information/test_phase5_belief_contradiction.py
```

Test cases:

```text
test_observation_contradicts_vague_rumor
test_failed_search_weakens_but_does_not_delete_claim
test_precise_observation_overrides_low_certainty_rumor
test_two_sources_disagree_creates_uncertainty
test_contradiction_updates_source_trust_slightly
```

---

# Task 7 — Implement source trust update

## Description

Source trust should change slowly.

A source should not become “trusted forever” after one correct answer or “useless forever” after one failed clue.

## Proposed service

```python
class SourceTrustUpdateService:
    def update(
        self,
        entity: EntityState,
        source_id: str | int,
        outcome: InformationOutcome,
        current_tick: int,
    ) -> SourceTrustEntry:
        ...
```

## Outcomes

```text
confirmed
partially_confirmed
contradicted
not_verifiable
deceptive_detected
stale
```

## Rules

```text
confirmed -> small trust increase
partially_confirmed -> tiny trust increase
contradicted -> trust decrease
not_verifiable -> no or tiny change
deceptive_detected -> stronger trust decrease
old trust slowly decays toward neutral
```

## Checklist

 - [x] Trust update is bounded.
 - [x] Trust stays within [0.0, 1.0].
 - [x] One event does not cause extreme swing.
 - [x] Repeated confirmation increases trust gradually.
 - [x] Repeated contradiction decreases trust gradually.
 - [x] Trust affects future source selection.
 - [x] Trust update is deterministic.
 - [x] Existing social contract trust tests are not duplicated.

Current uploaded tests already include social contract appraisal/trust behavior, so Phase 5 should test **information-source trust**, not recruitment contract appraisal.

## TDD tests

```text
tests/unit/domains/information/test_phase5_source_trust_update.py
```

Test cases:

```text
test_confirmed_answer_increases_source_trust_slightly
test_contradicted_answer_decreases_source_trust_slightly
test_repeated_contradictions_lower_future_source_score
test_trust_is_clamped_between_zero_and_one
test_not_verifiable_outcome_does_not_overreact
```

---

# Task 8 — Implement observation-to-belief bridge

## Description

Information does not only come from NPCs.

Entities should learn from direct observation:

```text
I saw iron ore in old_mine.
I saw wolf pack in forest.
I saw north_ruin is dangerous.
I saw blacksmith has no stock.
I saw guide clue failed.
```

## Proposed service

```python
class ObservationBeliefBridge:
    def process_observation(
        self,
        entity: EntityState,
        event: ObservationEvent,
        state: AuthoritativeState,
    ) -> InformationAssimilationResult:
        ...
```

## Observation types

```text
resource_seen
resource_depleted
enemy_seen
enemy_defeated
region_danger_seen
service_available
service_unavailable
quest_target_seen
claim_failed_search
```

## Checklist

 - [x] Direct resource observation creates high-certainty knowledge.
 - [x] Direct danger observation creates risk knowledge/concern.
 - [x] Direct service observation creates service-location fact.
 - [x] Failed search can trigger contradiction check.
 - [x] Observation can verify prior rumor.
 - [x] Observation can contradict prior rumor.
 - [x] Observation update is event-driven, not every tick.
 - [x] Observation does not reveal non-observed hidden truth.

## TDD tests

```text
tests/unit/domains/information/test_phase5_observation_belief_bridge.py
```

Test cases:

```text
test_seen_resource_creates_precise_knowledge
test_seen_enemy_creates_danger_lead_or_risk_fact
test_seen_service_creates_service_location_fact
test_failed_search_triggers_contradiction_check
test_direct_observation_overrides_vague_rumor
```

---

# Task 9 — Connect belief/knowledge to route decisions

## Description

Information is useless unless it changes behavior.

Phase 5 must connect updated knowledge to Phase 3 route choice.

Example:

```text
Before:
moon_resin source unknown
-> ask_information

After guide partial answer:
north_ruin may contain clue
-> scout_location

After contradiction:
north_ruin clue exhausted
-> ask_guild / ask_traveler / choose alternative recipe
```

## Proposed bridge

```python
class BeliefRouteImpactService:
    def evaluate_impact(
        self,
        entity_before: EntityState,
        entity_after: EntityState,
        assimilation_result: InformationAssimilationResult,
    ) -> RouteImpactHint:
        ...
```

## Output

```python
@dataclass(frozen=True)
class RouteImpactHint:
    invalidated_route_families: tuple[str, ...] = ()
    boosted_route_families: tuple[str, ...] = ()
    new_blockers: tuple[BlockerState, ...] = ()
    resolved_blockers: tuple[str, ...] = ()
    reason: str | None = None
```

## Checklist

 - [x] New material source boosts gather/scout route.
 - [x] New service location boosts service route.
 - [x] Unknown answer keeps information route active.
 - [x] Contradicted lead invalidates or weakens route.
 - [x] Precise observation can resolve unknown-source blocker.
 - [x] Impact hints feed Phase 3 route generator/scorer.
 - [x] Existing strategic detour tests are not duplicated.

The current strategic detour code already scores blocker/lead matches using certainty and source trust, so Phase 5 should reuse this idea rather than creating a parallel detour engine.

## TDD tests

```text
tests/unit/domains/information/test_phase5_belief_route_impact.py
```

Test cases:

```text
test_known_material_source_boosts_gather_route
test_partial_lead_boosts_scout_route_not_direct_gather
test_unknown_answer_keeps_information_need_active
test_contradicted_lead_weakens_scout_route
test_verified_fact_resolves_unknown_source_blocker
```

---

# Task 10 — Add information action intent bridge

## Description

Information decisions must become executable intents through existing action infrastructure.

Initial intent kinds:

```text
ASK_INFORMATION
READ_MAP
INSPECT_CLUE
OBSERVE_RESOURCE
OBSERVE_REGION
VERIFY_CLAIM
```

Phase 5 only needs `ASK_INFORMATION` and `INSPECT_CLUE` if Phase 1 has clue objects.

## Proposed resolver

```python
class InformationIntentResolver:
    def resolve(
        self,
        entity: EntityState,
        decision: InformationDecisionResult,
        state: AuthoritativeState,
    ) -> ActionIntent | None:
        ...
```

## Checklist

 - [x] If source is far, resolve to `MOVE_TO`.
 - [x] If source is near, resolve to `ASK_INFORMATION`.
 - [x] If information costs gold, requirement check happens first.
 - [x] If unaffordable, produce blocker, not free information.
 - [x] Intent execution does not bypass law layer.
 - [x] Information response becomes event/assimilation input.
 - [x] Trace connects need -> source -> query -> response.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_intent_resolver.py
```

Test cases:

```text
test_far_guide_resolves_to_move_to_guide
test_near_guide_resolves_to_ask_information
test_paid_information_requires_gold
test_unaffordable_information_creates_gold_blocker
test_information_intent_preserves_query_subject
```

---

# Task 11 — Add information/belief integration phase

## Description

Add a bounded phase that processes information requests and belief updates.

Do not run global belief processing every tick for every entity.

## Trigger conditions

```text
active unknown tied to current project
information need is dominant or high urgency
information response event received
direct observation event received
claim verification completed
lead becomes stale
contradiction event detected
```

## Skip conditions

```text
entity dead/inactive
no active unknowns
belief budget exhausted
no relevant source known
cooldown active
feature flag disabled
```

## Proposed phase

```text
InformationBeliefPhase:
  1. process pending information responses
  2. process direct observations
  3. detect contradictions
  4. update knowledge/source trust
  5. produce route impact hints
  6. emit trace events
```

## Checklist

 - [x] Phase is feature-flagged initially.
 - [x] Phase is event-driven where possible.
 - [x] Phase respects cognition capacity.
 - [x] Phase does not scan all facts/entities every tick.
 - [x] Phase emits `StrategicUpdate` or self-model update only through standard path.
 - [x] Phase output can trigger Phase 3 route reevaluation.
 - [x] Deterministic under same seed/input.
 - [x] Existing cognition-history API tests are not duplicated.

The uploaded tests already validate cognition snapshot/diff/history style endpoints and event search API shapes, so Phase 5 should only test event payload/phase behavior, not another API suite.

## TDD tests

```text
tests/integration/domains/information/test_phase5_information_belief_phase.py
```

Test cases:

```text
test_phase_skips_entity_without_active_unknown
test_phase_runs_when_information_response_received
test_phase_runs_when_observation_contradicts_claim
test_phase_respects_feature_flag
test_phase_respects_belief_budget
test_phase_outputs_route_impact_hint
test_phase_does_not_full_scan_world
```

---

# Task 12 — Add Phase 5 scenario tests

These are the important ones. They should prove **information changes life direction**.

## Scenario 5.1 — Common material source learned from guide

```text
Entity needs iron_ore.
Entity does not know source.
Guide knows old_mine.
```

Expected:

```text
entity asks guide
knowledge fact created: iron_ore source = old_mine
unknown source blocker resolved
future route shifts to gather_resource / reach_location
```

Forbidden:

```text
entity knows old_mine before asking
guide reveals unrelated hidden rare materials
```

---

## Scenario 5.2 — Rare material partial lead

```text
Entity needs moon_resin.
Guide does not know exact source.
Guide suggests north_ruin may contain clue.
```

Expected:

```text
entity records partial lead
moon_resin exact source remains unknown
route shifts to scout_location / investigate
```

Forbidden:

```text
entity directly knows moon_cave
partial lead treated as precise fact
```

---

## Scenario 5.3 — Contradicted rumor changes route

```text
Traveler says moon_resin is in north_ruin.
Entity searches north_ruin and finds no clue.
```

Expected:

```text
lead certainty decreases
traveler trust decreases slightly
route shifts to ask_guild / ask_other_source / alternate_recipe
```

Forbidden:

```text
lead remains equally trusted forever
traveler trust drops to zero from one failure
entity repeats same exhausted search forever
```

---

## Scenario 5.4 — Direct observation overrides rumor

```text
Rumor says wolf_den is safe.
Entity directly observes wolf pack in wolf_den.
```

Expected:

```text
safe rumor downgraded
danger knowledge created
future route avoids wolf_den or requires preparation
```

---

## Scenario 5.5 — Two sources disagree

```text
Guide says north road is dangerous.
Traveler says north road is safe.
Entity has no direct observation.
```

Expected:

```text
entity stores conflict
certainty stays moderate/low
entity may scout, ask guild, or choose alternate route
does not treat either claim as absolute truth
```

---

## Scenario 5.6 — Source trust affects future query choice

```text
Guide has been correct twice.
Traveler has been wrong twice.
Entity has new unknown.
Both sources can answer.
```

Expected:

```text
entity prefers guide if cost/distance comparable
trace includes source trust modifier
```

## Test file

```text
tests/integration/scenarios/test_phase5_information_belief_scenarios.py
```

## Checklist

 - [x] Scenarios assert knowledge/belief state.
 - [x] Scenarios assert future route impact.
 - [x] Scenarios assert no hidden truth leak.
 - [x] Scenarios assert source trust changes gradually.
 - [x] Scenarios assert contradiction changes future choice.
 - [x] Scenarios avoid duplicating basic guild intel emission.
 - [x] Scenarios are deterministic.
 - [x] Each scenario has at least one forbidden behavior assertion.

---

# Task 13 — Add Phase 5 trace events

## Description

Information/belief behavior must be inspectable.

Add events, but do not create another API test suite.

## Event types

```text
InformationNeedDetected
InformationSourceConsidered
InformationSourceSelected
InformationQueryAsked
InformationResponseReceived
KnowledgeFactLearned
UnknownFactRecorded
RumorRecorded
BeliefContradicted
SourceTrustUpdated
BeliefRouteImpactGenerated
```

## Example

```yaml
event_type: BeliefContradicted
entity_id: 1
subject: moon_resin
old_claim: north_ruin_hint
observation: search_failed
old_certainty: VAGUE
new_certainty: EXHAUSTED
source_id: traveler_7
trust_delta: -0.08
```

## Checklist

 - [x] Events emitted only on meaningful changes.
 - [x] Events include source ID.
 - [x] Events include certainty before/after.
 - [x] Events include route impact if any.
 - [x] Events are deterministic.
 - [x] Event volume is bounded.
 - [x] Events do not mutate authoritative state.
 - [x] Existing observability parity tests still pass.

## TDD tests

```text
tests/unit/domains/information/test_phase5_information_events.py
```

Test cases:

```text
test_query_event_contains_source_and_subject
test_response_event_contains_certainty
test_contradiction_event_contains_before_after_certainty
test_source_trust_event_contains_delta
test_event_generation_does_not_change_state_hash
```

---

# Task 14 — Add Phase 5 performance gates

## Description

Information/belief systems can become expensive if every entity tracks too many facts or queries too many sources.

## Required metrics

```text
information_queries_total
information_sources_considered_total
information_responses_total
knowledge_facts_added_total
unknowns_recorded_total
belief_contradictions_total
source_trust_updates_total
avg_information_phase_ms
p95_information_phase_ms
max_knowledge_entries_per_entity
skipped_due_to_budget
```

## Performance tests

```text
10 entities, 500 ticks
100 entities, 500 ticks
500 entities, 200 ticks
100 entities with conflicting rumors
```

## Checklist

 - [x] Source candidates capped.
 - [x] Knowledge entries capped.
 - [x] Contradiction checks scoped to relevant subject.
 - [x] No global all-claim comparison.
 - [x] No all-entity rumor propagation.
 - [x] Feature flag OFF matches old behavior.
 - [x] Feature flag ON stays within agreed overhead.
 - [x] Determinism hash stable.
 - [x] Performance report written.

## Test file

```text
tests/perf/test_phase5_information_belief_budget.py
```

---

# Phase 5 test files to add

```text
tests/unit/domains/information/test_phase5_information_boundary.py
tests/unit/domains/information/test_phase5_information_source_profile.py
tests/unit/domains/information/test_phase5_information_query_router.py
tests/unit/domains/information/test_phase5_information_response_normalizer.py
tests/unit/domains/information/test_phase5_information_assimilation.py
tests/unit/domains/information/test_phase5_belief_contradiction.py
tests/unit/domains/information/test_phase5_source_trust_update.py
tests/unit/domains/information/test_phase5_observation_belief_bridge.py
tests/unit/domains/information/test_phase5_belief_route_impact.py
tests/unit/domains/information/test_phase5_information_intent_resolver.py
tests/unit/domains/information/test_phase5_information_events.py

tests/integration/domains/information/test_phase5_information_belief_phase.py
tests/integration/scenarios/test_phase5_information_belief_scenarios.py
tests/perf/test_phase5_information_belief_budget.py
```

---

# Phase 5 non-goals

Do **not** implement these yet:

```text
full deception economy
complex multi-agent rumor spread
NPC gossip network
global knowledge graph
long-term biography memory
full social negotiation
political/faction propaganda
market intelligence system
large-scale news propagation
```

Also do not duplicate existing tests for:

```text
basic GuildIntelSystem lead emission
basic social contract appraisal
cognition history API
event search API
observability websocket/health/status
strategic detour scoring
```

Those are already present in the current test export or existing source/test surface.

---

# Phase 5 completion criteria

Phase 5 is done when this is true:

```text
An entity does not know hidden truth automatically.

It can ask an appropriate source,
receive known / partial / rumor / unknown information,
store only relevant knowledge,
act on uncertain leads,
verify or contradict claims through observation,
adjust source trust,
and change future route decisions.
```

Minimum proof:

```text
common material source can be learned
rare material creates partial lead, not exact truth
false or failed rumor weakens certainty
direct observation overrides weak rumor
two sources disagree without instant truth resolution
trusted sources are preferred later
belief/information overhead is bounded
```

---

# Priority Plan

## What changes in Phase 5

Phase 4 made combat judgment subjective.

Phase 5 makes **world knowledge subjective**.

The entity no longer behaves like:

```text
world truth -> entity action
```

It behaves like:

```text
world truth
-> source/observation filters
-> entity belief
-> uncertain route decision
-> verification
-> belief/source-trust update
-> future behavior change
```

## Implementation order

```text
1. Information source model
2. Query router
3. Response normalizer
4. Information assimilation
5. Observation-to-belief bridge
6. Contradiction detection
7. Source trust update
8. Belief-to-route impact bridge
9. Information intent resolver
10. Information/belief phase
11. Scenario tests
12. Performance gates
```

## What to stop

Stop using information as immediate truth.

Stop letting guild/guide interactions simply dump usable leads without source/certainty/trust consequences.

Stop storing every answer forever.

Stop checking contradictions globally.

## Consequence if ignored

You will have:

```text
rich entity self-model
rich adventure decisions
combat learning
```

but the entity will still feel omniscient or shallow because information does not have a life cycle.

Phase 5 makes knowledge itself part of the simulation.
