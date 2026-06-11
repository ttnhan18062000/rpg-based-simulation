---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

# Implementation Plan — Fix Critical Cognition / Strategy Issues First

The source confirms several concrete problems: `GoalRegistry` currently registers only five built-in scorers, `TownScorer` returns `target_pos` but no `target_id`, and `AppraisalSystem` has an unreachable `< 0.1` panic branch because `< 0.2` is checked first.

Do these in order. Do not start adding new cognition features before these are fixed.

---

## Task 1 — Choose one authoritative cognition execution path

### Description

Current risk: cognition may be split between `CognitionDomain.execute_brain()` and pipeline-level strategic logic such as `StrategicIntelligenceSystem.fused_strategic_pass()`.

That is dangerous. Two “brains” means duplicated decisions, inconsistent state mutation, and impossible debugging.

### Proposed solution

Make one system the source of truth.

Recommended choice:

```text
StrategicIntelligenceSystem / pipeline pass = authoritative strategic brain
CognitionDomain = reusable low-level services only
```

So `CognitionDomain` should expose pure helpers such as:

```python
class CognitionDomain:
    def evaluate_emotion(...): ...
    def filter_saliency(...): ...
    def build_cognitive_context(...): ...
```

But it should not independently decide final strategic projects if the pipeline already does that.

### Checklist

- [ ] Identify all call sites of `CognitionDomain.execute_brain()`.
- [ ] Identify all call sites of `StrategicIntelligenceSystem.fused_strategic_pass()`.
- [ ] Decide one authoritative path.
- [ ] Remove, deprecate, or narrow the other path.
- [ ] Add a test proving each entity receives exactly one strategic decision update per strategic tick.
- [ ] Add a test proving tactical decisions consume the selected strategic state, not a parallel cognition output.
- [ ] Add comments in code documenting the boundary:
  - strategic planning
  - emotional appraisal
  - tactical decision
  - action execution

### Important notes

Do not keep both paths “just in case.” That is cowardice disguised as flexibility. Pick one.

---

## Task 2 — Expand goal registry or reduce personality claims

### Description

The current `GoalRegistry` registers only:

```text
harvesting
fatigue
hunger
social
town_return
```

That is too narrow for the existing personality and strategy model. Traits like bravery, greed, industry, sociability, and directives cannot matter enough if the entity only chooses from five basic needs.

### Proposed solution

Add first-class goal scorers only where the engine already has downstream behavior.

Suggested new scorers:

| New scorer        | Purpose                                      |
| ----------------- | -------------------------------------------- |
| `combat_engage`   | bravery/aggression can produce combat intent |
| `combat_retreat`  | fear/panic/low HP can produce escape intent  |
| `crafting`        | missing materials, blacksmith, recipe goals  |
| `trade_profit`    | greed/economy-driven behavior                |
| `quest_progress`  | project/objective-driven quest behavior      |
| `recover`         | low HP, injury, stamina, safety behavior     |
| `resolve_blocker` | direct strategic blocker-to-goal bridge      |

Example shape:

```python
class CombatRetreatScorer:
    def score(self, entity, state):
        if entity.combat.hp_ratio > 0.4:
            return GoalScore(kind="combat_retreat", utility=0.0)

        utility = 80.0
        utility += entity.cognition.emotional.panic_level * 50.0
        utility -= entity.personality.bravery * 30.0

        return GoalScore(
            kind="combat_retreat",
            utility=utility,
            target_pos=state.town_center,
            metadata={"reason": "low_hp_or_panic"}
        )
```

### Checklist

- [x] Add only goal scorers that have real downstream project/action support.
- [x] Add unit tests for each new scorer.
- [x] Add integration tests proving high utility becomes a project or tactical action.
- [x] Add personality-difference tests:
  - brave entity engages more often than cowardly entity
  - greedy entity prioritizes profitable loot/trade more often
  - industrious entity prioritizes crafting/harvesting more often

- [x] Add deterministic tie-breaking between goal scores.
- [x] Update observability to expose selected goal kind and rejected alternatives.

### Important notes

Do not add 20 new goals. Add the minimum set that makes existing personality traits real.

---

## Task 3 — Wire belief system into actual gameplay

### Description

The belief system is rich, but the example documentation correctly flags that it is under-consumed: beliefs track observations, rumors, certainty, and contradictions, but normal town/social loops mostly use simple direct information sources.

### Proposed solution

Create a minimal belief-to-action path.

Required flow:

```text
information event
-> BeliefCycleSystem records belief
-> LeadState / HypothesisState updates
-> strategic scorer uses belief confidence
-> entity chooses or rejects action
-> contradiction changes future behavior
```

Add three concrete integration points:

| Integration point  | Behavior                                       |
| ------------------ | ---------------------------------------------- |
| Guild intel        | creates rumor-type beliefs, not just raw leads |
| Direct observation | upgrades or contradicts belief certainty       |
| Detour selection   | weighs lead certainty and source trust         |

Example logic:

```python
if observed_resource_missing:
    belief = belief_cycle.contradict(
        entity=entity,
        belief_key=f"resource:{node_id}:available",
        evidence_source="direct_observation"
    )

    if belief.certainty < MIN_ACTIONABLE_CERTAINTY:
        strategic.remove_or_deprioritize_lead(node_id)
```

### Checklist

- [x] Guild intel creates `BeliefEntry` with source type `rumor`.
- [x] Direct observation creates or updates `BeliefEntry` with stronger certainty.
- [x] Contradiction increments contradiction count.
- [x] Contradiction reduces future lead utility.
- [x] Detour selection ignores or deprioritizes exhausted/vague contradicted leads.
- [x] Add test: false rumor sends entity once, contradiction prevents repeated bad detour.
- [x] Add test: high-trust source beats low-trust source when both point to different targets.
- [x] Add event output for belief creation, belief contradiction, and belief exhaustion.

### Important notes

A belief system that does not change behavior is fake intelligence. Make belief affect action or delete the complexity.

---

## Task 4 — Make capacity enforcement unconditional and testable

### Description

The architecture claims cognition capacity is enforced, but the risk is that trimming happens only during strategic updates. If an entity is overloaded and no new update occurs, stale excess state may survive.

### Proposed solution

Separate capacity enforcement from strategic mutation.

Recommended structure:

```text
Strategic mutation systems create/update projects, leads, concerns, hypotheses.
CapacityEnforcementPhase trims every eligible entity on its cadence.
```

Capacity enforcement should be idempotent:

```python
def enforce_capacity(entity):
    strategic = entity.strategic
    profile = strategic.profile

    strategic.projects = keep_top_n(strategic.projects, profile.max_active_projects)
    strategic.leads = keep_top_n(strategic.leads, profile.max_leads)
    strategic.concerns = keep_top_n(strategic.concerns, profile.max_concerns)
    strategic.hypotheses = keep_top_n(strategic.hypotheses, profile.max_hypotheses)
```

### Checklist

- [x] Capacity enforcement runs independently from new strategic updates.
- [x] Enforcement is deterministic.
- [x] Enforcement preserves active/current project unless invalid.
- [x] Enforcement preserves highest-priority blockers/concerns/leads.
- [x] Add test: overloaded entity is trimmed even when no new concern/lead is added.
- [x] Add test: repeated enforcement produces same state after first trim.
- [x] Add observability event when trimming occurs:
  - entity ID
  - field trimmed
  - before count
  - after count
  - dropped IDs

### Important notes

Do not make trimming silent. Silent cognitive deletion will become a debugging nightmare.

---

## Task 5 — Fix enum/string drift

### Description

The engine appears to mix enum-like concepts with raw strings such as:

```text
"detour"
"harvesting"
"shopping"
"trauma"
"victory"
```

That causes schema drift. Diagnostics may say a project is one kind while runtime logic expects another.

### Proposed solution

Introduce canonical enums or constants for all strategic kinds.

Example:

```python
class GoalKind(str, Enum):
    HARVESTING = "harvesting"
    FATIGUE = "fatigue"
    HUNGER = "hunger"
    SOCIAL = "social"
    TOWN_RETURN = "town_return"
    COMBAT_RETREAT = "combat_retreat"
    COMBAT_ENGAGE = "combat_engage"
    CRAFTING = "crafting"
    DETOUR = "detour"
```

Then use constants everywhere:

```python
GoalRegistry.register(GoalKind.HARVESTING, HarvestScorer())
```

### Checklist

- [x] Define canonical enum/constant classes for:
  - goal kinds
  - project kinds
  - blocker kinds
  - concern kinds
  - directive kinds
  - event kinds

- [x] Replace raw strings in core logic.
- [x] Allow string serialization at boundaries only.
- [x] Add validation for loaded persisted state.
- [x] Add test: every registered goal kind is a valid canonical kind.
- [x] Add test: every emitted cognition event uses a valid event kind.
- [x] Add test: invalid persisted kind fails fast or maps through a migration layer.

### Important notes

Do not use enums everywhere blindly if persistence is string-based. Use string enums or constants that serialize cleanly.

---

## Task 6 — Fix near-death panic logic

### Description

Current panic logic checks:

```python
if hp_percent < 0.2:
    panic += 0.5
elif hp_percent < 0.1:
    panic += 0.8
```

The `< 0.1` branch is unreachable because anything below `0.1` already satisfies `< 0.2`.

### Proposed solution

Reverse the condition order:

```python
if hp_percent < 0.1:
    panic += 0.8
elif hp_percent < 0.2:
    panic += 0.5
```

Better version:

```python
if hp_percent < 0.1:
    panic += 0.8
elif hp_percent < 0.2:
    panic += 0.5
elif hp_percent < 0.4:
    panic += 0.2
```

### Checklist

- [x] `< 0.1` branch is reachable.
- [x] Panic at 9% HP is greater than panic at 15% HP.
- [x] Panic at 15% HP is greater than panic at 35% HP.
- [x] `is_fleeing` becomes true when panic crosses threshold.
- [x] Tactical decision uses `is_fleeing` to produce retreat behavior.
- [x] Add regression test for HP thresholds.

### Important notes

This is a small fix with high trust value. Do it early.

---

## Task 7 — Fix `TownScorer` project creation compatibility

### Description

`TownScorer` returns:

```python
GoalScore(kind="town_return", utility=utility, target_pos=state.town_center)
```

but does not return `target_id`. If downstream strategic project creation expects `target_id`, town return may score high but fail to become a normal project.

### Proposed solution

Option A: Add a canonical town target ID.

```python
return GoalScore(
    kind="town_return",
    utility=utility,
    target_id="town_center",
    target_pos=state.town_center,
    metadata={"target_type": "town"}
)
```

Option B: Update project creation to accept position-only targets.

```python
if score.target_id or score.target_pos:
    create_project_from_goal(score)
```

Recommended: do both safely.

### Checklist

- [x] `TownScorer` returns enough target data to create a project.
- [x] Strategic project creation supports `target_pos`.
- [x] Project objective supports navigation to position-only targets.
- [x] Add test: high hunger/sleep/inventory/full HP pressure creates town-return project.
- [x] Add test: town-return project produces movement toward town center.
- [x] Add test: after reaching town, correct service behavior triggers:
  - sleep
  - eat
  - sell/store
  - heal/recover, if implemented

### Important notes

A score that cannot become behavior is dead code. Fix the bridge.

---

## Task 8 — Decide what social contracts are supposed to do

### Description

The social system has contracts, trust, risk, betrayal, and negotiation, but town economy behavior is mostly atomic: buy, sell, craft, store. The documentation correctly calls out this mismatch.

### Proposed solution

Pick one of two strategies.

Recommended for now: **thin integration, not full negotiation**.

Use social contracts for only three high-value behaviors first:

| Contract use        | Concrete behavior                        |
| ------------------- | ---------------------------------------- |
| debt / promise      | entity owes item/gold/service            |
| escort / protection | entity follows/protects another          |
| delivery / fetch    | entity commits to deliver item to target |

Minimal contract flow:

```text
offer contract
-> accept/reject based on trust/risk/reward
-> create project/objective
-> monitor completion/failure
-> update trust/reputation
```

### Checklist

- [ ] Define 2–3 contract types only.
- [ ] Each contract type creates a real project or objective.
- [ ] Contract failure affects trust.
- [ ] Betrayal record affects future acceptance probability.
- [ ] Shop/blacksmith remain atomic unless explicitly turned into contracts.
- [ ] Add test: accepted delivery contract creates objective.
- [ ] Add test: failed contract reduces trust.
- [ ] Add test: previous betrayal reduces future contract acceptance.

### Important notes

Do not build a negotiation simulator before basic contracts affect behavior. That would be architecture theater.

---

## Task 9 — Make observability prove behavior, not just expose state

### Description

The cognition observability stack is strong, but there is a risk: snapshots and graphs can make the system look smarter than it behaves. The documentation says cognition is heavily exposed through snapshots, diffs, events, and root cause analysis.

### Proposed solution

Every cognition event should connect state change to behavioral consequence.

Add causal trace fields:

```python
{
    "event": "StrategicProjectChanged",
    "entity_id": 123,
    "previous_project": "harvesting",
    "new_project": "town_return",
    "reason": "inventory_full",
    "source_goal_score": 82.5,
    "resulting_action": "move",
    "target_pos": [10, 5]
}
```

Add a “cognition-to-action trace”:

```text
goal scores
-> selected goal
-> project created/switched
-> blocker/detour applied
-> tactical intent
-> action attempted
-> action accepted/rejected
```

### Checklist

- [x] Each selected goal has trace output.
- [x] Each project switch records the winning score and previous score.
- [x] Each blocker/detour records source lead and confidence.
- [x] Each tactical action records strategic source, if any.
- [x] Root cause engine distinguishes:
  - state-only anomaly
  - behavior anomaly
  - failed bridge from cognition to action

- [x] Add test: when project changes, a corresponding action or rejection appears within N ticks.
- [x] Add test: diagnostic report flags “cognition state did not produce behavior.”

### Important notes

Observability must become a lie detector. Not a decoration layer.

---

## Task 10 — Make `detour_depth` real or remove it

### Description

`detour_depth` sounds like multi-step planning, but the inspected behavior looks closer to one-step detour selection: blocker plus known lead equals detour project.

That is fine, but the config name overpromises.

### Proposed solution

Choose one.

Option A: Make it real.

```text
depth 1: find direct lead for blocker
depth 2: if lead requires precondition, create sub-detour
depth 3: allow chained blocker resolution
```

Example:

```text
Need sword
-> missing iron
-> known iron node blocked by danger
-> detour to recruit ally / recover first
-> then harvest iron
-> then craft sword
```

Option B: Rename it.

```text
detour_depth -> reserved_detour_depth
```

or remove it until implemented.

Recommended now: **rename or remove unless you are ready to test recursive planning**.

### Checklist

- [x] Search all usages of `detour_depth`.
- [x] If keeping it, implement depth-limited recursive detour planning.
- [x] If not keeping it, remove from active config or mark as reserved.
- [x] Add test for depth 1 behavior.
- [x] Add test for depth 2 behavior if implemented.
- [x] Add guard against detour loops.
- [x] Add event when detour depth limit is reached.

### Important notes

A config knob that does nothing meaningful is worse than no knob. It trains users to distrust the system.

---

# Suggested Execution Order

| Order | Task                                               | Why first                                         |
| ----: | -------------------------------------------------- | ------------------------------------------------- |
|     1 | Fix near-death panic                               | Small, clear bug                                  |
|     2 | Fix `TownScorer` bridge                            | Small, likely behavior bug                        |
|     3 | Choose authoritative cognition path                | Prevents future work from landing in wrong system |
|     4 | Fix enum/string drift                              | Prevents schema and event corruption              |
|     5 | Make capacity enforcement unconditional            | Stabilizes mental-state invariants                |
|     6 | Expand goal registry carefully                     | Makes personality/strategy real                   |
|     7 | Wire belief into gameplay                          | Makes epistemic model real                        |
|     8 | Define social contract behavior                    | Prevents social system bloat                      |
|     9 | Upgrade observability to cognition-to-action trace | Makes debugging honest                            |
|    10 | Implement or remove `detour_depth`                 | Removes misleading architecture surface           |

---

# Priority Plan

## Mindset / assumptions to change

Stop treating the cognition model as complete because the classes exist. The only valid proof is:

```text
cognitive state changes behavior under test
```

## Immediate actions

Start with the two obvious bugs:

```text
AppraisalSystem panic threshold
TownScorer target bridge
```

Then lock the architecture:

```text
one authoritative strategic brain
canonical goal/project/event kinds
capacity invariants
```

## Stop / eliminate

Stop adding more cognitive vocabulary until the existing vocabulary produces measurable behavior.

No more new:

```text
belief categories
emotion fields
social contract states
hypothesis types
personality traits
```

until each one affects goal scoring, project switching, tactical action, and test assertions.

## Consequence if ignored

You will build a beautiful cognition dashboard over a shallow rule-based agent. The opportunity cost is brutal: slower development, harder debugging, weaker experiments, and zero credibility when behavior does not match the architecture.
