# Phase 3 — Adventure Decision Layer

Phase 1 gives the world enough structured options.

Phase 2 gives the entity bottom-up interpretation:

```text
self-awareness
needs
capability estimates
knowledge / unknowns
```

Phase 3 connects those into **adventure-domain decision-making**, but it must **not** turn adventure into a required core entity model.

So Phase 3 is not:

```text
add AdventureReadinessComponent
```

It is:

```text
add an Adventure Decision Consumer
that reads general entity aspects + world opportunities
and produces route-family decisions / strategic projects
```

Existing tests already cover many lower-level areas: arena quest completion, regional combat effects, stop conditions, strategic detour/resumption, interruption resistance, observability, and certification/performance behavior. Phase 3 should not duplicate those; it should test the missing bridge from **interpreted entity state + world options** into **adventure route choice**.

---

# Phase 3 goal

Phase 3 answers:

```text
Given what the entity believes about itself,
what it needs,
what it knows,
what it can probably do,
and what the world exposes,

what adventure route should it commit to next?
```

Example:

```text
Entity:
- low-level warrior
- weak weapon
- 40 gold
- knows iron_sword recipe
- knows iron_ore source
- does not know moon_resin source
- wolf quest available but risky

Valid Phase 3 decisions:
- gather iron for craft route
- take easier quest first
- ask blacksmith/guide
- buy cheaper upgrade if possible
- defer wolf quest because risk too high
```

Not:

```text
always choose mathematically optimal path
```

---

# Phase 3 success definition

Phase 3 is successful when the engine can produce a trace like:

```yaml
adventure_decision:
  entity_id: 1
  dominant_need: equipment_improvement
  considered_routes:
    - buy_upgrade
    - craft_upgrade
    - take_easy_quest
    - ask_information
    - hunt_target
    - recover
  rejected_routes:
    buy_upgrade: not_enough_gold
    hunt_target: capability_too_low
  selected_route: craft_upgrade
  created_project: craft_iron_sword
  first_objective: acquire_iron_ore
```

This is the missing bridge:

```text
self-model + world options
-> route family choice
-> strategic project/objective
-> action intent later
```

---

# Task 1 — Add Adventure Decision domain boundary

## Description

Keep the core entity model generic.

Adventure logic should live in a domain layer:

```text
src/domains/adventure/
```

Not inside:

```text
EntityState
SelfAwarenessComponent
KnowledgeModelComponent
```

## Proposed solution

Create:

```python
class AdventureDecisionService:
    def evaluate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: AdventureDecisionContext,
    ) -> AdventureDecisionResult:
        ...
```

Core input:

```text
SelfAwarenessComponent
NeedInterpretationComponent
CapabilityEstimateComponent
KnowledgeModelComponent
World opportunities
Requirement results
Current strategic state
Personality / traits
```

Core output:

```text
AdventureDecisionResult
- selected route family
- rejected route families
- reason trace
- proposed strategic project
- proposed first objective
```

## Checklist

- [x] Adventure logic is isolated from core entity schema.
- [x] No `AdventureReadinessComponent` is added.
- [x] Service consumes generic self-model aspects.
- [x] Service consumes Phase 1 opportunities and requirements.
- [x] Service returns decision result without mutating state directly.
- [x] Output can be converted into `StrategicUpdate`.
- [x] Unit test verifies service can run with only mocked generic aspects.
- [x] Unit test verifies no adventure fields are required in `EntityState`.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py
```

Test cases:

```text
test_adventure_decision_does_not_require_adventure_component
test_adventure_decision_accepts_generic_self_model_inputs
test_adventure_decision_returns_trace_without_mutating_state
```

---

# Task 2 — Define route-family vocabulary

## Description

Route families are not actions.

They are high-level ways to solve adventure pressure.

Example:

```text
craft_upgrade
```

can later expand into:

```text
ask blacksmith
learn recipe
find material
harvest material
return to blacksmith
craft item
equip item
```

## Initial Phase 3 route families

```text
recover
buy_upgrade
craft_upgrade
train_skill
take_easy_quest
hunt_weak_enemy
gather_resource
sell_loot_for_gold
ask_information
scout_location
form_party
return_town
defer_with_reason
```

## Proposed route model

```python
@dataclass(frozen=True)
class AdventureRouteOption:
    family: str
    score: float
    confidence: float
    expected_benefit: float
    expected_risk: float
    requirements: tuple[Requirement, ...]
    blockers: tuple[str, ...] = ()
    source_opportunity_ids: tuple[str, ...] = ()
    reason: str | None = None
```

## Checklist

- [x] Route family enum/constants exist.
- [x] Every route family has a short semantic definition.
- [x] Every route family maps to possible project kind/objective kind.
- [x] Every route family has known blockers.
- [x] Every route family has test coverage for basic scoring.
- [x] Route family classifier from Phase 1 can recognize these families.
- [x] No route family directly executes action.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_route_families.py
```

Test cases:

```text
test_route_family_definitions_are_unique
test_route_family_has_project_mapping
test_route_family_has_required_trace_metadata
test_unknown_route_family_fails_fast
```

---

# Task 3 — Implement `AdventureRouteGenerator`

## Description

This service converts entity state + world opportunities into candidate route options.

It should not choose the final route yet.

It answers:

```text
What adventure-relevant routes are available or blocked?
```

## Proposed solution

```python
class AdventureRouteGenerator:
    def generate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        self_model: SelfModelView,
        opportunities: Sequence[Opportunity],
    ) -> tuple[AdventureRouteOption, ...]:
        ...
```

Route generation examples:

| Input condition                    | Generated route                                            |
| ---------------------------------- | ---------------------------------------------------------- |
| low HP / strong healing need       | `recover`                                                  |
| weak weapon + shop has item        | `buy_upgrade`                                              |
| weak weapon + known recipe         | `craft_upgrade`                                            |
| not enough gold                    | `gather_resource`, `take_easy_quest`, `sell_loot_for_gold` |
| unknown material source            | `ask_information`, `scout_location`                        |
| low confidence vs target           | `form_party`, `train_skill`, `defer_with_reason`           |
| active quest and enough capability | `hunt_weak_enemy` or `take_easy_quest`                     |

## Checklist

- [x] Generator consumes Phase 2 needs.
- [x] Generator consumes Phase 2 capability estimates.
- [x] Generator consumes Phase 2 knowledge/unknowns.
- [x] Generator consumes Phase 1 service/resource opportunities.
- [x] Generator creates blocked routes with reasons.
- [x] Generator creates at least one valid route or explicit defer route.
- [x] Generator does not perform full-world scan.
- [x] Generator does not mutate state.
- [x] Generator result count is capped.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_route_generator.py
```

Test cases:

```text
test_low_hp_generates_recover_route
test_weak_weapon_and_shop_item_generates_buy_upgrade_route
test_known_recipe_generates_craft_upgrade_route
test_unknown_material_generates_ask_information_route
test_not_enough_gold_generates_earn_gold_routes
test_no_valid_route_generates_defer_with_reason
test_generator_caps_result_count
```

---

# Task 4 — Implement route scoring with imperfect decision bias

## Description

Route selection must not always be globally optimal.

But it must be explainable.

The entity should choose based on:

```text
subjective estimate
personality / traits
confidence
urgency
risk tolerance
memory later
```

Phase 3 can start with simple deterministic bias.

## Proposed scoring inputs

```text
need urgency
expected benefit
expected risk
capability estimate
knowledge confidence
gold/material feasibility
distance / service availability
personality traits
current project interruption resistance
```

## Example scoring logic

```text
route_score =
    need_urgency
  + expected_benefit
  + personality_bias
  + knowledge_confidence
  - risk_penalty
  - blocker_penalty
  - uncertainty_penalty
```

## Personality examples

| Trait       | Effect                       |
| ----------- | ---------------------------- |
| bravery     | accepts higher risk          |
| greed       | values loot/gold routes more |
| caution     | prefers recover/prepare      |
| curiosity   | values scout/information     |
| industry    | values gather/craft          |
| sociability | values party/help routes     |

## Checklist

- [x] Route score uses subjective estimates, not hidden truth.
- [x] Personality can change ranking.
- [x] High urgency survival need can override growth route.
- [x] Unknown information lowers confidence.
- [x] Blocked route can remain visible but not selected unless desperation rule applies.
- [x] Same world + different traits can produce different selected route.
- [x] Same entity + same seed produces deterministic result.
- [x] Score trace includes all major modifiers.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_route_scoring.py
```

Test cases:

```text
test_healing_need_outranks_upgrade_when_hp_critical
test_greedy_entity_prefers_gold_route_when_risk_equal
test_cautious_entity_prefers_recover_before_hunt
test_curious_entity_prefers_information_when_unknown_exists
test_industrious_entity_prefers_craft_route_when_feasible
test_scoring_does_not_use_hidden_world_truth
test_route_scoring_is_deterministic
```

---

# Task 5 — Implement `AdventureDecisionService`

## Description

This service chooses one route from generated candidates.

It should output:

```text
selected route
rejected alternatives
decision reason
project proposal
trace
```

## Proposed result

```python
@dataclass(frozen=True)
class RejectedRoute:
    family: str
    reason: str
    score: float


@dataclass(frozen=True)
class AdventureDecisionResult:
    selected: AdventureRouteOption | None
    rejected: tuple[RejectedRoute, ...]
    proposed_project: ProjectState | None
    proposed_objective: ObjectiveState | None
    trace: Mapping[str, object]
```

## Decision postures

```text
COMMIT
PREPARE
SEEK_INFORMATION
RECOVER
DEFER
ESCALATE
```

Example:

```yaml
selected:
  family: craft_upgrade
  score: 0.71
rejected:
  buy_upgrade: not_enough_gold
  hunt_weak_enemy: capability_too_low
  ask_information: not_required_for_current_recipe
posture: PREPARE
```

## Checklist

- [x] Selects highest acceptable route after bias.
- [x] Can select `defer_with_reason`.
- [x] Produces proposed project/objective.
- [x] Rejected routes include reasons.
- [x] Decision does not mutate state directly.
- [x] Decision trace is serializable.
- [x] Decision can be consumed by strategic bridge task.
- [x] Deterministic under same seed/input.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_adventure_decision_service.py
```

Test cases:

```text
test_selects_recover_when_survival_need_critical
test_selects_craft_upgrade_when_recipe_and_material_source_known
test_selects_ask_information_when_required_source_unknown
test_selects_easy_quest_when_gold_needed_and_quest_feasible
test_returns_defer_when_all_routes_blocked
test_rejected_routes_preserve_reasons
test_decision_result_is_serializable
```

---

# Task 6 — Map route family to strategic project/objective

## Description

Existing strategic system already has projects, objectives, blockers, detours, interruption resistance, and project switching tests. Do not duplicate that.

Phase 3 only needs a bridge:

```text
AdventureDecisionResult
-> StrategicUpdate
```

## Proposed mapping

| Route family      | Project kind   | First objective                     |
| ----------------- | -------------- | ----------------------------------- |
| recover           | recovery       | reach_service / rest                |
| buy_upgrade       | preparation    | buy_item                            |
| craft_upgrade     | crafting       | acquire_material / reach_blacksmith |
| train_skill       | training       | reach_trainer                       |
| take_easy_quest   | quest          | accept_quest                        |
| hunt_weak_enemy   | quest/combat   | reach_target                        |
| gather_resource   | harvesting     | reach_resource                      |
| ask_information   | information    | reach_information_source            |
| scout_location    | exploration    | reach_location                      |
| form_party        | social         | recruit                             |
| return_town       | travel         | reach_town                          |
| defer_with_reason | none or paused | no active project                   |

## Checklist

- [x] Mapping is data-driven or table-driven.
- [x] Unknown route family fails fast.
- [x] Project IDs are deterministic.
- [x] Objective IDs are deterministic.
- [x] Blocked route can produce blocker state instead of project.
- [x] Existing strategic switching logic remains authoritative.
- [x] Does not bypass interruption resistance.
- [x] Does not duplicate existing detour/resumption tests.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_route_to_project_mapper.py
```

Test cases:

```text
test_craft_upgrade_maps_to_crafting_project
test_ask_information_maps_to_information_project
test_recover_maps_to_recovery_project
test_defer_route_does_not_create_active_project
test_project_ids_are_deterministic
test_mapper_does_not_override_existing_active_project_without_margin
```

Important: the current test suite already has strategic detour and project continuity/interruption-resistance coverage, so these tests should only verify the bridge output shape, not re-test the entire strategic engine.

---

# Task 7 — Add adventure decision integration phase

## Description

Add a controlled phase that runs adventure decision only when needed.

Do not run it every tick for every entity.

## Proposed phase

```text
AdventureDecisionPhase:
  input:
    dirty entities
    self-model changed
    no active project
    active project blocked
    major need changed
    new relevant opportunity appeared

  output:
    StrategicUpdate candidate
```

Cadence:

```text
event-driven + bounded strategic cadence
```

Run conditions:

```text
no current project
current project blocked
dominant need severity changed
new knowledge fact learned
new quest/opportunity observed
project completed/abandoned
```

## Checklist

- [x] Phase is disabled by default behind feature flag initially.
- [x] Phase only runs for eligible entities.
- [x] Phase respects strategic work budget.
- [x] Phase does not run for dead/inactive/stunned entities.
- [x] Phase produces `StrategicUpdate`, not direct state mutation.
- [x] Phase respects existing project switching/interruption logic.
- [x] Phase emits decision trace.
- [x] Performance counters include decision evaluations.

## TDD tests

Add:

```text
tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py
```

Test cases:

```text
test_phase_skips_entity_with_active_unblocked_project
test_phase_runs_when_no_current_project
test_phase_runs_when_current_project_blocked
test_phase_respects_dead_entity_skip
test_phase_respects_feature_flag
test_phase_produces_strategic_update_not_direct_mutation
test_phase_evaluation_count_is_bounded
```

---

# Task 8 — Add action-intent bridge for selected first objective

## Description

Phase 3 should not fully execute long adventure chains yet.

But once a project/objective exists, the system should be able to produce the first executable intent when possible.

Example:

```text
selected route: ask_information
project: information
objective: reach_guide / ask_guide_about_moon_resin
intent: MOVE_TO guide or ASK_INFORMATION if already near guide
```

## Proposed bridge

```python
class ObjectiveIntentResolver:
    def resolve(
        self,
        entity: EntityState,
        objective: ObjectiveState,
        state: AuthoritativeState,
    ) -> ActionIntent | None:
        ...
```

Initial objective kinds:

```text
reach_service
ask_information
buy_item
request_craft
reach_resource
harvest_resource
accept_quest
rest
return_town
```

## Checklist

- [x] Resolves first objective only.
- [x] Does not execute entire route.
- [x] Uses existing `ActionIntent` adapter from Phase 1.
- [x] If target too far, returns `MOVE_TO`.
- [x] If requirement fails, returns blocker.
- [x] Does not bypass legality checks.
- [x] Does not duplicate movement/combat/action tests.
- [x] Emits objective-to-intent trace.

## TDD tests

Add:

```text
tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py
```

Test cases:

```text
test_ask_information_objective_resolves_to_move_when_far
test_ask_information_objective_resolves_to_ask_when_near
test_buy_item_objective_fails_with_not_enough_gold_blocker
test_reach_resource_objective_resolves_to_move
test_harvest_resource_objective_resolves_when_near
test_unknown_objective_returns_no_intent_with_reason
```

---

# Task 9 — Add Phase 3 scenario tests

## Description

Now test complete decision routes, but still not long campaign.

These are scenario-driven TDD tests.

They assert valid route family and trace, not exact tick-by-tick path.

---

## Scenario 3.1 — Weak weapon, not enough gold

```text
Entity:
- level 1
- weak weapon
- 40 gold

World:
- shop sells iron_sword for 100
- easy quest gives 50 gold
- herbs can be gathered and sold
```

Expected valid routes:

```text
take_easy_quest
gather_resource
sell_loot_for_gold
defer_with_reason
```

Forbidden:

```text
buy_upgrade without gold
craft without materials
hidden resource knowledge
```

---

## Scenario 3.2 — Known recipe, known material source

```text
Entity:
- weak weapon
- knows iron_sword recipe
- knows iron_ore source
- has enough gold for crafting fee

World:
- blacksmith exists
- old_mine has iron_ore
```

Expected:

```text
selected route family should be craft_upgrade or gather_resource_for_craft
project kind should be crafting or harvesting-prep
trace should explain material requirement
```

---

## Scenario 3.3 — Unknown rare material

```text
Entity:
- wants hunter_blade
- knows recipe requires moon_resin
- does not know moon_resin source

World:
- guide can suggest north_ruin clue
- exact moon_cave source is hidden
```

Expected:

```text
selected route should be ask_information or scout_location
entity must not know moon_cave directly
trace includes unknown material source
```

---

## Scenario 3.4 — Low HP overrides growth

````text
Entity:
- low HP
- weak weapon
- known upgrade route

Expected:

```text
selected route should be recover
growth route should be rejected or deferred
trace explains survival need outranks equipment improvement
````

---

## Scenario 3.5 — Different traits produce different valid routes

```text
Same world, three entities:
- brave
- cautious
- industrious

Expected:

brave:
  may choose easy hunt/quest

cautious:
  may choose recover/prepare/information

industrious:
  may choose gather/craft route
```

Important:

```text
All choices must be valid.
They do not need to be identical.
They do not need to be globally optimal.
```

---

## Checklist

- [ ] Scenarios use Phase 1 content pack.
- [ ] Scenarios use Phase 2 self-model.
- [ ] Scenarios assert route family, not exact path.
- [ ] Scenarios include negative assertions.
- [ ] Scenarios include decision trace assertion.
- [ ] Scenarios avoid duplicating arena quest/combat tests.
- [ ] Scenarios are deterministic under fixed seed.
- [ ] Scenario runner records selected/rejected routes.

## Test file

```text
tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py
```

---

# Task 10 — Add Phase 3 performance gates

## Description

Adventure decision can become expensive if it generates too many routes or runs too often.

Phase 3 must remain bounded.

## Metrics

```text
adventure_decision_evaluations_total
route_options_generated_total
route_options_scored_total
avg_decision_ms
p95_decision_ms
skipped_due_to_active_project
skipped_due_to_budget
```

## Performance tests

```text
10 entities, 500 ticks
100 entities, 500 ticks
500 entities, 200 ticks
```

## Checklist

- [x] Decision phase is scoped to dirty/eligible entities.
- [x] Max route options per entity is capped.
- [x] No full-world scan.
- [x] Decision result trace volume is bounded.
- [x] 100-entity test stays under agreed budget.
- [x] Determinism hash remains stable.
- [x] Feature flag can disable phase with no behavior change.
- [x] Performance report is written.

## Test file

```text
tests/perf/test_phase3_adventure_decision_budget.py
```

---

# Phase 3 test files to add

```text
tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py
tests/unit/domains/adventure/test_phase3_route_families.py
tests/unit/domains/adventure/test_phase3_route_generator.py
tests/unit/domains/adventure/test_phase3_route_scoring.py
tests/unit/domains/adventure/test_phase3_adventure_decision_service.py
tests/unit/domains/adventure/test_phase3_route_to_project_mapper.py
tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py
tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py
tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py
tests/perf/test_phase3_adventure_decision_budget.py
```

---

# Phase 3 non-goals

Do **not** implement these yet:

```text
combat engagement cognition
long-term combat learning
deep rumor contradiction
party coordination
full quest generation rewrite
multi-day journey/campaign lifecycle
reward conversion planning
world emergence
```

Also do not duplicate existing tests for:

```text
quest reward completion
combat arena progression
detour completion/resumption
project switching margin
API observability
long-run stability
```

Those already exist in the uploaded test suite.

---

# Phase 3 completion criteria

Phase 3 is done when this is true:

```text
Given a generic self-model and scoped world opportunities,
an entity can choose a valid adventure route family,
explain why,
reject alternatives with reasons,
and create a strategic project/objective
without hardcoding the story path.
```

Minimum proof:

```text
weak + poor entity does not buy impossible item
unknown source creates information route
low HP chooses recovery before growth
known recipe creates craft route
different traits create different valid route choices
decision phase stays bounded under 100+ entities
```

---

# Priority Plan

## What changes in Phase 3

Phase 1:

```text
world exposes options
```

Phase 2:

```text
entity interprets itself
```

Phase 3:

```text
entity chooses route family
```

## Immediate order

```text
1. Route family vocabulary
2. AdventureRouteGenerator
3. Route scoring with personality bias
4. AdventureDecisionService
5. Route-to-project mapper
6. Objective-to-intent resolver
7. Decision integration phase
8. Scenario tests
9. Performance gates
```

## What to stop

Stop adding direct one-off behavior like:

```text
if weak weapon, go blacksmith
```

Use:

```text
weak weapon -> equipment_improvement need
equipment_improvement need -> route options
route options -> scored choice
choice -> project/objective
```

## Consequence if ignored

You will have:

```text
rich world
rich self-model
but brittle hardcoded behavior
```

Phase 3 prevents that by making route choice explainable, testable, and extensible.
