---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Phase 6 — Progression / Equipment / Reward Conversion

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
entity handles uncertain knowledge and source trust
```

Phase 6:

```text
entity converts reward, loot, gold, XP, materials, and equipment into meaningful long-term growth
```

Current tests already cover several lower-level mechanics:

```text
shop sell uses ResourceTransferIntent
blacksmith craft uses ResourceTransferIntent
combat reward flows through ResourceTransferIntent
RewardUpdate no longer accepts direct gold/items
unauthorized direct gold/item/XP/combat reward mutation is stripped
```

So Phase 6 should **not** re-test transaction legality. Those are already covered.

The missing layer is different:

```text
After receiving resources, does the entity understand what the reward means and convert it into growth?
```

---

# Phase 6 goal

Phase 6 answers:

```text
Given what the entity owns now,
what should it keep, sell, equip, store, craft, repair, train, or save for?
```

Not:

```text
Can shop sell iron_ore for 10 gold?
```

Already tested.

Not:

```text
Can blacksmith craft steel_sword if materials exist?
```

Already tested.

Phase 6 is about **meaningful conversion**:

```text
loot -> value understanding
gold -> spending plan
material -> craft route
XP/AP -> stat/skill growth
gear -> equip/repair/sell/store decision
reward -> next capability increase
```

---

# Phase 6 success definition

Phase 6 is successful when the engine can produce a trace like:

```yaml
reward_conversion_decision:
  entity_id: 1
  new_rewards:
    gold: 80
    items:
      - iron_ore
      - wolf_fang
    xp: 120

  interpreted_value:
    iron_ore: useful_for_iron_sword
    wolf_fang: useful_for_hunter_blade
    gold: insufficient_for_best_weapon_but_enough_for_repair
    xp: enough_to_level

  considered_conversions:
    - equip_better_weapon
    - craft_iron_sword
    - repair_current_weapon
    - sell_unused_loot
    - train_skill
    - save_gold

  selected_conversion:
    route: craft_iron_sword
    reason: "known recipe, known material source, improves weak weapon gap"

  future_effect: capability_gap.weapon reduced
```

---

# Task 1 — Add Phase 6 coverage audit

## Description

Avoid duplicating existing tests.

Existing test export already covers transaction/law-level reward and economy safety:

```text
ShopSystem uses ResourceTransferIntent.
BlacksmithSystem uses ResourceTransferIntent.
Combat reward uses ResourceTransferIntent.
RewardUpdate cannot directly carry gold/items.
Unauthorized worker mutations for gold/items/XP/combat rewards are stripped.
```

Phase 6 should test:

```text
meaning
choice
conversion plan
growth impact
future behavior
```

not:

```text
raw transaction legality
```

## Proposed document

```text
docs/test_coverage/phase6_progression_reward_conversion_coverage.md
```

## Checklist

- [x] Existing shop/blacksmith/reward/mutation-boundary tests are listed.
- [x] Phase 6 new test scope is explicitly limited to interpretation/conversion.
- [x] Tests do not duplicate `ResourceTransferIntent` law checks.
- [x] Tests do not duplicate quest reward delivery.
- [x] Tests do not duplicate combat kill reward.
- [x] Tests focus on post-reward decision-making.

---

# Task 2 — Define progression/reward conversion domain boundary

## Description

Create a domain layer:

```text
src/domains/progression/
```

This domain reads generic entity/world state and produces conversion decisions.

It should not replace:

```text
shop
blacksmith
quest_rewards
resource_transactions
evolution
```

Those already exist as engine phases. The current phase graph already has `quest_rewards`, `shop`, `resource_transactions`, and `evolution` phases. Phase 6 should plug into them, not replace them.

## Proposed service

```python
class ProgressionDecisionService:
    def evaluate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: ProgressionDecisionContext,
    ) -> ProgressionDecisionResult:
        ...
```

## Inputs

```text
inventory
equipment
identity / level / AP / XP
known recipes
knowledge model
capability estimate
self-awareness
need interpretation
active strategic project
available service opportunities
```

## Outputs

```text
conversion route
rejected alternatives
reason trace
proposed strategic update
proposed action intent
```

## Checklist

- [x] Domain does not directly mutate inventory/gold/XP.
- [x] Domain produces intent/project/update proposals only.
- [x] Existing authoritative transaction systems remain responsible for mutation.
- [x] No adventure-specific component required.
- [x] Can run for any role later, but Phase 6 scenarios focus on adventurer.
- [x] Feature-flagged initially.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_progression_boundary.py
```

Test cases:

```text
test_progression_service_does_not_mutate_state
test_progression_service_does_not_execute_shop_or_blacksmith
test_progression_service_returns_conversion_trace
test_progression_service_does_not_require_adventure_component
```

---

# Task 3 — Implement `PossessionUnderstandingComponent`

## Description

Inventory tells the engine:

```text
I have iron_ore.
I have wolf_fang.
I have rusted_sword.
```

Possession understanding tells the entity:

```text
iron_ore is useful for known recipe.
wolf_fang might be useful later.
rusted_sword is worse than equipped sword.
this item can be sold safely.
this item should be kept.
```

This is a core missing entity-life aspect.

## Proposed model

```python
@dataclass(frozen=True)
class PossessionMeaning:
    item_id: str
    known_uses: tuple[str, ...] = ()
    estimated_value: float = 0.0
    keep_priority: float = 0.0
    sell_priority: float = 0.0
    equip_priority: float = 0.0
    craft_priority: float = 0.0
    reason: str | None = None


@dataclass(frozen=True)
class PossessionUnderstandingComponent:
    meanings: Mapping[str, PossessionMeaning] = field(default_factory=dict)
    last_evaluated_tick: int = 0
```

## Checklist

- [x] Component defaults safely empty.
- [x] Component is deterministic and serializable.
- [x] Builder integration exists.
- [x] Canonical hashing inclusion/exclusion is documented.
- [x] No item is automatically “junk” without registry/knowledge basis.
- [x] Known recipe material increases keep priority.
- [x] Unknown rare item can have “unknown_use” reason.
- [x] Worse gear increases sell/store priority.
- [x] Better gear increases equip priority.

## TDD tests

```text
tests/unit/entity/test_phase6_possession_understanding_component.py
```

Test cases:

```text
test_default_possession_understanding_is_empty
test_known_recipe_material_gets_keep_priority
test_unknown_rare_item_is_not_auto_sold
test_worse_weapon_gets_sell_or_store_priority
test_better_weapon_gets_equip_priority
test_component_serializes_deterministically
```

---

# Task 4 — Implement `PossessionUnderstandingService`

## Description

This service evaluates inventory items against:

```text
item registry
recipe registry
active projects
knowledge model
equipment state
shop value
class fit
```

## Proposed service

```python
class PossessionUnderstandingService:
    def evaluate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: PossessionContext,
    ) -> PossessionUnderstandingComponent:
        ...
```

## Example logic

```text
iron_ore:
  known use: iron_sword recipe
  keep_priority: high

wolf_fang:
  known use: hunter_blade recipe
  keep_priority: medium/high

old_boot:
  no known use
  low value
  sell_priority: medium

iron_sword:
  better than current rusted_sword
  equip_priority: high
```

## Checklist

- [x] Uses item registry tags.
- [x] Uses known recipe requirements.
- [x] Uses active project needs.
- [x] Uses equipment comparison.
- [x] Uses class fit if available.
- [x] Uses knowledge uncertainty.
- [x] Does not scan all recipes if context can be scoped.
- [x] Does not mutate state.
- [x] Output includes reasons.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_possession_understanding_service.py
```

Test cases:

```text
test_material_for_active_recipe_has_high_keep_priority
test_material_for_unknown_recipe_has_lower_keep_priority
test_junk_item_has_sell_priority_when_gold_need_exists
test_better_class_fit_weapon_has_equip_priority
test_incompatible_gear_has_sell_or_store_priority
test_service_does_not_mutate_inventory
```

---

# Task 5 — Implement `GrowthGapEvaluator`

## Description

Phase 2 detects broad weaknesses:

```text
weak_weapon
low_health
low_stamina
low_confidence
```

Phase 6 needs growth-specific gaps:

```text
weapon_gap
armor_gap
skill_gap
gold_gap
material_gap
level_gap
repair_gap
supply_gap
```

## Proposed model

```python
@dataclass(frozen=True)
class GrowthGap:
    key: str
    severity: float
    confidence: float
    reason: str
    candidate_resolution_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class GrowthGapReport:
    gaps: tuple[GrowthGap, ...]
    dominant_gap: str | None = None
```

## Checklist

- [x] Weak weapon creates `weapon_gap`.
- [x] Damaged equipment creates `repair_gap`.
- [x] Known recipe missing material creates `material_gap`.
- [x] Insufficient gold creates `gold_gap`.
- [x] XP/AP available creates `level_or_attribute_gap`.
- [x] Skill need creates `skill_gap`.
- [x] Dominant gap is deterministic.
- [x] Gaps include candidate resolution tags.
- [x] Does not choose action directly.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py
```

Test cases:

```text
test_weak_weapon_creates_weapon_gap
test_damaged_weapon_creates_repair_gap
test_missing_recipe_material_creates_material_gap
test_insufficient_gold_creates_gold_gap
test_available_xp_creates_level_gap
test_dominant_gap_prioritizes_critical_repair_over_minor_upgrade
```

---

# Task 6 — Implement `RewardLedger`

## Description

Entities need to know what recently changed.

Not every inventory item should trigger conversion. Phase 6 needs a small ledger of recent/pending rewards:

```text
new loot
new gold
new XP/AP
new material
new gear
new recipe
```

This should be event-driven and capacity-bounded.

## Proposed model

```python
@dataclass(frozen=True)
class RewardEntry:
    tick: int
    kind: str
    subject: str
    quantity: int | float = 1
    source: str | None = None
    consumed_by_plan: bool = False


@dataclass(frozen=True)
class RewardLedgerComponent:
    entries: tuple[RewardEntry, ...] = ()
    last_processed_tick: int = 0
```

## Checklist

- [x] Ledger records new gold reward.
- [x] Ledger records new item reward.
- [x] Ledger records XP/AP gain.
- [x] Ledger records new recipe learned.
- [x] Ledger is bounded.
- [x] Entries can be marked consumed by conversion plan.
- [x] Ledger is event-driven, not reconstructed every tick.
- [x] Does not duplicate authoritative inventory.

## TDD tests

```text
tests/unit/entity/test_phase6_reward_ledger_component.py
```

Test cases:

```text
test_reward_ledger_records_item_gain
test_reward_ledger_records_gold_gain
test_reward_ledger_records_xp_gain
test_reward_ledger_capacity_is_bounded
test_reward_ledger_entry_can_be_marked_consumed
test_reward_ledger_does_not_replace_inventory_truth
```

---

# Task 7 — Implement `RewardInterpretationService`

## Description

Reward is not useful until interpreted.

Example:

```text
+80 gold
```

could mean:

```text
can repair weapon
still cannot buy iron_sword
can afford information
can afford inn rest
can save for future upgrade
```

Example:

```text
+wolf_fang
```

could mean:

```text
material for hunter_blade
sellable loot
quest material
unknown-use rare item
```

## Proposed service

```python
class RewardInterpretationService:
    def interpret(
        self,
        entity: EntityState,
        ledger: RewardLedgerComponent,
        possession: PossessionUnderstandingComponent,
        gaps: GrowthGapReport,
        state: AuthoritativeState,
    ) -> RewardInterpretationReport:
        ...
```

## Output

```python
@dataclass(frozen=True)
class RewardMeaning:
    entry_id: str
    meaning: str
    priority: float
    suggested_conversion_tags: tuple[str, ...]
    reason: str
```

## Checklist

- [x] Gold reward can resolve gold gap.
- [x] Item reward can resolve material gap.
- [x] Gear reward can resolve equipment gap.
- [x] XP reward can resolve level/stat gap.
- [x] Unknown item can produce information need.
- [x] Interpretation depends on active gaps.
- [x] Interpretation does not mutate inventory.
- [x] Output includes reasons.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_reward_interpretation_service.py
```

Test cases:

```text
test_gold_reward_resolves_repair_affordability
test_material_reward_resolves_known_recipe_gap
test_gear_reward_creates_equip_conversion
test_xp_reward_creates_level_or_attribute_conversion
test_unknown_rare_reward_creates_information_conversion
test_reward_interpretation_uses_current_growth_gap
```

---

# Task 8 — Implement `ConversionOptionGenerator`

## Description

Generate possible conversions:

```text
equip
repair
sell
store
craft
train
allocate AP
buy supply
buy upgrade
save
ask information
```

## Proposed model

```python
@dataclass(frozen=True)
class ConversionOption:
    kind: str
    score: float
    expected_growth_delta: float
    cost_gold: int = 0
    requirements: tuple[Requirement, ...] = ()
    blockers: tuple[str, ...] = ()
    reason: str | None = None
```

## Conversion kinds

```text
EQUIP_ITEM
REPAIR_GEAR
SELL_LOOT
STORE_ITEM
CRAFT_ITEM
TRAIN_SKILL
ALLOCATE_AP
BUY_SUPPLY
BUY_UPGRADE
SAVE_FOR_LATER
ASK_ITEM_USE
```

## Checklist

- [x] Better gear generates `EQUIP_ITEM`.
- [x] Damaged gear generates `REPAIR_GEAR`.
- [x] Sellable junk generates `SELL_LOOT`.
- [x] Useful later material generates `STORE_ITEM` or `KEEP`.
- [x] Known recipe + materials generates `CRAFT_ITEM`.
- [x] Available AP/XP generates `ALLOCATE_AP`.
- [x] Skill gap + trainer opportunity generates `TRAIN_SKILL`.
- [x] Unknown item use generates `ASK_ITEM_USE`.
- [x] Blocked options include reasons.
- [x] Result count is capped.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_conversion_option_generator.py
```

Test cases:

```text
test_better_weapon_generates_equip_option
test_damaged_weapon_generates_repair_option
test_junk_loot_generates_sell_option
test_recipe_material_generates_keep_or_craft_option
test_known_recipe_with_materials_generates_craft_option
test_unknown_rare_item_generates_ask_item_use_option
test_generator_caps_option_count
```

---

# Task 9 — Implement `ConversionDecisionService`

## Description

Choose one or more conversion options.

This should be explainable and not always globally optimal.

Inputs:

```text
growth gap severity
self needs
possession meaning
reward interpretation
service opportunities
personality traits
knowledge confidence
risk/cost
```

## Scoring idea

```text
conversion_score =
    growth_gap_severity
  + expected_growth_delta
  + need_urgency
  + personality_bias
  + knowledge_confidence
  - gold_cost_penalty
  - blocker_penalty
  - uncertainty_penalty
```

## Personality examples

| Trait        | Bias                                    |
| ------------ | --------------------------------------- |
| cautious     | repair/rest/supply before risky upgrade |
| greedy       | sell loot/save gold                     |
| industrious  | craft/keep materials                    |
| aggressive   | weapon/skill upgrade                    |
| curious      | ask about unknown item                  |
| conservative | keep rare materials                     |

## Checklist

- [x] Selects conversion option with trace.
- [x] Can choose `SAVE_FOR_LATER`.
- [x] Can choose non-optimal but explainable option via personality.
- [x] Does not use hidden recipe/material truth.
- [x] Does not mutate state.
- [x] Rejected options include reasons.
- [x] Deterministic under same input.
- [x] Can output multiple ordered conversions if safe.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_conversion_decision_service.py
```

Test cases:

```text
test_selects_equip_when_better_weapon_available
test_selects_repair_when_weapon_damaged_and_risk_high
test_selects_sell_when_junk_and_gold_gap
test_selects_craft_when_materials_and_recipe_ready
test_selects_save_when_best_upgrade_not_affordable
test_industrious_entity_prefers_craft_over_buy_when_both_valid
test_greedy_entity_prefers_sell_loot_when_growth_delta_equal
test_decision_does_not_use_hidden_truth
```

---

# Task 10 — Add conversion-to-intent bridge

## Description

A conversion decision should map to existing action systems.

Do not rewrite shop/blacksmith/evolution.

The bridge outputs `ActionIntent` or `StrategicUpdate`.

## Mapping

| Conversion       | Intent / update                        |
| ---------------- | -------------------------------------- |
| `EQUIP_ITEM`     | equipment update intent / equip action |
| `REPAIR_GEAR`    | blacksmith repair intent               |
| `SELL_LOOT`      | shop sell intent                       |
| `STORE_ITEM`     | storage deposit intent                 |
| `CRAFT_ITEM`     | blacksmith craft intent                |
| `TRAIN_SKILL`    | train action intent                    |
| `ALLOCATE_AP`    | allocate AP action intent              |
| `BUY_SUPPLY`     | shop buy intent                        |
| `BUY_UPGRADE`    | shop buy intent                        |
| `ASK_ITEM_USE`   | information query intent               |
| `SAVE_FOR_LATER` | strategic note / no action             |

Existing blacksmith crafting already checks blacksmith proximity, recipe, materials, gold, and emits a `ResourceTransferIntent`; Phase 6 should route into that path rather than duplicating it.

## Checklist

- [x] Bridge produces intent, not direct mutation.
- [x] Intent uses existing law/transaction path.
- [x] Blocked intent creates blocker/reason.
- [x] If service is far, produces move-to-service objective.
- [x] If conversion is `SAVE_FOR_LATER`, no invalid action emitted.
- [x] Trace links conversion decision to intent.
- [x] Existing transaction tests remain authoritative.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py
```

Test cases:

```text
test_craft_conversion_maps_to_blacksmith_craft_intent
test_repair_conversion_maps_to_repair_intent
test_sell_conversion_maps_to_shop_sell_intent
test_allocate_ap_conversion_maps_to_allocate_ap_intent
test_unknown_item_conversion_maps_to_information_query
test_save_for_later_emits_no_action
test_bridge_does_not_bypass_requirement_evaluator
```

---

# Task 11 — Add progression update phase

## Description

Add a bounded engine phase.

Trigger it only when relevant.

## Trigger conditions

```text
reward ledger changed
inventory changed
equipment changed
XP/AP changed
recipe learned
active growth gap changed
service opportunity appeared
project completed
```

## Skip conditions

```text
entity dead/inactive
no relevant reward/inventory/equipment change
conversion cooldown active
budget exhausted
feature flag disabled
```

## Proposed phase

```text
ProgressionConversionPhase:
  1. update possession understanding
  2. evaluate growth gaps
  3. update reward ledger from events
  4. interpret rewards
  5. generate conversion options
  6. choose conversion decision
  7. map to intent/project
  8. emit trace
```

## Checklist

- [x] Phase is feature-flagged initially.
- [x] Phase is event-driven/dirty-entity driven.
- [x] Does not run for every entity every tick.
- [x] Does not directly mutate inventory/gold/XP.
- [x] Uses existing transaction/evolution/action systems.
- [x] Updates are deterministic.
- [x] Performance counters exist.
- [x] Trace events are emitted only on meaningful change.

## TDD tests

```text
tests/integration/domains/progression/test_phase6_progression_conversion_phase.py
```

Test cases:

```text
test_phase_skips_entity_without_inventory_or_reward_change
test_phase_runs_after_item_reward
test_phase_runs_after_xp_reward
test_phase_respects_feature_flag
test_phase_outputs_intent_not_direct_mutation
test_phase_evaluation_count_is_bounded
```

---

# Task 12 — Add Phase 6 scenario tests

These are scenario-driven tests. They should prove conversion behavior, not transaction law.

## Scenario 6.1 — Reward gold becomes repair

```text
Entity:
- damaged weapon
- has repair need
- receives enough gold
- blacksmith known

Expected:
- reward interpretation says gold can resolve repair gap
- selected conversion is repair
- bridge emits repair intent or reach-blacksmith objective
```

Forbidden:

```text
directly mutates durability without repair law
spends gold without transaction path
```

---

## Scenario 6.2 — Loot material is kept, not sold

```text
Entity:
- knows iron_sword recipe
- needs iron_ore
- receives iron_ore
- also has low gold

Expected:
- iron_ore keep/craft priority > sell priority
- entity does not sell needed material just because gold is low
```

---

## Scenario 6.3 — Junk loot is sold for upgrade route

```text
Entity:
- needs gold for upgrade
- receives junk loot with no known use
- shop nearby

Expected:
- possession understanding marks item sellable
- conversion route selects sell_loot
- future gold gap reduced after existing shop law executes
```

Do not re-test sell price formula; existing tests already cover shop sell intent behavior.

---

## Scenario 6.4 — Better weapon is equipped

```text
Entity:
- currently has rusted_sword
- receives iron_sword
- class fits sword

Expected:
- equip priority high
- selected conversion is equip item
- weapon gap reduced after equip
```

---

## Scenario 6.5 — Unknown rare item triggers information route

```text
Entity:
- receives ancient_fragment
- item has rare/unknown tag
- guide/guild can maybe explain

Expected:
- item is not sold immediately
- unknown use recorded
- selected conversion is ask_item_use or store
```

---

## Scenario 6.6 — XP/AP becomes attribute/skill plan

```text
Entity:
- receives enough XP/AP
- has combat weakness
- has known useful attribute route

Expected:
- progression decision selects allocate AP or train skill
- trace explains growth gap
```

Important: earlier issue says training may write to the wrong field. If Phase 0 fixed that, this scenario can become integration coverage. If not fixed, this scenario should fail honestly.

---

## Scenario 6.7 — Personality changes conversion choice

```text
Same rewards, same world:

Entity A: industrious
Entity B: greedy
Entity C: cautious

Expected:
- industrious tends to keep/craft material
- greedy tends to sell safe junk/save gold
- cautious tends to repair/supply first

All choices must be valid.
```

## Test file

```text
tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py
```

---

# Task 13 — Add progression trace events

## Event types

```text
PossessionMeaningUpdated
GrowthGapDetected
RewardLedgerUpdated
RewardInterpreted
ConversionOptionGenerated
ConversionDecisionSelected
ConversionIntentEmitted
GrowthGapResolved
```

## Example

```yaml
event_type: ConversionDecisionSelected
entity_id: 1
selected: CRAFT_ITEM
subject: iron_sword
reason: "weapon_gap high, recipe known, materials available"
rejected:
  SELL_IRON_ORE: "needed for active recipe"
  BUY_IRON_SWORD: "not enough gold"
```

## Checklist

- [x] Events include reason.
- [x] Events include selected and rejected options.
- [x] Events include growth gap link.
- [x] Events are emitted only on meaningful change.
- [x] Events do not mutate authoritative state.
- [x] Event volume is bounded.
- [x] Existing observability parity tests still pass.

## TDD tests

```text
tests/unit/domains/progression/test_phase6_progression_events.py
```

Test cases:

```text
test_conversion_event_contains_selected_and_rejected_options
test_growth_gap_event_contains_reason
test_reward_interpreted_event_links_reward_to_gap
test_event_generation_does_not_change_state_hash
```

---

# Task 14 — Add Phase 6 performance gates

## Required metrics

```text
progression_evaluations_total
possession_items_evaluated_total
growth_gaps_detected_total
conversion_options_generated_total
conversion_decisions_total
avg_progression_phase_ms
p95_progression_phase_ms
max_reward_ledger_entries_per_entity
skipped_due_to_budget
```

## Performance tests

```text
10 entities, 500 ticks
100 entities, 500 ticks
500 entities, 200 ticks
100 entities with loot-heavy scenario
```

## Checklist

- [x] Possession evaluation capped by inventory size and item-change events.
- [x] Reward ledger bounded.
- [x] Conversion options capped.
- [x] No global recipe scan if active context is available.
- [x] Feature flag OFF matches old behavior.
- [x] Feature flag ON stays inside agreed overhead.
- [x] Determinism hash stable.
- [x] Performance report written.

## Test file

```text
tests/perf/test_phase6_progression_conversion_budget.py
```

---

# Phase 6 test files to add

```text
tests/unit/entity/test_phase6_possession_understanding_component.py
tests/unit/entity/test_phase6_reward_ledger_component.py

tests/unit/domains/progression/test_phase6_progression_boundary.py
tests/unit/domains/progression/test_phase6_possession_understanding_service.py
tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py
tests/unit/domains/progression/test_phase6_reward_interpretation_service.py
tests/unit/domains/progression/test_phase6_conversion_option_generator.py
tests/unit/domains/progression/test_phase6_conversion_decision_service.py
tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py
tests/unit/domains/progression/test_phase6_progression_events.py

tests/integration/domains/progression/test_phase6_progression_conversion_phase.py
tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py
tests/perf/test_phase6_progression_conversion_budget.py

docs/test_coverage/phase6_progression_reward_conversion_coverage.md
```

---

# Phase 6 non-goals

Do **not** implement these yet:

```text
full economy simulation
dynamic market demand
complex crafting specialization
full profession/job system
deep item appraisal/deception
auction/trade network
large-scale merchant behavior
party loot split
social gift economy
```

Also do **not** duplicate tests for:

```text
shop transaction legality
blacksmith transaction legality
combat reward transfer legality
quest reward transfer legality
unauthorized mutation stripping
resource transaction application
```

Those are already covered in the uploaded tests and existing source/test surface.

---

# Phase 6 completion criteria

Phase 6 is done when this is true:

```text
An entity does not merely receive rewards.

It understands what those rewards mean,
connects them to current weaknesses and goals,
chooses a valid conversion route,
uses existing lawful systems to execute it,
and future capability/behavior changes as a result.
```

Minimum proof:

```text
gold reward can become repair/supply/training decision
known recipe material is kept instead of sold
junk loot can be sold for a growth route
better equipment is equipped
unknown rare item triggers information/store behavior
XP/AP creates growth plan
personality changes conversion choice validly
progression overhead remains bounded
```

---

# Priority Plan

## What changes in Phase 6

Before Phase 6:

```text
entity can get rewards
```

After Phase 6:

```text
entity can convert rewards into life progress
```

## Implementation order

```text
1. Coverage audit
2. Progression domain boundary
3. PossessionUnderstandingComponent
4. PossessionUnderstandingService
5. GrowthGapEvaluator
6. RewardLedger
7. RewardInterpretationService
8. ConversionOptionGenerator
9. ConversionDecisionService
10. Conversion-to-intent bridge
11. ProgressionConversionPhase
12. Scenario tests
13. Trace events
14. Performance gates
```

## What to stop

Stop treating reward as the end of the loop.

Reward is only useful when it becomes:

```text
better capability
better equipment
better knowledge
better survival
better future route choice
```

## Consequence if ignored

The engine will produce entities that can fight, loot, buy, sell, craft, and gain XP, but they will not **progress intentionally**.

They will collect things but not understand them.

Phase 6 turns rewards into growth.
