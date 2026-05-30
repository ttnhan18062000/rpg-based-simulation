# Phase 4 — Combat Engagement Cognition

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
entity decides whether to enter, avoid, probe, continue, or exit combat
based on subjective estimate, personality, objective pressure, and memory
```

Current tests already cover many combat-adjacent things: arena quest kill/reward progression, regional combat effects, conquest debuffs, arena startup/scaling, stop conditions, group coordination, stress, legality/readiness, and root-cause detection for unresolved combat.

So Phase 4 must **not** duplicate:

```text
damage formula
attack legality
quest reward after kill
regional influence after death
arena 5v5 tactics
50v50 stress
combat stop condition
```

Phase 4 tests the missing layer:

```text
pre-combat judgment
mid-combat reassessment
post-combat learning
future decision change
```

The cognition doc already describes selective attention, emotional appraisal, personality bias, tactical decision-making, and movement modes, but also identifies the gap: emotional/personality cognition is richer than the actual downstream combat behavior that consumes it.

---

# Phase 4 goal

Phase 4 answers:

```text
Given that entity A sees entity B,
does A believe fighting B is worth the risk?
```

Not:

```text
Can A legally attack B?
```

That already exists.

Not:

```text
How much damage does A deal?
```

That already exists.

Phase 4 sits before and around combat execution:

```text
perceive target
-> estimate target
-> estimate self
-> evaluate risk/value/personality
-> choose combat posture
-> execute tactical intent
-> observe outcome
-> learn
-> future engagement changes
```

---

# Phase 4 success definition

Phase 4 is successful when the engine can produce traces like:

```yaml
combat_engagement_decision:
  actor_id: 1
  target_id: 2
  perceived_target_power:
    estimate: 105
    uncertainty: 0.25
    confidence: 0.55
  self_combat_estimate:
    estimate: 100
    condition_modifier: -0.10
  objective_pressure:
    quest_target: true
    value: 0.30
  personality_modifiers:
    bravery: +0.15
    caution: -0.05
  selected_posture: PROBE
  reason: "target appears near-equal, uncertainty high, objective value moderate"
```

After loss:

```yaml
combat_learning:
  actor_id: 1
  target_id: 2
  outcome: LOST
  observed_target_damage: high
  observed_skill_ids:
    - heavy_strike
  updated_opponent_estimate:
    estimate: 125
    uncertainty: 0.08
  future_effect: avoid_same_target_unless_stronger_or_with_allies
```

---

# Task 1 — Define combat engagement boundary

## Description

Create a domain layer for combat engagement cognition.

Do **not** put this directly into `CombatResolutionSystem`.

Combat resolution should stay authoritative and mathematical.

Combat engagement cognition should decide:

```text
engage
avoid
watch
probe
skirmish
call help
retreat
panic flee
```

## Proposed solution

Create:

```text
src/domains/combat_engagement/
```

Main service:

```python
class CombatEngagementDecisionService:
    def evaluate(
        self,
        actor: EntityState,
        target: EntityState,
        state: AuthoritativeState,
        context: CombatEngagementContext,
    ) -> CombatEngagementDecisionResult:
        ...
```

## Checklist

 - [x] Combat engagement logic is outside combat damage resolution.
 - [x] Service does not mutate state directly.
 - [x] Service does not bypass attack legality.
 - [x] Service consumes Phase 2 self-model and capability estimates.
 - [x] Service can consume Phase 3 objective pressure.
 - [x] Service returns posture and trace.
 - [x] Same input + same seed produces deterministic result.
 - [x] Existing arena/combat resolution tests still pass unchanged.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_combat_engagement_boundary.py
```

Test cases:

```text
test_engagement_service_does_not_execute_attack
test_engagement_service_does_not_mutate_state
test_engagement_service_returns_posture_trace
test_engagement_service_does_not_require_adventure_component
```

---

# Task 2 — Define combat posture vocabulary

## Description

Combat should not be binary:

```text
fight / flee
```

Use posture.

## Initial posture set

```text
IGNORE
WATCH
AVOID
PROBE
THREATEN
ENGAGE
SKIRMISH
CALL_HELP
RETREAT
PANIC_FLEE
GUARD_ALLY
VENGEANCE_ENGAGE
```

## Meaning

| Posture            | Meaning                                  |
| ------------------ | ---------------------------------------- |
| `IGNORE`           | target irrelevant                        |
| `WATCH`            | observe without commitment               |
| `AVOID`            | route around                             |
| `PROBE`            | test target with low commitment          |
| `THREATEN`         | hold ground / intimidate                 |
| `ENGAGE`           | commit to fight                          |
| `SKIRMISH`         | fight while preserving escape            |
| `CALL_HELP`        | seek ally/group                          |
| `RETREAT`          | controlled withdrawal                    |
| `PANIC_FLEE`       | emergency emotional flee                 |
| `GUARD_ALLY`       | fight because ally/objective requires it |
| `VENGEANCE_ENGAGE` | non-optimal grudge-driven attack         |

## Checklist

 - [x] Postures are canonical constants/enums.
 - [x] Every posture has semantic definition.
 - [x] Every posture maps to tactical/movement/action intent later.
 - [x] No posture directly applies damage.
 - [x] Unknown posture fails fast.
 - [x] Posture appears in trace.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_combat_postures.py
```

Test cases:

```text
test_combat_posture_names_are_unique
test_each_posture_has_semantic_mapping
test_each_posture_has_trace_label
test_unknown_posture_fails_fast
```

---

# Task 3 — Implement `OpponentPerceptionService`

## Description

The entity should not know exact target power.

It should estimate based on visible and remembered signals.

## Inputs

```text
target visible level
target role/class/kind
target equipment hints
target current HP appearance
target group support
known faction
known enemy type
past memory
distance / visibility
actor perception/intelligence/wisdom
actor stress/panic
```

## Output

```python
@dataclass(frozen=True)
class PerceivedOpponentEstimate:
    target_id: int
    estimated_power: float
    uncertainty: float
    confidence: float
    visible_signals: tuple[str, ...]
    unknown_factors: tuple[str, ...]
    memory_used: tuple[str, ...] = ()
```

Example:

```text
A sees B.
B appears equal.
A has low prior knowledge.

estimated_power = 100
uncertainty = 0.25
confidence = 0.55
```

After previous combat:

```text
estimated_power = 125
uncertainty = 0.08
confidence = 0.85
```

## Checklist

 - [x] Estimate does not use hidden exact combat truth directly.
 - [x] Visible enemy type affects estimate.
 - [x] Visible equipment/level hints affect estimate.
 - [x] Prior memory reduces uncertainty.
 - [x] Low perception/wisdom increases uncertainty.
 - [x] Panic/stress can increase uncertainty.
 - [x] Output is deterministic.
 - [x] Trace lists visible signals and unknown factors.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py
```

Test cases:

```text
test_unknown_enemy_has_high_uncertainty
test_known_enemy_memory_reduces_uncertainty
test_visible_better_equipment_increases_estimate
test_low_perception_increases_uncertainty
test_estimate_does_not_expose_hidden_exact_power
```

---

# Task 4 — Implement `SelfCombatEstimateService`

## Description

Phase 2 self-awareness says:

```text
I am wounded.
I am tired.
I have weak gear.
```

Phase 4 needs a combat-specific derived estimate:

```text
How capable am I in this fight, right now?
```

This is a derived view, not a permanent entity component.

## Proposed output

```python
@dataclass(frozen=True)
class SelfCombatEstimate:
    actor_id: int
    estimated_power: float
    confidence: float
    condition_modifiers: Mapping[str, float]
    constraints: tuple[str, ...]
```

Inputs:

```text
HP
stamina
wounds
equipment quality
durability
skills/cooldowns
party support
escape route
Phase 2 capability estimate
Phase 2 self-awareness
```

## Checklist

 - [x] Low HP reduces self estimate.
 - [x] Low stamina reduces self estimate.
 - [x] Damaged weapon reduces self estimate.
 - [x] Better equipment increases self estimate.
 - [x] Ally support can increase group estimate.
 - [x] No escape route increases risk, not raw power.
 - [x] Output is deterministic.
 - [x] Service does not mutate state.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_self_combat_estimate.py
```

Test cases:

```text
test_low_hp_reduces_self_combat_estimate
test_low_stamina_reduces_self_combat_estimate
test_better_weapon_increases_self_combat_estimate
test_damaged_weapon_reduces_self_combat_estimate
test_ally_support_increases_group_confidence
```

---

# Task 5 — Implement `EngagementRiskEvaluator`

## Description

This evaluator decides whether the fight seems worth the risk.

It does not choose final posture yet.

## Inputs

```text
perceived opponent estimate
self combat estimate
objective pressure
reward expectation
death/wound risk
uncertainty
escape possibility
ally support
personality traits
emotion/appraisal
combat memory
```

## Output

```python
@dataclass(frozen=True)
class EngagementRiskEvaluation:
    win_confidence: float
    death_risk: float
    uncertainty_penalty: float
    objective_value: float
    personality_bias: float
    emotional_bias: float
    risk_score: float
    value_score: float
    acceptable: bool
    reasons: tuple[str, ...]
```

## Scoring idea

```text
engage_value =
    objective_value
  + reward_value
  + bravery/aggression/grudge
  + ally_support
  - death_risk
  - uncertainty_penalty
  - wound/fatigue penalty
  - fear memory
```

## Checklist

 - [x] Risk uses subjective opponent estimate.
 - [x] Risk uses self combat estimate.
 - [x] High uncertainty penalizes engagement.
 - [x] High objective pressure can justify risk.
 - [x] Brave/aggressive entity tolerates more risk.
 - [x] Cautious/fearful entity tolerates less risk.
 - [x] Grudge can create non-optimal but explainable engagement.
 - [x] Evaluation trace includes all major modifiers.
 - [x] Deterministic under same input.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_engagement_risk.py
```

Test cases:

```text
test_equal_power_high_uncertainty_prefers_probe_or_watch
test_low_hp_increases_death_risk
test_brave_trait_increases_risk_tolerance
test_cautious_trait_decreases_risk_tolerance
test_grudge_can_override_caution_with_trace
test_objective_pressure_can_justify_engagement
test_risk_evaluator_uses_subjective_estimate_not_truth
```

---

# Task 6 — Implement `CombatPostureSelector`

## Description

Convert risk evaluation into posture.

## Mapping examples

| Condition                        | Posture                   |
| -------------------------------- | ------------------------- |
| irrelevant target                | `IGNORE`                  |
| unknown near-equal target        | `WATCH` or `PROBE`        |
| target stronger, no objective    | `AVOID`                   |
| target stronger, must pass route | `CALL_HELP` or `SKIRMISH` |
| target weaker, reward relevant   | `ENGAGE`                  |
| low HP mid-combat                | `RETREAT`                 |
| panic high                       | `PANIC_FLEE`              |
| ally threatened                  | `GUARD_ALLY`              |
| grudge high                      | `VENGEANCE_ENGAGE`        |

## Checklist

 - [x] Selector accepts risk evaluation.
 - [x] Selector returns one posture.
 - [x] Selector can return non-attack postures.
 - [x] Selector can return `PROBE` when uncertainty is high.
 - [x] Selector can return `RETREAT` when condition is bad.
 - [x] Selector can return `VENGEANCE_ENGAGE` for grudge case.
 - [x] Selector output includes reason trace.
 - [x] Selector is deterministic.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_posture_selector.py
```

Test cases:

```text
test_weaker_enemy_selects_engage
test_unknown_equal_enemy_selects_probe_or_watch
test_stronger_enemy_without_objective_selects_avoid
test_low_hp_selects_retreat
test_panic_selects_panic_flee
test_ally_threat_selects_guard_ally
test_grudge_selects_vengeance_engage_when_bias_crosses_threshold
```

---

# Task 7 — Map posture to tactical/action intent

## Description

The source already has tactical movement modes and action handling. Phase 4 should bridge posture into existing behavior, not rewrite tactics.

## Mapping

| Posture            | Intent                                                 |
| ------------------ | ------------------------------------------------------ |
| `IGNORE`           | none / continue current project                        |
| `WATCH`            | maintain distance / no attack                          |
| `AVOID`            | navigation detour                                      |
| `PROBE`            | low-commitment approach / ranged poke if available     |
| `THREATEN`         | hold position / face target                            |
| `ENGAGE`           | attack / pursue target                                 |
| `SKIRMISH`         | attack + preserve distance                             |
| `CALL_HELP`        | social/party request later; for now, strategic blocker |
| `RETREAT`          | movement mode retreat                                  |
| `PANIC_FLEE`       | emergency retreat                                      |
| `GUARD_ALLY`       | move/attack to protect ally                            |
| `VENGEANCE_ENGAGE` | attack despite risk trace                              |

## Checklist

 - [x] Mapping produces `ActionIntent` or `StrategicUpdate`, not direct mutation.
 - [x] `ENGAGE` maps to existing attack route only if legal later.
 - [x] `RETREAT` maps to movement/navigation, not HP mutation.
 - [x] `CALL_HELP` can create blocker/need if party system not ready.
 - [x] No posture bypasses `verify_attack_legality`.
 - [x] No posture bypasses readiness checks.
 - [x] Existing combat legality tests remain authoritative.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_posture_to_intent.py
```

Test cases:

```text
test_engage_posture_maps_to_attack_intent
test_retreat_posture_maps_to_retreat_movement_intent
test_avoid_posture_maps_to_detour_or_no_attack
test_probe_posture_does_not_force_full_commitment
test_call_help_creates_blocker_when_party_system_missing
test_mapping_does_not_bypass_attack_legality
```

---

# Task 8 — Add mid-combat reassessment

## Description

Engagement decision should not happen only before combat.

During combat, new information appears:

```text
target deals high damage
target uses hidden skill
actor HP drops
ally dies
target flees
stamina drops
escape route changes
```

The entity should reassess posture.

## Proposed service

```python
class CombatReassessmentService:
    def reassess(
        self,
        actor: EntityState,
        target: EntityState,
        recent_combat_events: Sequence[CombatEvent],
        previous_decision: CombatEngagementDecisionResult,
        state: AuthoritativeState,
    ) -> CombatEngagementDecisionResult:
        ...
```

## Checklist

 - [x] HP drop can change `ENGAGE` to `RETREAT`.
 - [x] Hidden skill observation can increase target estimate.
 - [x] Ally death can increase risk.
 - [x] Target weak/fleeing can increase engage/pursue confidence.
 - [x] Reassessment has cooldown/cadence to avoid posture flicker.
 - [x] Reassessment respects target stickiness and interruption resistance.
 - [x] Reassessment trace explains changed posture.
 - [x] Does not duplicate existing tactical target switching tests.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_combat_reassessment.py
```

Test cases:

```text
test_high_damage_received_triggers_retreat_reassessment
test_hidden_skill_seen_increases_target_estimate
test_ally_death_increases_risk
test_target_low_hp_can_shift_probe_to_engage
test_reassessment_cooldown_prevents_flicker
```

---

# Task 9 — Add combat learning / opponent model update

## Description

After combat, the entity should remember important combat information.

This is not full general memory yet.

It is a minimal combat-specific learning layer.

## Proposed data

```python
@dataclass(frozen=True)
class OpponentModel:
    subject_key: str
    estimated_power: float
    uncertainty: float
    confidence: float
    known_skill_ids: tuple[str, ...] = ()
    outcomes: tuple[str, ...] = ()
    last_updated_tick: int = 0
```

Subject keys:

```text
entity.42
enemy_type.wolf
faction.bandits
region.north_ruin.combat
```

## Learning events

```text
won_easy
won_close
lost
fled
nearly_died
observed_high_damage
observed_skill
ally_killed
enemy_fled
```

## Checklist

 - [x] Loss increases opponent estimate or risk.
 - [x] Easy win decreases perceived risk.
 - [x] Hidden skill is recorded when observed.
 - [x] Near-death strongly increases future caution.
 - [x] Memory can be specific target and generalized enemy type.
 - [x] Memory reduces future uncertainty.
 - [x] Memory is capacity-limited.
 - [x] Learning update is deterministic.
 - [x] Learning does not mutate world truth.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_combat_learning.py
```

Test cases:

```text
test_losing_to_target_increases_future_estimate
test_easy_win_reduces_future_risk
test_observed_skill_is_recorded
test_near_death_creates_strong_risk_memory
test_memory_reduces_uncertainty_next_encounter
test_memory_capacity_is_bounded
```

---

# Task 10 — Add combat engagement phase

## Description

Integrate the service into the engine as a bounded phase.

Do not evaluate every possible pair every tick.

## Trigger conditions

```text
hostile or relevant entity enters sensory range
current objective requires target
actor is attacked
actor has combat directive
actor has quest target visible
actor current combat posture expired
recent combat event requires reassessment
```

## Skip conditions

```text
entity dead/inactive
entity stunned/frozen
no relevant target
decision cooldown active
strategic budget exceeded
combat engagement disabled by feature flag
```

## Checklist

 - [x] Phase is behind feature flag initially.
 - [x] Phase uses sensory filter / relevant target candidates.
 - [x] Phase caps targets considered per entity.
 - [x] Phase does not run full pairwise entity comparison.
 - [x] Phase produces posture/intents/strategic updates.
 - [x] Phase emits trace events.
 - [x] Phase respects existing tactical system and attack legality.
 - [x] Performance counters include engagement evaluations.

## TDD tests

Add:

```text
tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py
```

Test cases:

```text
test_phase_skips_entity_without_relevant_target
test_phase_runs_when_hostile_enters_range
test_phase_caps_targets_considered
test_phase_skips_dead_entity
test_phase_respects_feature_flag
test_phase_does_not_perform_pairwise_global_scan
test_phase_produces_posture_trace
```

---

# Task 11 — Add Phase 4 scenario tests

These are scenario-driven tests, not raw combat mechanics tests.

## Scenario 4.1 — Unknown equal opponent

```text
A sees B.
B appears equal power with high uncertainty.
A has no urgent objective.
```

Expected:

```text
A chooses WATCH, AVOID, or PROBE.
A should not always instantly ENGAGE.
```

Forbidden:

```text
uses exact hidden target power
attacks without decision trace
```

---

## Scenario 4.2 — Brave vs cautious divergence

```text
Same target.
Same world.
Two entities:
- brave
- cautious
```

Expected:

```text
brave entity may select PROBE/ENGAGE
cautious entity may select WATCH/AVOID
both choices are valid and traceable
```

---

## Scenario 4.3 — Objective pressure justifies risk

```text
A has active hunt quest.
Target appears slightly risky.
```

Expected:

```text
A may engage or probe because objective value raises engagement score.
Trace must show objective pressure.
```

---

## Scenario 4.4 — Loss changes future decision

```text
A fights B and loses badly.
Later A sees B again.
```

Expected:

```text
A estimate for B is stronger.
Uncertainty is lower.
A avoids, calls help, probes, or retreats unless stronger.
```

This is the most important Phase 4 scenario.

---

## Scenario 4.5 — Hidden skill revealed mid-combat

```text
A initially estimates B as manageable.
B uses hidden skill.
```

Expected:

```text
A updates target model.
A reassesses posture.
A may retreat or switch to skirmish.
```

---

## Scenario 4.6 — Monster self-preservation

```text
Monster attacks adventurer.
Monster is badly wounded.
```

Expected:

```text
Monster may retreat or flee.
Monster should not always fight to death.
```

This is important. Monsters should not be loot boxes by default.

---

## Test file

```text
tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py
```

## Checklist

 - [x] Scenarios assert posture family, not exact movement path.
 - [x] Scenarios assert decision trace.
 - [x] Scenarios assert subjective estimates, not exact formulas.
 - [x] Scenarios do not duplicate arena damage/quest tests.
 - [x] Scenario 4.4 proves future behavior changes after loss.
 - [x] Scenario 4.6 proves monster self-preservation path exists.
 - [x] Scenarios are deterministic under fixed seed.

---

# Task 12 — Add Phase 4 observability and diagnostics

## Description

Combat engagement must be inspectable.

Existing observability is strong; use it. Do not add another API suite yet.

Add event types and scenario scorecard consumption.

## Event types

```text
CombatOpponentPerceived
CombatEngagementEvaluated
CombatPostureSelected
CombatPostureChanged
CombatReassessmentTriggered
CombatExperienceLearned
OpponentModelUpdated
```

## Example event

```yaml
event_type: CombatPostureSelected
entity_id: 1
target_id: 2
posture: PROBE
reason: "high uncertainty equal target"
risk_score: 0.42
value_score: 0.38
```

## Checklist

 - [x] Events emitted only on meaningful change.
 - [x] Events include reason fields.
 - [x] Events include estimate/uncertainty.
 - [x] Events do not mutate authoritative state.
 - [x] Scenario scorecard can read them.
 - [x] Event volume is bounded.
 - [x] Existing observability parity tests still pass.

## TDD tests

Add:

```text
tests/unit/domains/combat_engagement/test_phase4_combat_engagement_events.py
```

Test cases:

```text
test_engagement_event_payload_contains_estimate_and_reason
test_posture_change_event_emitted_only_on_change
test_learning_event_contains_outcome_and_future_effect
test_event_generation_does_not_change_state_hash
```

---

# Task 13 — Add Phase 4 performance gates

## Description

Combat engagement can explode computationally if implemented as all-vs-all evaluation.

Never do that.

## Required metrics

```text
combat_engagement_evaluations_total
targets_considered_total
targets_considered_per_entity_max
opponent_estimates_computed_total
reassessments_total
combat_learning_updates_total
avg_engagement_ms
p95_engagement_ms
skipped_due_to_budget
```

## Performance tests

```text
10 entities, 500 ticks
100 entities, 500 ticks
500 entities, 200 ticks
50v50 arena with engagement phase enabled
```

## Checklist

 - [x] Max targets considered per entity is capped.
 - [x] Uses spatial/sensory filtering.
 - [x] No global pairwise scan.
 - [x] Feature flag OFF matches old behavior.
 - [x] Feature flag ON stays within agreed overhead.
 - [x] Determinism hash stable under same seed.
 - [x] Memory growth from opponent models is bounded.
 - [x] Performance report written.

## Test file

```text
tests/perf/test_phase4_combat_engagement_budget.py
```

---

# Phase 4 test files to add

```text
tests/unit/domains/combat_engagement/test_phase4_combat_engagement_boundary.py
tests/unit/domains/combat_engagement/test_phase4_combat_postures.py
tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py
tests/unit/domains/combat_engagement/test_phase4_self_combat_estimate.py
tests/unit/domains/combat_engagement/test_phase4_engagement_risk.py
tests/unit/domains/combat_engagement/test_phase4_posture_selector.py
tests/unit/domains/combat_engagement/test_phase4_posture_to_intent.py
tests/unit/domains/combat_engagement/test_phase4_combat_reassessment.py
tests/unit/domains/combat_engagement/test_phase4_combat_learning.py
tests/unit/domains/combat_engagement/test_phase4_combat_engagement_events.py
tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py
tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py
tests/perf/test_phase4_combat_engagement_budget.py
```

---

# Phase 4 non-goals

Do **not** implement these in Phase 4:

```text
new damage formula
new combat resolver
new quest reward logic
new regional conquest logic
full party coordination
full social negotiation
full rumor system
full long-term biography memory
full monster ecology overhaul
```

Do **not** duplicate existing tests around:

```text
arena combat resolution
hunt quest completion
regional influence shift
conquest debuff
50v50 stress
stop condition wipe/timeout
attack legality/readiness
```

Those are already covered in the uploaded test suite and source logic markers.

---

# Phase 4 completion criteria

Phase 4 is done when this is true:

```text
An entity does not enter combat only because a target is nearby.

It first forms a subjective estimate,
compares risk/value,
applies personality/emotion/objective pressure,
chooses a posture,
acts through existing systems,
learns from the result,
and behaves differently later.
```

Minimum proof:

```text
unknown equal target does not always trigger instant attack
brave and cautious entities diverge validly
objective pressure can justify risk
loss changes future estimate and posture
hidden skill causes reassessment
monster can preserve itself instead of always fighting to death
combat engagement overhead remains bounded
```

---

# Priority Plan

## What changes in Phase 4

Phase 3:

```text
choose adventure route
```

Phase 4:

```text
choose combat posture when an entity becomes a possible combat target
```

## Implementation order

```text
1. Combat posture vocabulary
2. Opponent perception estimate
3. Self combat estimate
4. Engagement risk evaluator
5. Posture selector
6. Posture-to-intent bridge
7. Mid-combat reassessment
8. Combat learning / opponent model update
9. Combat engagement phase integration
10. Scenario tests
11. Performance gates
```

## What to stop

Stop treating combat as:

```text
enemy visible -> attack
```

Stop treating combat decision as:

```text
my true power > enemy true power
```

Use:

```text
my perceived chance + personality + objective value + memory + uncertainty
```

## Consequence if ignored

Your entities will have richer routes and self-models, but combat will still feel mechanical.

They will fight, win, lose, and die.

But they will not seem to judge danger, make imperfect decisions, or learn from violence.

Phase 4 makes combat part of an entity’s life, not just an action handler.
