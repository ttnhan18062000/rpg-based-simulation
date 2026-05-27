# Phase 1 — World Capability Foundation

## Phase 1 goal

Build the smallest world-side foundation that makes entity decision-making visible.

Not:

```text
rewrite the engine
```

But:

```text
keep current execution systems
add richer data
add narrow query/provider layer
add scenario-driven tests
measure performance
```

Phase 1 should answer:

```text
What exists in the world?
What can an entity possibly do with it?
Why is an action blocked?
Who can provide information?
Can we observe the resulting story path?
```

---

# Phase 1 success definition

Phase 1 is successful when a level-1 adventurer in hometown can face a simple need like:

```text
I need to get stronger.
```

and the engine can expose multiple valid route families:

```text
buy item
craft item
gather material
ask guide
take easy quest
fight weak monster
retreat/recover
defer because blocked
```

without hardcoding one story path.

---

# Task 1 — Create scenario-driven TDD harness

## Description

Current testing can prove isolated mechanics, but it does not prove a coherent life path.

Before implementing new logic, create a scenario harness that can run a compact world and evaluate route-family behavior.

The test should not assert:

```text
entity must ask blacksmith first
```

It should assert:

```text
entity must choose at least one valid route toward getting stronger
```

## Proposed solution

Create a scenario spec format:

```yaml
scenario_id: phase1_first_growth_routes

world_pack: phase1_adventure_seed

actors:
  - id: arl
    role: HERO
    level: 1
    class: warrior
    start: hometown
    gold: 60
    equipment:
      weapon: rusted_sword

initial_pressure:
  - weak_weapon
  - nearby_easy_quest_available

valid_route_families:
  - buy_upgrade
  - craft_upgrade
  - gather_for_gold
  - ask_information
  - accept_easy_quest
  - hunt_weak_enemy
  - defer_with_reason

forbidden_behavior:
  - omniscient_hidden_source
  - buy_without_gold
  - craft_without_materials
  - infinite_same_failed_action
  - action_after_death
  - no_trace_for_selected_route
```

Create a scenario runner that outputs:

```text
scenario_scorecard.json
route_trace.jsonl
world_diff.json
performance_report.json
```

## Checklist

- [x] Scenario spec can define actors, world pack, valid route families, and forbidden behaviors.
- [x] Scenario runner can execute N ticks deterministically.
- [x] Scenario runner records selected route family, not just raw actions.
- [x] Scenario scorecard distinguishes:
  - pass
  - partial pass
  - fail
  - invalid behavior
  - missing capability

- [x] Scenario can fail before implementation, proving test-first workflow.
- [x] Each scenario records performance:
  - total ticks
  - average tick time
  - provider call count
  - strategic evaluation count

- [x] At least 3 initial failing scenarios exist before provider implementation.

## Important notes

This is not optional. Without this, you will implement “smart” logic and have no proof that it creates better life behavior.

---

# Task 2 — Define Phase 1 content pack

## Description

The current world data is too thin to reveal meaningful entity intelligence. If there are only a few resources/actions, enhanced cognition will still produce shallow behavior.

Phase 1 needs a compact but rich adventure content pack.

## Proposed solution

Add a `phase1_adventure_seed` pack.

Minimum content:

```yaml
resources:
  - wood
  - herb
  - iron_ore
  - beast_fang
  - wolf_pelt
  - moon_resin
  - crystal_shard
  - goblin_token
  - ancient_fragment
  - healing_flower

items:
  - rusted_sword
  - wooden_staff
  - basic_bow
  - leather_armor
  - iron_sword
  - hunter_blade
  - apprentice_staff
  - small_potion
  - travel_ration
  - repair_kit

recipes:
  iron_sword:
    requires:
      iron_ore: 2
      wood: 1
      gold: 40
  hunter_blade:
    requires:
      iron_ore: 2
      beast_fang: 1
      moon_resin: 1
      gold: 50
  small_potion:
    requires:
      healing_flower: 1
      crystal_shard: 1
      gold: 10

enemies:
  - rat
  - wolf
  - goblin
  - goblin_archer
  - cave_spider
  - bandit_scout
  - elite_goblin

regions:
  - hometown
  - near_forest
  - old_mine
  - wolf_den
  - north_ruin
  - goblin_camp
  - moon_cave

services:
  - shop
  - blacksmith
  - guide
  - guild
  - inn
  - trainer
  - healer
  - storage
```

## Checklist

- [x] World pack can be loaded from data, not hardcoded in tests.
- [x] Every item has:
  - tags
  - base value
  - rarity
  - use category

- [x] Every resource has:
  - source region
  - yield item
  - depletion behavior
  - optional tool/skill requirement

- [x] Every enemy has:
  - visible danger hint
  - actual combat profile
  - loot table
  - region spawn mapping

- [x] Every service has:
  - location
  - supported affordances
  - knowledge scope, if applicable

- [x] Every recipe has:
  - required materials
  - service requirement
  - gold cost
  - output item

- [x] At least one material is intentionally unknown through normal guide knowledge, such as `moon_resin`.

## Important notes

Keep the data small but semantically rich. Do not add 100 items. Add 10–20 items that create real decision branches.

---

# Task 3 — Add data registries, not full world rewrite

## Description

The content pack needs a structured place to live.

Do not scatter item/resource/enemy/recipe definitions across shop, blacksmith, guild, quest, and test code.

## Proposed solution

Add lightweight registries:

```text
ItemRegistry
ResourceRegistry
EnemyRegistry
RecipeRegistry
ServiceRegistry
RegionRegistry
QuestTemplateRegistry
```

Example shape:

```python
@dataclass(frozen=True)
class ItemDef:
    id: str
    tags: tuple[str, ...]
    rarity: str
    base_value: int
    use_kind: str
    class_fit: tuple[str, ...] = ()
```

```python
@dataclass(frozen=True)
class ResourceDef:
    id: str
    yield_item: str
    source_region_tags: tuple[str, ...]
    required_tool: str | None = None
    base_difficulty: int = 1
```

## Checklist

- [x] Registries are read-only during simulation.
- [x] Registries are loadable from YAML/JSON or deterministic Python definitions.
- [x] Existing shop/blacksmith/resource systems can reference registries without being rewritten.
- [x] Registry lookups are O(1) by ID.
- [x] Missing registry entry fails fast with a clear error.
- [x] Tests verify all recipe material IDs exist in `ItemRegistry` or `ResourceRegistry`.
- [x] Tests verify enemy loot table item IDs exist.
- [x] Tests verify service-supported affordance kinds are valid.

## Important notes

This is infrastructure, not behavior. Do not turn this into a general plugin framework yet.

---

# Task 4 — Implement `RequirementEvaluator`

## Description

The engine needs a generic way to explain why an intended route/action cannot happen.

Without this, blockers remain ad hoc:

```text
not enough gold
missing material
unknown location
too far
too dangerous
service unavailable
```

The requirement evaluator turns failures into structured blocker candidates.

## Proposed solution

Create a small evaluator:

```python
@dataclass(frozen=True)
class Requirement:
    kind: str
    subject: str | None = None
    quantity: int = 1

@dataclass(frozen=True)
class RequirementResult:
    requirement: Requirement
    passed: bool
    blocker_kind: str | None = None
    reason: str | None = None
    suggested_resolution_tags: tuple[str, ...] = ()
```

Example requirements:

```text
has_gold:80
has_item:iron_ore:2
knows_fact:material.moon_resin.source
near_service:blacksmith
target_alive:wolf_12
inventory_space:1
```

Example result:

```yaml
requirement: has_item:moon_resin:1
passed: false
blocker_kind: missing_material
reason: entity lacks moon_resin
suggested_resolution_tags:
  - ask_information
  - buy_material
  - research_location
  - choose_alternative_recipe
```

## Checklist

- [x] Evaluator supports Phase 1 requirement kinds:
  - has_gold
  - has_item
  - knows_fact
  - near_service
  - inventory_space
  - target_exists
  - target_alive
  - service_available
  - recipe_known

- [x] Failed requirements produce structured blocker kinds.
- [x] Requirement results are deterministic.
- [x] Requirement evaluator does not mutate state.
- [x] Unit tests cover each requirement kind.
- [x] Scenario test verifies missing `moon_resin` becomes `missing_material` or `unknown_source`, not silent failure.
- [x] Scenario test verifies `not_enough_gold` leads to `gather_for_gold` or `easy_quest` route.
- [x] Performance test confirms evaluator cost is bounded for 10, 30, and 100 entities.

## Important notes

This is the most important Phase 1 component. Blocker reasoning is the bridge from mechanics to story.

---

# Task 5 — Implement narrow `InformationProvider`

## Description

Entities should not know hidden truth. They should ask scoped information sources.

But do not build a giant knowledge system. Start with guide/guild/blacksmith only.

## Proposed solution

Create an interface:

```python
@dataclass(frozen=True)
class InformationQuery:
    kind: str
    subject: str
    actor_id: int

@dataclass(frozen=True)
class InformationResponse:
    answer_kind: str
    facts: tuple[KnowledgeFact, ...] = ()
    unknowns: tuple[str, ...] = ()
    suggested_leads: tuple[LeadState, ...] = ()
    certainty: float = 0.0
    source_id: str | int | None = None
    cost_gold: int = 0
```

Initial providers:

```text
GuideInformationProvider
GuildInformationProvider
BlacksmithInformationProvider
```

Example:

```yaml
query:
  kind: material_source
  subject: moon_resin

guide_response:
  answer_kind: partial
  facts: []
  unknowns:
    - material.moon_resin.source
  suggested_leads:
    - research:north_ruin
  certainty: 0.55
  cost_gold: 10
```

## Checklist

- [x] Guide can answer common resource sources.
- [x] Guide can return partial answer for rare/secret material.
- [x] Guild can answer basic quest and regional danger hints.
- [x] Blacksmith can answer recipe requirements, not necessarily material source.
- [x] Provider response distinguishes:
  - known
  - partial
  - unknown
  - rumor
  - contradiction, later phase optional

- [x] Asking information can cost gold.
- [x] Entity does not receive hidden world truth unless provider exposes it.
- [x] Scenario test verifies `moon_resin` source is not directly known.
- [x] Scenario test verifies guide can suggest `north_ruin` research lead without revealing exact source.
- [x] Scenario test verifies blacksmith gives recipe requirements but not full material acquisition path.

## Important notes

Do not store the guide’s whole knowledge base in entity memory. Entity stores only relevant answer, lead, or unknown.

---

# Task 6 — Implement `ResourceOpportunityProvider`

## Description

Entities need to see possible resource actions without scanning the whole world.

The provider answers:

```text
What resource opportunities are relevant to this entity now?
```

## Proposed solution

Create provider:

```python
@dataclass(frozen=True)
class Opportunity:
    kind: str
    target_id: str | int
    subject: str
    estimated_reward: float
    estimated_risk: float
    requirements: tuple[Requirement, ...]
    confidence: float
```

`ResourceOpportunityProvider` returns opportunities from:

```text
nearby visible resource nodes
known resource facts
active material blockers
active recipe requirements
```

Example:

```yaml
opportunity:
  kind: gather_resource
  target_id: node_iron_1
  subject: iron_ore
  estimated_reward: 30
  estimated_risk: 0.2
  requirements:
    - near_target
    - inventory_space
```

## Checklist

- [x] Provider returns nearby visible nodes.
- [x] Provider returns known-source nodes for active material needs.
- [x] Provider does not scan all nodes if context is scoped.
- [x] Provider can explain why an opportunity is unavailable:
  - depleted
  - too far
  - dangerous region
  - inventory full

- [x] Scenario test verifies entity can identify `iron_ore` opportunity after learning source.
- [x] Scenario test verifies depleted node produces blocker/detour, not repeated harvest.
- [x] Performance test confirms provider result count is capped.

## Important notes

Limit results. Example: max 5 candidate resource opportunities per strategic evaluation.

---

# Task 7 — Implement `ServiceOpportunityProvider`

## Description

Town services already exist mechanically, but entity cognition needs a general way to discover relevant service opportunities.

## Proposed solution

Provider returns opportunities for:

```text
shop buy/sell
blacksmith craft/repair
guide ask info
guild quest/info
inn rest
trainer train
healer heal
storage deposit/withdraw
```

Phase 1 can start with:

```text
shop
blacksmith
guide
guild
inn
```

Example:

```yaml
opportunity:
  kind: ask_information
  target_id: guide_hometown
  subject: material.moon_resin.source
  estimated_reward: knowledge
  requirements:
    - near_service:guide
    - has_gold:10
```

## Checklist

- [x] Provider returns only services in current town/known region.
- [x] Provider can return service opportunities relevant to active blockers.
- [x] Shop exposes buy/sell opportunities for Phase 1 items.
- [x] Blacksmith exposes repair/craft/recipe inquiry opportunities.
- [x] Guide exposes information opportunities.
- [x] Guild exposes easy quest and danger info opportunities.
- [x] Inn exposes rest opportunity.
- [x] Scenario test verifies insufficient gold can produce shop rejection and earn-gold alternatives.
- [x] Scenario test verifies damaged equipment can expose repair opportunity.
- [x] Scenario test verifies missing recipe/material exposes blacksmith/guide opportunities.

## Important notes

Do not directly execute service calls from provider. Provider only describes options. Existing action systems execute.

---

# Task 8 — Add minimal `ActionIntent` adapter

## Description

Current engine has multiple action surfaces: router actions, domain actions, town wrappers, and system enforcers. Phase 1 should not unify everything, but it needs a thin adapter so scenario tests can trace chosen intent to actual execution.

## Proposed solution

Create:

```python
@dataclass(frozen=True)
class ActionIntent:
    kind: str
    actor_id: int
    target_id: str | int | None = None
    payload: Mapping[str, object] = field(default_factory=dict)
    source_opportunity_id: str | None = None
    reason: str | None = None
```

Map only Phase 1 intents:

```text
MOVE_TO
ASK_INFORMATION
BUY_ITEM
SELL_ITEM
REQUEST_CRAFT
REPAIR_GEAR
ACCEPT_QUEST
HARVEST_RESOURCE
ATTACK_TARGET
REST_AT_INN
RETURN_TOWN
```

## Checklist

- [x] `ActionIntent` can represent Phase 1 route actions.
- [x] Intent adapter delegates to existing mechanics where available.
- [x] Intent execution produces existing `EntityUpdate` / `StateUpdate`.
- [x] Intent trace records:
  - why selected
  - opportunity source
  - requirements checked
  - execution result

- [x] Invalid intent does not mutate state.
- [x] Scenario test verifies `REQUEST_CRAFT` fails legally without materials.
- [x] Scenario test verifies `BUY_ITEM` fails legally without gold.
- [x] Scenario test verifies `HARVEST_RESOURCE` respects depletion/proximity/inventory.

## Important notes

This is an adapter, not a new execution engine.

Do not replace `ActionRouter`, `ShopService`, `BlacksmithService`, or movement/combat systems in Phase 1.

---

# Task 9 — Add Phase 1 route-family classifier

## Description

Scenario tests need to know what route the entity is following.

Raw actions are too low-level:

```text
move
interact
buy
attack
```

The scenario scorecard needs route families:

```text
buy_upgrade
craft_upgrade
ask_information
gather_for_gold
easy_quest
hunt_weak_enemy
recover
defer
```

## Proposed solution

Create a classifier that consumes action/intent/project traces.

Example:

```python
class RouteFamilyClassifier:
    def classify(trace: list[TraceEvent]) -> set[str]:
        ...
```

Rules:

```text
ASK_INFORMATION + material_source query -> ask_information
REQUEST_CRAFT + missing materials -> craft_upgrade
BUY_ITEM + equipment tag -> buy_upgrade
HARVEST_RESOURCE + sell later -> gather_for_gold
ATTACK_TARGET + weak enemy + quest target -> hunt_weak_enemy
REST/EAT/INN -> recover
```

## Checklist

- [x] Classifier works from trace, not hardcoded scenario.
- [x] Classifier can detect multiple route families in one run.
- [x] Scenario scorecard reports detected route families.
- [x] Missing route family is reported as a test failure only if scenario requires it.
- [x] Forbidden route patterns are detected:
  - repeated same failed action
  - hidden knowledge usage
  - invalid transfer

- [x] Classifier has unit tests for synthetic traces.
- [x] Classifier has integration test on Phase 1 world.

## Important notes

This is essential for TDD. Otherwise you cannot prove the engine produced a story-like route.

---

# Task 10 — Add performance budget gates for providers

## Description

Provider-based architecture can destroy performance if every entity queries everything.

Phase 1 must include performance gates from day one.

## Proposed solution

Add counters:

```text
provider_calls_total
provider_calls_by_kind
opportunities_returned_total
requirements_evaluated_total
avg_provider_time_ms
strategic_eval_time_ms
tick_time_ms
```

Add a performance test:

```text
10 entities
30 entities
100 entities
same Phase 1 world pack
run 500 ticks
compare baseline vs provider-enabled
```

## Checklist

- [x] Provider calls are counted.
- [x] Each provider has max result cap.
- [x] Providers accept scoped context.
- [x] No provider scans the whole world unless explicitly allowed in test setup.
- [x] 10-entity scenario has negligible overhead.
- [x] 30-entity scenario stays under agreed tick budget.
- [x] 100-entity scenario produces a report even if not fully optimized yet.
- [x] Performance regression threshold is defined before tuning.
- [x] Scenario scorecard includes performance section.

## Important notes

Performance is a pillar, not a later cleanup. If Phase 1 slows the engine dramatically, stop and fix provider scoping before adding cognition.

---

# Phase 1 scenario suite

Write these before or alongside implementation.

## Scenario 1 — First growth route discovery

```text
Entity starts level 1 with weak weapon and 60 gold.
Shop has better weapon costing 100.
Blacksmith has craftable iron sword.
Iron source is known.
Entity must choose some valid improvement route or defer with reason.
```

Acceptance:

```text
valid route detected:
- gather_for_gold
- craft_upgrade
- ask_blacksmith
- buy_upgrade_after_gold
- defer_with_reason
```

Reject:

```text
buy without gold
craft without iron
hidden material knowledge
same failed action repeated
```

---

## Scenario 2 — Unknown material source

```text
Hunter blade requires moon_resin.
Blacksmith knows recipe requirement.
Guide does not know exact source, but suggests north_ruin.
```

Acceptance:

```text
moon_resin source remains unknown
research lead created
entity does not magically know moon_cave
```

---

## Scenario 3 — Depleted resource detour

```text
Entity needs iron_ore.
Known iron node is depleted.
Another possible source exists but is unknown.
Guide can suggest old_mine.
```

Acceptance:

```text
depletion detected
failed requirement/blocker created
entity seeks information or alternate route
```

---

## Scenario 4 — Service opportunity

```text
Entity has damaged weapon and some gold.
Blacksmith nearby can repair.
```

Acceptance:

```text
repair opportunity exposed
repair intent selected if relevant
gold consumed
durability restored
```

---

## Scenario 5 — Performance smoke test

```text
30 level-1 adventurers in hometown.
World pack loaded.
Run 500 ticks.
```

Acceptance:

```text
provider calls bounded
tick time below threshold
no global full scans in normal provider path
```

---

# Phase 1 deliverables

```text
docs/scenarios/phase1/*.yaml
src/data/registries/*
src/world/providers/requirements.py
src/world/providers/information.py
src/world/providers/resources.py
src/world/providers/services.py
src/engine/intent/action_intent.py
src/testing/scenario_runner.py
src/testing/route_family_classifier.py
reports/phase1_scorecards/*.json
reports/phase1_perf/*.json
```

---

# Phase 1 non-goals

Do **not** implement these yet:

```text
full self-awareness component
long-term memory component
full belief contradiction propagation
complex party behavior
full quest generation overhaul
full plugin system
global resolution graph
large content database
deep economy simulation
```

Phase 1 is foundation, not the full intelligent entity.

---

# Priority Plan

## What must change in mindset

Phase 1 is not “make entities smarter.”

Phase 1 is:

```text
make the world expose enough structured options so smarter entities can exist later
```

## Immediate actions

1. Write the five Phase 1 scenarios first.
2. Add the compact world content pack.
3. Add registries.
4. Add `RequirementEvaluator`.
5. Add `InformationProvider`.
6. Add resource/service opportunity providers.
7. Add route-family classifier.
8. Add performance gates.

## What to stop

Stop adding entity cognition before the world has enough structured options.

Stop writing one-off hardcoded action logic for each story branch.

Stop designing full generic architecture before Phase 1 proves value.

## Consequence if ignored

You will build advanced entity aspects that still choose between shallow options.

The result will look sophisticated internally but behave almost the same in simulation.

Phase 1 must prove this first:

```text
The world can expose meaningful, scoped, performant choices.
```

Only then should Phase 2 enrich entity self-awareness and decision-making.
