# Phase 8 — World Emergence / Population-Level Consequences

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
entity judges combat engagement
```

Phase 5:

```text
entity handles uncertain information
```

Phase 6:

```text
entity converts reward into growth
```

Phase 7:

```text
entity uses social cooperation as a life strategy
```

Phase 8:

```text
many entity decisions accumulate into visible world change
```

This phase is important because the final target is not only:

```text
one smart entity
```

The final target is:

```text
many imperfect entities
-> many small decisions
-> resources change
-> danger changes
-> services change
-> quests change
-> rumors change
-> economy changes
-> regions evolve
-> future entities react differently
```

Current code already has some world-dynamics foundation: regional trauma/stability recovery, deterministic spawning, camp maturity/spawn/clearing, calamity consequences, boss spawning, resource ecology, threat evolution, raids, camps, hazard effects, and long-run stability checks.

So Phase 8 must **not** duplicate existing passive world-dynamics tests.

It should test the missing layer:

```text
Do entity actions actually create local-to-global world changes that affect future entity decisions?
```

---

# Phase 8 goal

Phase 8 answers:

```text
When many entities act over time, does the world remember and respond?
```

Examples:

```text
many entities harvest iron
-> local iron scarcity increases
-> blacksmith crafting becomes harder
-> iron price rises
-> entities choose alternate routes
```

```text
many heroes die in north_ruin
-> region danger reputation increases
-> guild creates warning/quest pressure
-> cautious entities avoid it
-> brave entities form parties
```

```text
many goblin camps mature
-> raids occur
-> hometown service availability changes
-> quests appear
-> entities change route choice
```

This phase is about **macro feedback loops**.

---

# Phase 8 success definition

Phase 8 is successful when the engine can produce traces like:

```yaml
world_emergence_trace:
  trigger:
    event: repeated_hero_deaths
    region: north_ruin
    count: 5

  world_effect:
    region_trauma_delta: +5.0
    danger_reputation: increased
    guild_pressure: increased
    quest_pressure:
      kind: clear_threat
      urgency: high

  entity_effect:
    cautious_entities:
      route_change: avoid_region
    brave_entities:
      route_change: request_party_or_accept_threat_quest
    low_level_entities:
      route_change: choose_safer_area

  proof: future decisions changed because world state changed
```

The key proof is:

```text
world change affects future decisions
```

Not just:

```text
world value changed numerically
```

---

# Task 1 — Add Phase 8 coverage audit

## Description

Avoid duplicating existing tests.

Existing tests already cover:

```text
regional trauma/stability passive recovery
deterministic spawning
camp maturity and spawn
camp clearing reward
calamity intensity after hero death
boss spawn bounds
resource node caps
long-run stability
population stability
threat bounds
```

Phase 8 should cover:

```text
entity actions -> world aggregate signal
world aggregate signal -> opportunity/quest/service/resource change
world change -> future entity route/decision change
```

## Proposed document

```text
docs/test_coverage/phase8_world_emergence_coverage.md
```

## Checklist

- [x] Existing world-dynamics tests are listed.
- [x] Existing camp/calamity/boss tests are listed.
- [x] Existing long-run stability tests are listed.
- [x] Phase 8 scope is defined as action-to-world-to-future-decision feedback.
- [x] No test duplicates passive trauma recovery.
- [x] No test duplicates raw camp maturity formula.
- [x] No test duplicates boss spawn cap.
- [x] No test duplicates generic long-run memory stability.

---

# Task 2 — Define world emergence domain boundary

## Description

Create a domain layer:

```text
src/domains/world_emergence/
```

This domain should not replace existing world systems.

It should connect:

```text
entity events
-> aggregate world signals
-> world pressure
-> opportunities/quests/information/economy changes
-> future entity decisions
```

Current source already has `WorldDynamicsSystem` handling hazard damage, death-triggered trauma, sovereignty, calamity, standard spawning, resource ecology, threat evolution, boss spawning, raids, and camps. Phase 8 should plug into that instead of rewriting it.

## Proposed service

```python
class WorldEmergenceService:
    def evaluate(
        self,
        state: AuthoritativeState,
        recent_events: Sequence[WorldEvent],
        context: WorldEmergenceContext,
    ) -> WorldEmergenceResult:
        ...
```

## Inputs

```text
recent entity deaths
resource harvest events
quest failures/completions
camp events
shop stock/price events
travel/route danger events
service availability events
rumor/information events
regional trauma/threat
population density
```

## Outputs

```text
world pressure update
opportunity pressure
quest pressure
region memory update
resource scarcity update
economy pressure update
information/rumor seed
trace events
```

## Checklist

- [x] Domain does not directly replace `WorldDynamicsSystem`.
- [x] Domain consumes event streams or bounded recent event summaries.
- [x] Domain produces `StateUpdate` / world update proposals.
- [x] Domain can produce opportunity/quest pressure hints.
- [x] Domain can produce information rumors/leads.
- [x] Domain does not scan all historical events every tick.
- [x] Feature-flagged initially.
- [x] Deterministic under same seed/input.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py
```

Test cases:

```text
test_world_emergence_service_does_not_mutate_state_directly
test_world_emergence_consumes_recent_events
test_world_emergence_outputs_world_update_proposals
test_world_emergence_is_deterministic
test_world_emergence_does_not_replace_world_dynamics_system
```

---

# Task 3 — Implement `WorldEventAggregator`

## Description

Phase 8 needs aggregation.

Do not let each event immediately trigger a huge world update.

Instead:

```text
many small events
-> bounded aggregate signal
-> world effect
```

## Event categories

```text
entity_death
near_death
resource_harvested
resource_depleted
quest_completed
quest_failed
camp_cleared
camp_raid
shop_stock_depleted
service_unavailable
region_entered
region_avoided
rumor_confirmed
rumor_contradicted
party_abandoned
```

## Proposed model

```python
@dataclass(frozen=True)
class WorldEventAggregate:
    region_id: str | None
    category: str
    subject: str | None
    count: int
    severity_sum: float
    first_tick: int
    last_tick: int
```

## Service

```python
class WorldEventAggregator:
    def aggregate(
        self,
        events: Sequence[WorldEvent],
        window: TickWindow,
    ) -> tuple[WorldEventAggregate, ...]:
        ...
```

## Checklist

- [x] Aggregates by region.
- [x] Aggregates by category.
- [x] Aggregates by subject when useful.
- [x] Uses bounded time window.
- [x] Ignores low-salience spam.
- [x] Keeps deterministic ordering.
- [x] Does not store unbounded history.
- [x] Can summarize 1,000 events into small aggregate list.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py
```

Test cases:

```text
test_deaths_aggregate_by_region
test_resource_depletions_aggregate_by_resource_type
test_quest_failures_aggregate_by_region_and_kind
test_low_salience_events_are_ignored
test_aggregate_window_is_bounded
test_aggregation_order_is_deterministic
```

---

# Task 4 — Implement `RegionalPressureModel`

## Description

Regions should accumulate meaningful pressures.

Existing `RegionState` already has fields such as trauma, stability, hazard, calamity, influence, retaliation pressure, and ownership behavior in the source/tests. Phase 8 should add a higher-level pressure interpretation layer, not duplicate the numeric update rules.

## Pressures

```text
danger_pressure
resource_pressure
quest_pressure
trade_pressure
travel_pressure
camp_pressure
calamity_pressure
reputation_pressure
service_pressure
```

## Proposed model

```python
@dataclass(frozen=True)
class RegionalPressure:
    region_id: str
    pressure_kind: str
    intensity: float
    confidence: float
    source_aggregates: tuple[str, ...]
    reason: str
```

## Service

```python
class RegionalPressureService:
    def evaluate(
        self,
        state: AuthoritativeState,
        aggregates: tuple[WorldEventAggregate, ...],
    ) -> tuple[RegionalPressure, ...]:
        ...
```

## Checklist

- [x] Repeated deaths increase danger pressure.
- [x] Repeated resource depletion increases resource pressure.
- [x] Repeated quest failures increase quest pressure.
- [x] Camp maturity/raid events increase camp pressure.
- [x] Successful clearing can reduce danger/camp pressure.
- [x] Pressure values are bounded.
- [x] Pressure update is deterministic.
- [x] Pressure does not directly force entity behavior.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py
```

Test cases:

```text
test_repeated_deaths_increase_danger_pressure
test_resource_depletion_increases_resource_pressure
test_camp_raid_increases_camp_pressure
test_camp_clearing_reduces_camp_pressure
test_pressure_values_are_bounded
test_pressure_output_has_reason
```

---

# Task 5 — Implement `ScarcityModel`

## Description

Resource scarcity must become visible.

Current code has resource nodes and ecology/replenishment, and worldbuilding expansion can generate resource nodes from world specs.

But Phase 8 needs higher-level scarcity interpretation:

```text
iron_ore is becoming scarce in old_mine
herbs are abundant in near_forest
moon_resin is rare and uncertain
```

This feeds:

```text
price changes
quest pressure
entity route choice
information rumors
crafting blockers
```

## Proposed model

```python
@dataclass(frozen=True)
class ResourceScarcitySignal:
    region_id: str
    resource_type: str
    availability: float
    scarcity_level: float
    trend: str
    confidence: float
    reason: str
```

## Service

```python
class ScarcityModelService:
    def evaluate(
        self,
        state: AuthoritativeState,
        aggregates: tuple[WorldEventAggregate, ...],
    ) -> tuple[ResourceScarcitySignal, ...]:
        ...
```

## Checklist

- [x] Depleted nodes increase scarcity.
- [x] Replenishment decreases scarcity.
- [x] Heavy harvesting trend increases scarcity.
- [x] Scarcity is region-specific.
- [x] Scarcity is resource-specific.
- [x] Scarcity values are bounded.
- [x] Scarcity can feed economy/opportunity later.
- [x] No full-world scan every tick; use cadence or dirty region/resource index.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_scarcity_model.py
```

Test cases:

```text
test_repeated_iron_depletion_increases_old_mine_scarcity
test_replenishment_reduces_scarcity
test_scarcity_is_region_specific
test_scarcity_is_resource_specific
test_scarcity_values_are_bounded
test_scarcity_does_not_mutate_resource_nodes_directly
```

---

# Task 6 — Implement `WorldOpportunityPressureService`

## Description

World pressures should create opportunities.

Examples:

```text
danger pressure high
-> guild posts clear-threat quest

resource scarcity high
-> gathering quest / trade opportunity

camp pressure high
-> raid warning / camp clearing quest

service pressure high
-> repair/healer/shop stock issue

travel pressure high
-> escort quest / route warning
```

## Proposed model

```python
@dataclass(frozen=True)
class WorldOpportunityPressure:
    id: str
    kind: str
    region_id: str
    subject: str | None
    urgency: float
    suggested_opportunity_kinds: tuple[str, ...]
    reason: str
```

## Service

```python
class WorldOpportunityPressureService:
    def evaluate(
        self,
        pressures: tuple[RegionalPressure, ...],
        scarcity: tuple[ResourceScarcitySignal, ...],
        state: AuthoritativeState,
    ) -> tuple[WorldOpportunityPressure, ...]:
        ...
```

## Opportunity kinds

```text
clear_threat
scout_region
gather_resource
escort_travel
defend_town
investigate_ruin
trade_material
repair_supply_chain
camp_clear
boss_warning
```

## Checklist

- [x] Danger pressure can create clear-threat opportunity pressure.
- [x] Scarcity can create gather/trade opportunity pressure.
- [x] Camp pressure can create camp-clear pressure.
- [x] Calamity pressure can create boss-warning/investigation pressure.
- [x] Pressure is bounded and decays if resolved.
- [x] Opportunity pressure does not automatically create accepted quests.
- [x] Output can be consumed by quest/opportunity providers.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py
```

Test cases:

```text
test_danger_pressure_creates_clear_threat_opportunity
test_resource_scarcity_creates_gather_or_trade_opportunity
test_camp_pressure_creates_camp_clear_opportunity
test_opportunity_pressure_decays_after_resolution
test_opportunity_pressure_does_not_auto_accept_quest
```

---

# Task 7 — Implement `DynamicQuestSeedService`

## Description

The world should generate quest seeds from world pressures.

Do not rewrite the full quest system.

Generate **quest seeds**, not full hardcoded quests.

## Quest seed examples

```text
clear goblin camp
investigate north ruin
gather iron ore due to shortage
escort traveler through dangerous road
hunt wolves after attacks
defend town from raid
```

## Proposed model

```python
@dataclass(frozen=True)
class QuestSeed:
    id: str
    kind: str
    region_id: str
    subject: str | None
    difficulty_hint: int
    reward_hint: int
    urgency: float
    source_pressure_id: str
    valid_resolution_tags: tuple[str, ...]
```

## Service

```python
class DynamicQuestSeedService:
    def generate(
        self,
        opportunity_pressures: tuple[WorldOpportunityPressure, ...],
        state: AuthoritativeState,
    ) -> tuple[QuestSeed, ...]:
        ...
```

## Checklist

- [x] High danger pressure can generate hunt/clear-threat seed.
- [x] Resource scarcity can generate gather/trade seed.
- [x] Camp pressure can generate camp-clear seed.
- [x] Travel danger can generate escort/scout seed.
- [x] Quest seed IDs are deterministic.
- [x] Duplicate seeds are avoided.
- [x] Seed count is capped.
- [x] Seeds do not become accepted quests automatically.
- [x] Existing quest completion/reward tests are not duplicated.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py
```

Test cases:

```text
test_danger_pressure_generates_clear_threat_seed
test_scarcity_pressure_generates_gather_seed
test_camp_pressure_generates_camp_clear_seed
test_quest_seed_ids_are_deterministic
test_duplicate_quest_seeds_are_not_generated
test_quest_seed_count_is_capped
```

---

# Task 8 — Implement `RumorSeedService`

## Description

World changes should become discoverable through information systems.

Examples:

```text
many deaths in north_ruin
-> rumor: north_ruin is dangerous

iron depleted in old_mine
-> rumor: old_mine is running dry

camp raid happened
-> rumor: goblins are preparing attacks

boss spawned
-> rumor: terrifying presence in forest
```

This connects Phase 8 back to Phase 5.

## Proposed model

```python
@dataclass(frozen=True)
class RumorSeed:
    id: str
    subject: str
    region_id: str | None
    certainty: float
    source_kind: str
    spread_scope: str
    reason: str
```

## Service

```python
class RumorSeedService:
    def generate(
        self,
        pressures: tuple[RegionalPressure, ...],
        scarcity: tuple[ResourceScarcitySignal, ...],
        state: AuthoritativeState,
    ) -> tuple[RumorSeed, ...]:
        ...
```

## Checklist

- [x] High danger pressure creates danger rumor seed.
- [x] Scarcity creates scarcity rumor seed.
- [x] Camp/raid pressure creates threat rumor seed.
- [x] Rumor certainty is lower than direct observation.
- [x] Rumor seeds are scoped by region/town.
- [x] Rumor seed count is capped.
- [x] Rumor does not equal truth for all entities.
- [x] Phase 5 information providers can expose rumor seeds later.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py
```

Test cases:

```text
test_danger_pressure_generates_low_certainty_rumor
test_scarcity_generates_region_scoped_rumor
test_camp_raid_generates_threat_rumor
test_rumor_seed_count_is_capped
test_rumor_does_not_directly_update_all_entity_knowledge
```

---

# Task 9 — Implement `ServiceStatePressureModel`

## Description

Services should not remain static under world pressure.

Examples:

```text
blacksmith affected by iron scarcity
shop affected by travel danger
healer affected by high casualties
guild affected by threat pressure
inn affected by refugee/traffic pressure
```

Do not build full economy yet. Start with service pressure signals.

## Proposed model

```python
@dataclass(frozen=True)
class ServicePressure:
    service_id: str
    pressure_kind: str
    intensity: float
    effect_tags: tuple[str, ...]
    reason: str
```

## Effects

```text
price_pressure
stock_pressure
quest_pressure
service_delay
repair_demand
healing_demand
information_demand
```

## Checklist

- [x] Resource scarcity can create blacksmith stock/material pressure.
- [x] Danger pressure can create guild quest pressure.
- [x] High casualties can create healer demand pressure.
- [x] Travel danger can create shop stock/supply pressure.
- [x] Pressure is bounded.
- [x] Service pressure does not directly execute transactions.
- [x] Service opportunity providers can read pressure later.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py
```

Test cases:

```text
test_iron_scarcity_creates_blacksmith_material_pressure
test_high_danger_creates_guild_quest_pressure
test_high_death_count_creates_healer_demand_pressure
test_travel_danger_creates_shop_supply_pressure
test_service_pressure_values_are_bounded
```

---

# Task 10 — Implement `WorldToEntitySignalBridge`

## Description

World emergence matters only if entities can perceive or learn it.

Bridge world pressures into:

```text
opportunities
information rumors
risk beliefs
knowledge leads
quest availability
route scoring modifiers
```

This should be mediated by visibility/information, not global omniscience.

## Proposed service

```python
class WorldToEntitySignalBridge:
    def expose(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        world_signals: WorldEmergenceResult,
        context: ExposureContext,
    ) -> EntitySignalExposure:
        ...
```

## Exposure channels

```text
direct observation
local town rumor
guild notice
guide warning
region entry
quest board
ally report
service price/stock change
```

## Checklist

- [x] Entity only receives local/known/visible signals.
- [x] Direct observation has higher certainty than rumor.
- [x] Guild/guide can expose relevant pressure.
- [x] Far-away world pressure does not become automatic knowledge.
- [x] Exposure can trigger Phase 5 information/belief update.
- [x] Exposure can trigger Phase 3 route reevaluation.
- [x] Exposure is deterministic and bounded.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py
```

Test cases:

```text
test_local_region_danger_exposes_warning_to_entity_in_region
test_town_guild_exposes_nearby_threat_pressure
test_far_region_pressure_not_exposed_without_source
test_rumor_exposure_has_lower_certainty_than_observation
test_exposure_can_trigger_route_reevaluation_hint
```

---

# Task 11 — Add world emergence integration phase

## Description

Add a bounded phase.

Do not evaluate full world emergence every tick.

Use cadence + dirty signals.

## Trigger conditions

```text
enough relevant events accumulated
resource node depleted
region death count changed
camp raid/clearing happened
boss/calamity event happened
quest failure/completion cluster
service stock changed
scheduled world emergence cadence
```

## Skip conditions

```text
no relevant aggregates
feature flag disabled
world emergence budget exhausted
region unchanged
cadence not reached
```

## Proposed phase

```text
WorldEmergencePhase:
  1. aggregate recent events
  2. evaluate regional pressures
  3. evaluate scarcity
  4. generate opportunity pressure
  5. generate quest seeds
  6. generate rumor seeds
  7. evaluate service pressure
  8. expose local signals to entities through Phase 5/Phase 3 hooks
  9. emit trace events
```

## Checklist

- [x] Phase is feature-flagged initially.
- [x] Phase runs on cadence/event threshold.
- [x] Phase processes bounded event window.
- [x] Phase does not scan entire event history.
- [x] Phase does not directly force entity actions.
- [x] Phase produces world update proposals and signal exposures.
- [x] Phase can trigger route reevaluation.
- [x] Deterministic under same seed/input.

## TDD tests

```text
tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py
```

Test cases:

```text
test_phase_skips_when_no_relevant_events
test_phase_runs_after_resource_depletion_cluster
test_phase_runs_after_death_cluster
test_phase_respects_feature_flag
test_phase_processes_bounded_event_window
test_phase_outputs_world_signals_not_direct_entity_action
test_phase_can_trigger_route_reevaluation_hint
```

---

# Task 12 — Add Phase 8 scenario tests

These are the important TDD tests.

They should prove:

```text
entity actions change world
world changes future entity behavior
```

---

## Scenario 8.1 — Iron scarcity changes crafting route

```text
World:
- old_mine has limited iron nodes
- several entities harvest iron
- blacksmith recipes need iron

Expected:
- iron scarcity signal increases for old_mine
- blacksmith material pressure increases
- later entities either:
  - ask for alternate material source
  - choose different upgrade route
  - accept scarcity-related quest
  - buy at higher price if economy hook enabled
```

Forbidden:

```text
later entities behave exactly as if iron is abundant
scarcity becomes global truth for entities without exposure
resource nodes exceed cap
```

---

## Scenario 8.2 — Repeated deaths create danger reputation

```text
World:
- north_ruin has repeated hero deaths

Expected:
- danger pressure increases
- rumor/quest seed generated
- cautious entities avoid or seek information
- brave/social entities may form party or accept clear-threat quest
```

Forbidden:

```text
all entities automatically know exact danger
all entities ignore repeated deaths
death count directly forces route with no trace
```

---

## Scenario 8.3 — Camp maturity creates regional pressure

```text
World:
- goblin camp matures and spawns/raids
```

Expected:

```text
camp pressure increases
guild/quest pressure appears
nearby entities receive warning/opportunity through local exposure
some entities change route to avoid/help/clear camp
```

Do not duplicate raw camp maturity formula; existing tests already cover camp maturity and spawn.

---

## Scenario 8.4 — Camp clearing reduces pressure

```text
World:
- camp pressure high
- party clears camp

Expected:
- camp pressure decreases
- region danger pressure decreases or stabilizes
- future cautious entities become more willing to travel
```

---

## Scenario 8.5 — Resource depletion causes route diversification

```text
World:
- many entities need same herb resource
- nearby herb nodes depleted

Expected:
- later entities diversify:
  - ask info for alternate source
  - buy from shop if available
  - choose different quest
  - defer
```

---

## Scenario 8.6 — Rumor exposure is local, not omniscient

```text
World:
- wolf_den danger pressure high
- only entities in hometown hear guild warning
- entity far away without source should not know

Expected:
- hometown entities update risk/route
- isolated entity does not magically know
```

---

## Scenario 8.7 — Service pressure affects decisions

```text
World:
- healer demand high from many injuries
- blacksmith material pressure high from iron scarcity

Expected:
- service opportunity/provider exposes pressure
- entities may choose:
  - alternate service
  - delay
  - pay higher cost if economy hook enabled
  - seek material supply quest
```

## Test file

```text
tests/integration/scenarios/test_phase8_world_emergence_scenarios.py
```

## Checklist

- [x] Scenarios assert world pressure, not raw formula only.
- [x] Scenarios assert future entity route/decision change.
- [x] Scenarios assert no omniscient global knowledge.
- [x] Scenarios assert local exposure path.
- [x] Scenarios do not duplicate passive world dynamics.
- [x] Scenarios are deterministic.
- [x] Each scenario includes forbidden behavior assertions.

---

# Task 13 — Add world emergence trace events

## Event types

```text
WorldEventAggregated
RegionalPressureUpdated
ResourceScarcitySignalUpdated
WorldOpportunityPressureGenerated
QuestSeedGenerated
RumorSeedGenerated
ServicePressureUpdated
WorldSignalExposedToEntity
WorldRouteImpactGenerated
```

## Example

```yaml
event_type: RegionalPressureUpdated
region_id: north_ruin
pressure_kind: danger
old_intensity: 0.35
new_intensity: 0.62
reason: "5 entity deaths in recent window"
```

```yaml
event_type: WorldSignalExposedToEntity
entity_id: 12
region_id: north_ruin
channel: guild_warning
signal: danger_pressure
certainty: 0.65
future_hint: avoid_or_prepare
```

## Checklist

- [x] Events include reason.
- [x] Events include source aggregate.
- [x] Events include before/after where applicable.
- [x] Entity exposure events include channel and certainty.
- [x] Events emitted only on meaningful change.
- [x] Events do not mutate authoritative state.
- [x] Event volume bounded.
- [x] Existing observability parity tests still pass.

## TDD tests

```text
tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py
```

Test cases:

```text
test_regional_pressure_event_contains_before_after_and_reason
test_scarcity_event_contains_resource_and_region
test_quest_seed_event_contains_source_pressure
test_entity_exposure_event_contains_channel_and_certainty
test_event_generation_does_not_change_state_hash
```

---

# Task 14 — Add Phase 8 performance gates

## Description

World emergence can become expensive if it scans all events, regions, resources, and entities.

Do not do that.

## Required metrics

```text
world_events_aggregated_total
aggregates_generated_total
regions_evaluated_total
resources_evaluated_total
pressures_generated_total
quest_seeds_generated_total
rumor_seeds_generated_total
entity_signal_exposures_total
avg_world_emergence_ms
p95_world_emergence_ms
skipped_due_to_cadence
skipped_due_to_budget
event_window_size
```

## Performance tests

```text
10 entities, 500 ticks
100 entities, 500 ticks
500 entities, 200 ticks
1000 events in bounded window
100 regions with sparse events
resource-heavy scenario
```

## Checklist

- [x] Event window bounded.
- [x] Only dirty regions/resources evaluated.
- [x] Quest seed count capped.
- [x] Rumor seed count capped.
- [x] Entity exposure scoped by region/source.
- [x] No global all-entity exposure.
- [x] Feature flag OFF matches old behavior.
- [x] Feature flag ON stays inside agreed overhead.
- [x] Determinism hash stable.
- [x] Performance report written.

## Test file

```text
tests/perf/test_phase8_world_emergence_budget.py
```

---

# Phase 8 test files to add

```text
tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py
tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py
tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py
tests/unit/domains/world_emergence/test_phase8_scarcity_model.py
tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py
tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py
tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py
tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py
tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py
tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py

tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py
tests/integration/scenarios/test_phase8_world_emergence_scenarios.py
tests/perf/test_phase8_world_emergence_budget.py

docs/test_coverage/phase8_world_emergence_coverage.md
```

---

# Phase 8 non-goals

Do **not** implement these yet:

```text
full economy simulation
full dynamic market pricing
global news network
political/faction governance
settlement construction
population reproduction
large-scale trade routes
full ecology simulation
disease/plague system
seasonal climate simulation
```

Also do **not** duplicate existing tests for:

```text
passive trauma recovery
camp maturity formula
camp clearing reward formula
calamity intensity increment
boss spawn cap
resource node cap
long-run stability
deterministic spawning
```

Those already exist in the current test export/source surface.

---

# Phase 8 completion criteria

Phase 8 is done when this is true:

```text
The world is no longer just a static stage.

Entity actions accumulate into regional, resource, service, quest, rumor,
and danger pressures.

Those pressures are exposed locally and imperfectly.

Future entities change decisions because of them.
```

Minimum proof:

```text
resource depletion changes later route choice
repeated deaths create danger reputation
camp pressure creates quest/warning pressure
camp clearing reduces future pressure
rumors are local, not omniscient
service pressure affects service/opportunity decisions
world emergence overhead remains bounded
```

---

# Priority Plan

## What changes in Phase 8

Before Phase 8:

```text
entities act in the world
```

After Phase 8:

```text
entity actions reshape the world,
and the reshaped world changes future entities
```

## Implementation order

```text
1. Coverage audit
2. World emergence domain boundary
3. WorldEventAggregator
4. RegionalPressureModel
5. ScarcityModel
6. WorldOpportunityPressureService
7. DynamicQuestSeedService
8. RumorSeedService
9. ServiceStatePressureModel
10. WorldToEntitySignalBridge
11. WorldEmergencePhase
12. Scenario tests
13. Trace events
14. Performance gates
```

## What to stop

Stop treating world state as only passive numbers:

```text
trauma_score
stability
hazard_level
resource count
camp maturity
```

Those numbers must become:

```text
signals
pressures
opportunities
rumors
quest seeds
route modifiers
future behavior changes
```

## Consequence if ignored

You will have smarter entities, but they will still live in a world that does not meaningfully remember them.

The simulation may show individual intelligence, but not world history.

Phase 8 makes the world become a participant in the story.
