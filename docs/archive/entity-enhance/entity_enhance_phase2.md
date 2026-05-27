# Phase 2 — Bottom-Up Entity Self Model

Phase 1 makes the world expose richer options. Phase 2 makes the entity able to **interpret itself and its known world** without hardcoding “adventure readiness.”

Do **not** implement `AdventureReadinessComponent`.

The correct Phase 2 target is:

```text id="mna6sa"
Entity understands:
- what condition it is in
- what it needs
- what it believes it can do
- what it knows / does not know
```

Then later phases can derive:

```text id="vehq1r"
AdventureReadinessView
CombatReadinessView
QuestReadinessView
TravelReadinessView
CraftingReadinessView
```

as computed views, not core entity state.

The uploaded test export already has broad coverage around cognition history APIs, arena quest progression, regional combat effects, arena scaling, stop conditions, certification stability, scenario repository behavior, social contracts, strategic detours, and performance gates. Phase 2 should avoid duplicating those and focus only on the missing bottom-up entity model.

---

# Phase 2 success definition

Phase 2 is successful when the engine can produce a trace like this:

```text id="3tdzf4"
raw entity state
-> self-awareness
-> interpreted needs
-> capability estimates
-> knowledge / unknowns
-> cognition signals
```

without yet requiring full adventure behavior.

Example:

```text id="lcwxo4"
Entity has low HP, weak weapon, 40 gold, unknown moon_resin source.

Phase 2 output:
- perceived weakness: low_health, weak_weapon
- active needs: healing, equipment_improvement, information
- capability estimate: can fight rat, risky against wolf, cannot craft hunter_blade yet
- knowledge model: knows iron source, does not know moon_resin source
```

That is the foundation for later route selection.

---

# Task 1 — Add Phase 2 coverage audit and test map

## Description

Before adding tests, explicitly map what existing tests already cover so Phase 2 does not duplicate them.

Existing tests already cover many areas:

```text id="mbyzv8"
combat arena behavior
quest progression
regional control
social contract lifecycle
strategic detours
observability APIs
performance/stability
scenario repository
transaction atomicity
```

So Phase 2 should not re-test:

```text id="rj6czj"
combat damage formula
quest reward resolution
shop/blacksmith transaction law
API response shapes
regional conquest math
arena stop conditions
```

## Proposed solution

Create a small markdown or JSON test map:

```text id="q6gj6s"
docs/test_coverage/phase2_self_model_coverage.md
```

Example:

```markdown id="sa728d"
# Phase 2 Test Coverage Map

## Existing coverage reused

- arena quest completion: tests/arena/test_arena_quests.py
- regional combat/conquest: tests/arena/test_arena_regional_control.py
- strategic detours: tests/unit/strategic/\*
- social contracts: tests/unit/social/\*
- performance envelopes: tests/perf/_ and tests/certification/_

## New Phase 2 coverage

- SelfAwarenessComponent schema and canonical serialization
- NeedInterpretationService
- CapabilityEstimateService
- KnowledgeModelComponent
- Knowledge assimilation from Phase 1 InformationProvider
- Self-model trace generation
```

## Checklist

- [ ] Existing test areas are documented.
- [ ] Phase 2 tests are placed under new files, not mixed into old arena/combat tests.
- [ ] No Phase 2 test asserts raw combat damage formula.
- [ ] No Phase 2 test duplicates quest reward resolution.
- [ ] No Phase 2 test duplicates shop/blacksmith transfer law.
- [ ] New tests focus on interpretation, estimation, and knowledge state.
- [ ] Test names include `phase2` or `self_model` for searchability.

## Important notes

This is a guardrail against test bloat. You already have many tests. Adding duplicated tests will slow development and hide the real gap.

---

# Task 2 — Implement new bottom-up entity components

## Description

Add only core bottom-up components.

Phase 2 components:

```text id="jtgev6"
SelfAwarenessComponent
NeedInterpretationComponent
CapabilityEstimateComponent
KnowledgeModelComponent
```

Do **not** add:

```text id="6s2f7r"
AdventureReadinessComponent
QuestReadinessComponent
CombatReadinessComponent
```

Those are derived views later.

## Proposed solution

Add dataclasses to the entity state model or a dedicated self-model module.

Example shape:

```python id="7amx26"
@dataclass(frozen=True)
class SelfAwarenessComponent:
    perceived_condition: Mapping[str, float] = field(default_factory=dict)
    perceived_weaknesses: tuple[str, ...] = ()
    perceived_strengths: tuple[str, ...] = ()
    confidence_level: float = 0.5
    stress_level: float = 0.0
    uncertainty_level: float = 0.0
    last_self_check_tick: int = 0
```

```python id="295mtt"
@dataclass(frozen=True)
class NeedInterpretationComponent:
    active_needs: Mapping[str, InterpretedNeed] = field(default_factory=dict)
    dominant_need: str | None = None
    last_interpreted_tick: int = 0
```

```python id="9c5sd5"
@dataclass(frozen=True)
class CapabilityEstimateComponent:
    estimates: Mapping[str, CapabilityEstimate] = field(default_factory=dict)
```

```python id="04l477"
@dataclass(frozen=True)
class KnowledgeModelComponent:
    facts: Mapping[str, KnowledgeFact] = field(default_factory=dict)
    unknowns: Mapping[str, UnknownFact] = field(default_factory=dict)
```

## Checklist

- [ ] Components are immutable/frozen if the rest of state follows immutable update style.
- [ ] Components have safe default empty values.
- [ ] Components are included in `EntityState` or attached through a clearly named self-model structure.
- [ ] Components are supported by builder methods.
- [ ] Components serialize deterministically.
- [ ] Components are included or intentionally excluded from canonical hashing with documentation.
- [ ] Component equality is deterministic.
- [ ] No component directly references “adventure.”
- [ ] No component directly mutates action systems.
- [ ] Unit tests verify default construction.
- [ ] Unit tests verify canonical serialization stability.
- [ ] Unit tests verify builder integration.

## Important notes

This is pure model work. No behavior yet. Keep it small.

---

# Task 3 — Implement `SelfAssessmentService`

## Description

The entity already has raw state: HP, stamina, equipment, inventory, biological status, level, class, wounds, and attributes.

`SelfAssessmentService` converts raw state into subjective self-awareness.

It answers:

```text id="movlyc"
What does the entity believe about itself right now?
```

## Proposed solution

Create a stateless service:

```python id="oilj85"
class SelfAssessmentService:
    def assess(self, entity: EntityState, state: AuthoritativeState) -> SelfAwarenessComponent:
        ...
```

Inputs:

```text id="2si55z"
combat
stamina
biological
inventory
equipment
identity/class
attributes
wounds/scars
recent memory later
```

Outputs:

```text id="6kctz5"
perceived_condition.health
perceived_condition.stamina
perceived_condition.equipment_quality
perceived_condition.carrying_load
perceived_weaknesses
perceived_strengths
confidence_level
stress_level
uncertainty_level
```

Example:

```text id="jggfwr"
HP 20/100 + weak weapon + full inventory
-> weaknesses:
   low_health
   weak_weapon
   inventory_full
-> stress_level high
-> confidence low
```

## Checklist

- [ ] Low HP creates `low_health` weakness.
- [ ] Low stamina creates `low_stamina` weakness.
- [ ] Full inventory creates `inventory_pressure`.
- [ ] Broken/damaged gear creates `gear_damaged`.
- [ ] Weak weapon relative to level/class creates `weak_weapon`.
- [ ] Strong current condition increases confidence.
- [ ] Stress increases when multiple severe weaknesses exist.
- [ ] Output is deterministic for same input.
- [ ] Service does not mutate state.
- [ ] Unit tests cover HP, stamina, inventory, gear, and mixed conditions.
- [ ] Integration test verifies self-awareness appears in entity inspection/debug trace.

## Important notes

Do not make it perfectly intelligent yet. Phase 2 can use simple deterministic rules. Imperfect self-awareness can be introduced later through personality, wisdom, stress, and memory modifiers.

---

# Task 4 — Implement `NeedInterpretationService`

## Description

Raw hunger, fatigue, low HP, damaged gear, low gold, full inventory, and unknown information should become interpreted needs.

It answers:

```text id="ec168g"
What pressure is currently pulling this entity?
```

## Proposed solution

Create:

```python id="p66is5"
class NeedInterpretationService:
    def interpret(
        self,
        entity: EntityState,
        self_awareness: SelfAwarenessComponent,
        state: AuthoritativeState,
    ) -> NeedInterpretationComponent:
        ...
```

Need examples:

```text id="au1dbh"
healing
rest
food
safety
inventory_space
equipment_repair
equipment_improvement
gold
information
```

Need record:

```python id="13abtx"
@dataclass(frozen=True)
class InterpretedNeed:
    key: str
    urgency: float
    confidence: float
    reason: str
```

## Checklist

- [ ] Low HP produces `healing` need.
- [ ] Hunger produces `food` need.
- [ ] Sleep debt/fatigue produces `rest` need.
- [ ] Damaged gear produces `equipment_repair` need.
- [ ] Weak gear produces `equipment_improvement` need.
- [ ] Full inventory produces `inventory_space` need.
- [ ] Unknown required fact produces `information` need.
- [ ] Dominant need is the highest-urgency need.
- [ ] Critical survival need outranks low-priority growth need.
- [ ] Output is deterministic.
- [ ] Unit tests cover individual needs.
- [ ] Unit tests cover priority competition:
  - low HP vs upgrade desire
  - hunger vs quest desire
  - full inventory vs harvesting

- [ ] Scenario test verifies severe need can be traced before later strategic interruption.

## Important notes

Do not directly choose actions here. This service only produces interpreted needs.

---

# Task 5 — Implement `CapabilityEstimateService`

## Description

The entity needs subjective estimates of what it can do:

```text id="1v72z9"
Can I fight this enemy?
Can I survive this region?
Can I gather this resource?
Can I craft this recipe?
Can I complete this quest?
```

This is not raw stat calculation. It is a belief-like estimate with confidence.

## Proposed solution

Create:

```python id="m9ozky"
class CapabilityEstimateService:
    def estimate(
        self,
        entity: EntityState,
        state: AuthoritativeState,
        context: CapabilityContext,
    ) -> CapabilityEstimateComponent:
        ...
```

Initial Phase 2 estimate keys:

```text id="cq4pvx"
combat.enemy_type.rat
combat.enemy_type.wolf
travel.region.near_forest
travel.region.north_ruin
gather.resource.iron_ore
craft.recipe.iron_sword
```

Estimate shape:

```python id="rnldlf"
@dataclass(frozen=True)
class CapabilityEstimate:
    capability_key: str
    estimate: float
    confidence: float
    source: str
    last_updated_tick: int
```

## Checklist

- [ ] Estimate supports combat enemy type.
- [ ] Estimate supports region travel risk.
- [ ] Estimate supports resource gathering.
- [ ] Estimate supports recipe/crafting feasibility.
- [ ] Low HP/stamina lowers combat/travel capability.
- [ ] Better weapon/armor increases combat estimate.
- [ ] Missing tool/material/recipe lowers craft/gather estimate.
- [ ] Unknown data lowers confidence rather than producing false certainty.
- [ ] Unit tests cover:
  - weak entity vs rat
  - weak entity vs wolf
  - wounded entity vs same enemy
  - equipped entity vs same enemy
  - unknown region risk
  - known safe region

- [ ] Integration test verifies capability estimates appear in scenario trace.
- [ ] Performance test verifies estimates are scoped, not computed for every enemy/resource in the world.

## Important notes

Do not make it perfect truth. In Phase 2, uncertainty can be simple. Later phases can add perception, memory, and personality bias.

---

# Task 6 — Implement `KnowledgeModelService`

## Description

Entity needs personal knowledge, unknowns, and learned facts.

This should consume Phase 1 `InformationProvider` responses but must not expose hidden world truth directly.

It answers:

```text id="xbrxun"
What does this entity know well enough to act on?
What does it know that it does not know?
```

## Proposed solution

Create:

```python id="i0yvbr"
class KnowledgeModelService:
    def assimilate_information(
        self,
        entity: EntityState,
        response: InformationResponse,
        tick: int,
    ) -> KnowledgeModelComponent:
        ...
```

Fact examples:

```text id="hay4fl"
service.blacksmith.location = hometown
recipe.iron_sword.requires = iron_ore + wood + gold
resource.iron_ore.source = old_mine
region.north_ruin.possible_clue = moon_resin
```

Unknown examples:

```text id="7pbqps"
unknown.material.moon_resin.source
unknown.region.north_ruin.danger
unknown.enemy.goblin_chief.weakness
```

## Checklist

- [ ] Known provider facts become `KnowledgeFact`.
- [ ] Partial provider answers create both facts/leads and unknowns.
- [ ] Unknown provider answer creates `UnknownFact`, not fake knowledge.
- [ ] Certainty is preserved from provider response.
- [ ] Source ID is recorded.
- [ ] Stable facts can persist.
- [ ] Low-confidence rumors are not treated as confirmed facts.
- [ ] Unit test: blacksmith recipe response creates recipe requirement fact.
- [ ] Unit test: guide partial answer keeps `moon_resin.source` unknown.
- [ ] Unit test: guild danger hint creates uncertain region fact.
- [ ] Negative test: entity cannot learn hidden exact source if provider did not return it.
- [ ] Integration test: unknown material source produces information need.

## Important notes

Do not duplicate existing `LeadState` blindly. A `LeadState` can remain strategic/uncertain route information. The knowledge model should store entity-owned facts and unknowns.

---

# Task 7 — Add self-model update phase

## Description

New components must be updated in a controlled phase, not randomly from every action.

You need a deterministic self-model update step.

## Proposed solution

Add a phase or service orchestration:

```text id="zowjda"
SelfModelUpdatePhase:
  1. SelfAssessmentService
  2. NeedInterpretationService
  3. CapabilityEstimateService
  4. KnowledgeModelService only when information events exist
```

Cadence:

```text id="31gqpe"
SelfAssessment: short cadence or when dirty
NeedInterpretation: short cadence or when dirty
CapabilityEstimate: scoped/contextual
KnowledgeModel: event-driven
```

Dirty triggers:

```text id="ll0gx2"
HP changed
stamina changed
inventory changed
equipment changed
biological state changed
information response received
region entered
combat outcome observed
```

## Checklist

- [ ] Self-model update phase is deterministic.
- [ ] Phase can run only for dirty entities.
- [ ] No full-world scan.
- [ ] Knowledge update is event-driven.
- [ ] Capability estimates are scoped to current context.
- [ ] Canonical hash is stable across repeated same input.
- [ ] Observability mode does not alter authoritative state.
- [ ] Unit test verifies dirty entity gets updated.
- [ ] Unit test verifies clean entity is skipped.
- [ ] Integration test verifies HP change updates self-awareness next phase.
- [ ] Performance test verifies 100 entities self-model update stays within budget.

## Important notes

Existing tests already care about determinism and observability parity, so do not break those. The uploaded tests include explicit certification and observability parity style checks; Phase 2 must respect that pattern.

---

# Task 8 — Add Phase 2 trace events

## Description

If self-model exists but cannot be inspected, it will be impossible to debug.

Do not only store fields. Emit trace events when important self-model changes occur.

## Proposed solution

Add trace event types:

```text id="72t2wv"
SelfAwarenessUpdated
NeedInterpreted
CapabilityEstimateUpdated
KnowledgeFactLearned
KnowledgeUnknownRecorded
```

Example trace:

```yaml id="xwy5ps"
event_type: NeedInterpreted
entity_id: 1
tick: 30
dominant_need: healing
needs:
  healing: 0.9
  equipment_improvement: 0.4
reason: low_health
```

## Checklist

- [ ] Events are emitted only on meaningful change, not every tick spam.
- [ ] Events are deterministic.
- [ ] Events do not mutate authoritative state when observability is off.
- [ ] Trace includes reason fields.
- [ ] Trace links to source facts/events where available.
- [ ] Unit test verifies event payload shape.
- [ ] Integration test verifies scenario scorecard can read self-model trace.
- [ ] Performance test verifies event volume is bounded.

## Important notes

You already have extensive observability/API tests. Do not duplicate API tests. Test the event payload and scenario scorecard consumption only.

---

# Task 9 — Add Phase 2 scenario tests

## Description

Phase 2 needs scenario-driven tests, not only unit tests.

But unlike Phase 1, these scenarios should not require the entity to complete route selection. They verify interpretation.

## Proposed scenarios

### Scenario 2.1 — Wounded weak adventurer self-model

```text id="eohj0q"
Entity starts with:
- low HP
- weak weapon
- some gold
- known blacksmith
```

Expected:

```text id="cnjs9p"
self-awareness includes low_health and weak_weapon
dominant need is healing or safety
equipment_improvement exists but lower priority than healing
```

---

### Scenario 2.2 — Unknown material creates knowledge gap

```text id="zr1y0c"
Entity learns hunter_blade recipe requiring moon_resin.
Entity does not know moon_resin source.
```

Expected:

```text id="d064xa"
KnowledgeModel contains recipe requirement fact.
KnowledgeModel contains unknown material.moon_resin.source.
NeedInterpretation includes information need.
```

---

### Scenario 2.3 — Capability estimate changes with equipment

```text id="51s3pw"
Same entity before and after equipping iron_sword.
Enemy type = wolf.
```

Expected:

```text id="l3iw6h"
combat.enemy_type.wolf estimate improves after equipment upgrade.
confidence remains same unless new combat memory exists.
```

---

### Scenario 2.4 — Low condition lowers capability

```text id="w4fy6s"
Same entity at full HP and then at 20% HP.
Enemy type = rat.
```

Expected:

```text id="1u1bmk"
combat estimate decreases when wounded.
NeedInterpretation increases healing need.
```

---

### Scenario 2.5 — Information provider does not grant hidden truth

```text id="m6u2n9"
Guide knows only that north_ruin may contain clue.
Exact moon_cave source exists in world truth.
```

Expected:

```text id="0gmjfb"
Entity records north_ruin lead or partial fact.
Entity does not know moon_cave exact source.
```

## Checklist

- [ ] Scenarios are deterministic.
- [ ] Scenarios use Phase 1 content pack.
- [ ] Scenarios assert self-model state, not exact action story.
- [ ] Scenarios do not duplicate existing arena combat/quest tests.
- [ ] Scenarios produce scorecards.
- [ ] Each scenario has at least one negative assertion.
- [ ] Scenario tests can fail before implementation.

## Important notes

These are **interpretation scenarios**, not full adventure campaigns yet.

---

# Task 10 — Add Phase 2 performance gates

## Description

Self-model updates can become expensive if computed for every entity every tick.

Performance must be included from the start.

## Proposed solution

Add benchmark:

```text id="6qrck2"
test_phase2_self_model_update_budget
```

Cases:

```text id="h2q45l"
10 entities, 100 ticks
100 entities, 100 ticks
500 entities, 100 ticks
```

Metrics:

```text id="7kxfud"
self_model_updates_total
dirty_entities_processed
capability_estimates_computed
knowledge_updates_total
avg_self_model_ms
p95_self_model_ms
```

## Checklist

- [ ] Clean entities are skipped.
- [ ] Dirty update count is bounded.
- [ ] Capability estimate count is scoped.
- [ ] No full-world scan.
- [ ] Memory growth is bounded.
- [ ] Determinism hash remains stable.
- [ ] Performance report is written.
- [ ] Regression threshold is defined.
- [ ] Test does not duplicate existing long-run certification tests; it only targets self-model overhead.

## Important notes

Existing tests already cover broad long-run stability and performance. Phase 2 performance tests should be narrow and cheap.

---

# Phase 2 test files to add

```text id="d4998d"
tests/unit/entity/test_phase2_self_model_components.py
tests/unit/cognition/test_phase2_self_assessment_service.py
tests/unit/cognition/test_phase2_need_interpretation_service.py
tests/unit/cognition/test_phase2_capability_estimate_service.py
tests/unit/cognition/test_phase2_knowledge_model_service.py
tests/integration/scenarios/test_phase2_self_model_scenarios.py
tests/perf/test_phase2_self_model_budget.py
docs/test_coverage/phase2_self_model_coverage.md
```

---

# Phase 2 non-goals

Do **not** implement these in Phase 2:

```text id="2c8h9g"
combat engagement cognition
full adventure route selection
party formation logic
new quest acceptance behavior
long-term combat learning
full rumor contradiction propagation
reward conversion planning
region/world emergence
AdventureReadinessComponent
```

Those belong to later phases.

Phase 2 only builds the bottom-up self model.

---

# Phase 2 dependency on Phase 1

Phase 2 assumes Phase 1 already provides:

```text id="fssvnx"
content pack
registries
RequirementEvaluator
InformationProvider
ResourceOpportunityProvider
ServiceOpportunityProvider
ActionIntent adapter
scenario runner
route-family classifier
performance counters
```

Without Phase 1, Phase 2 still works as a model layer, but it will not show meaningful behavior.

---

# Phase 2 completion criteria

Phase 2 is done when this is true:

```text id="gy2abc"
Given raw state and scoped world facts,
the entity can produce deterministic, inspectable, performance-bounded
self-awareness, needs, capability estimates, and personal knowledge/unknowns.
```

Minimum proof:

```text id="1szn4m"
wounded entity knows it is vulnerable
hungry entity has food need
weak-weapon entity has equipment weakness
unknown material produces knowledge gap
better equipment improves capability estimate
provider partial answer does not leak hidden truth
self-model update stays inside performance budget
```

---

# Priority Plan

## Mindset / assumption to change

Phase 2 is not about making entities choose better actions yet.

It is about making entities have the **internal interpretation layer** required for future choices.

## Immediate actions

1. Write Phase 2 coverage map.
2. Add component schemas.
3. Write failing unit tests for component serialization and builder integration.
4. Write failing service tests for self-assessment, need interpretation, capability estimate, and knowledge assimilation.
5. Write the five Phase 2 scenario tests.
6. Implement services.
7. Add dirty-update phase.
8. Add trace events.
9. Add narrow performance budget test.

## What to stop

Stop adding adventure-specific readiness fields.

Stop adding direct action-selection logic in Phase 2.

Stop duplicating existing combat, quest, regional, and API tests.

## Consequence if ignored

You will jump from rich world options directly to decision-making without a stable self-model.

That creates brittle behavior:

```text id="bawzux"
entity chooses action
but cannot explain what it believes about itself
cannot explain what it needs
cannot explain what it can do
cannot explain what it knows
```

Phase 2 fixes that foundation.
