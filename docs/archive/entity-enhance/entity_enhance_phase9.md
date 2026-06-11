---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Phase 9 — Long-Run Life-Arc Scenario Campaigns

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
entity uses cooperation as life strategy
```

Phase 8:

```text
entity actions reshape the world
```

Phase 9:

```text
prove that all previous phases create coherent long-run entity lives
```

This phase is not mainly about adding new mechanics.

It is about proving:

```text
Over many ticks,
entities do not just execute isolated actions.

They form readable life arcs:
start weak
make imperfect choices
learn
recover
grow
fail
cooperate
avoid danger
change routes
reshape the world
```

The current uploaded tests already include long-run stability, determinism parity, arena stress, certification, observability, and API tests. So Phase 9 must **not** duplicate long-run performance/stability certification. It should test **semantic life continuity** over long runs.

---

# Phase 9 goal

Phase 9 answers:

```text
Does the simulation produce coherent lives, not just correct ticks?
```

Examples:

```text
Entity A starts weak.
A loses to wolf.
A remembers wolf risk.
A asks guide.
A gathers material.
A crafts better weapon.
A retries easier combat.
A gains confidence.
A later accepts harder quest.
```

Or:

```text
Entity B is cautious.
B hears north_ruin is dangerous.
B avoids it.
B takes safe quests.
B grows slowly.
Later, with party support, B investigates north_ruin.
```

Or:

```text
Many entities overharvest iron.
Iron scarcity appears.
Later entities stop choosing iron-based craft routes.
Some ask for alternate material.
Some take gold quests instead.
```

This is the first phase where you validate the engine as a **life simulation**, not just a mechanics engine.

---

# Phase 9 success definition

Phase 9 is successful when a campaign report can show:

```yaml
campaign_summary:
  campaign_id: first_30_days_adventurers
  ticks: 3000
  entity_count: 30

  entity_arcs:
    - entity_id: 1
      arc_type: cautious_growth
      major_events:
        - first_failed_hunt
        - recovered_at_inn
        - asked_guide
        - crafted_iron_sword
        - completed_easy_quest
      behavior_change_proofs:
        - avoided_wolf_after_loss
        - retried_after_upgrade

    - entity_id: 2
      arc_type: risky_growth
      major_events:
        - accepted_hunt_early
        - nearly_died
        - requested_party_next_time
        - completed_hunt_with_ally

  world_arcs:
    - region: old_mine
      arc: iron_scarcity
      effect:
        - later_entities_diversified_routes

  verdict:
    semantic_life_continuity: pass
    forbidden_behavior_count: 0
```

The proof is not:

```text
simulation ran 3000 ticks without crash
```

That is already covered elsewhere.

The proof is:

```text
past experience changed future behavior
world changes changed future route choices
entity choices formed readable long-run arcs
```

---

# Task 1 — Add Phase 9 coverage audit

## Description

Document what existing long-run tests already prove.

Existing uploaded tests already cover:

```text
long-run pure stability
long-run runtime stability
determinism parity
arena 50v50 stress
memory/resource envelope violations
observability parity
API live status/health/websocket
```

So Phase 9 should avoid testing:

```text
RSS boundedness only
p95 latency only
hash parity only
arena wipe/timeout only
API response shape only
```

Phase 9 tests:

```text
life-arc coherence
behavioral change after memory
route diversity
world-to-entity feedback
multi-entity divergence
campaign scorecard validity
```

## Proposed document

```text
docs/test_coverage/phase9_life_arc_campaign_coverage.md
```

## Checklist

- [x] Existing long-run stability tests are listed.
- [x] Existing arena stress tests are listed.
- [x] Existing determinism tests are listed.
- [x] Phase 9 semantic test scope is clearly separated.
- [x] No test duplicates raw long-run stability certification.
- [x] No test duplicates arena combat stress.
- [x] Phase 9 tests assert semantic arcs and behavior changes.

---

# Task 2 — Define campaign spec format

## Description

A campaign is not a scripted story.

It is a long-running scenario with:

```text
initial world
actors
pressure seeds
allowed route families
valid arc patterns
forbidden behaviors
semantic scorecard
```

The campaign should allow many valid paths.

Do not assert exact action sequence.

## Proposed model

```yaml
campaign_id: first_30_days_adventurers
seed: 42
ticks: 3000

world_pack: phase1_adventure_seed

actors:
  count: 30
  start_region: hometown
  start_level: 1
  class_distribution:
    warrior: 10
    ranger: 10
    mage: 10
  trait_distribution:
    brave: 0.25
    cautious: 0.25
    industrious: 0.25
    curious: 0.25

initial_world_pressures:
  - weak_starting_equipment
  - limited_iron_nodes
  - wolf_den_danger
  - unknown_moon_resin_source

expected_arc_families:
  - cautious_growth
  - risky_growth
  - craft_growth
  - information_growth
  - party_recovery
  - failed_adventurer
  - world_avoidance

forbidden_behavior:
  - omniscient_hidden_knowledge
  - repeated_same_failed_action_forever
  - action_after_death
  - direct_reward_mutation
  - global_full_world_scan
  - no_trace_for_major_decision
```

## Checklist

- [x] Campaign spec is data-driven.
- [x] Campaign spec supports multiple entities.
- [x] Campaign spec supports expected arc families.
- [x] Campaign spec supports forbidden behavior.
- [x] Campaign spec supports performance budget fields.
- [x] Campaign spec supports semantic scorecard rules.
- [x] Campaign spec does not hardcode exact path.
- [x] Campaign spec can be reused with different seeds.

## TDD tests

```text
tests/unit/campaigns/test_phase9_campaign_spec.py
```

Test cases:

```text
test_campaign_spec_loads_from_yaml
test_campaign_spec_requires_expected_arc_families
test_campaign_spec_requires_forbidden_behavior_rules
test_campaign_spec_rejects_exact_action_script_as_required_path
test_campaign_spec_is_deterministic_after_normalization
```

---

# Task 3 — Implement campaign runner

## Description

The normal scenario runner may execute bounded cases.

Phase 9 needs a campaign runner that tracks semantic progress over long runs.

It should wrap existing harness/kernel behavior, not replace it.

## Proposed runner

```python
class CampaignRunner:
    def run(
        self,
        campaign_spec: CampaignSpec,
        profile: RuntimeProfile,
    ) -> CampaignResult:
        ...
```

## Output

```python
@dataclass(frozen=True)
class CampaignResult:
    campaign_id: str
    final_state: AuthoritativeState
    entity_arc_reports: tuple[EntityArcReport, ...]
    world_arc_reports: tuple[WorldArcReport, ...]
    semantic_scorecard: CampaignScorecard
    performance_summary: Mapping[str, object]
```

## Checklist

- [x] Runner uses existing kernel/harness.
- [x] Runner records semantic events.
- [x] Runner records route-family transitions.
- [x] Runner records memory/knowledge/progression changes.
- [x] Runner records world pressure changes.
- [x] Runner outputs campaign report JSON.
- [x] Runner can run with feature flags on/off.
- [x] Runner remains deterministic under fixed seed.

## TDD tests

```text
tests/integration/campaigns/test_phase9_campaign_runner.py
```

Test cases:

```text
test_campaign_runner_executes_small_campaign
test_campaign_runner_outputs_entity_arc_reports
test_campaign_runner_outputs_world_arc_reports
test_campaign_runner_is_deterministic_for_same_seed
test_campaign_runner_can_disable_new_life_logic_by_feature_flag
```

---

# Task 4 — Implement life-arc classifier

## Description

You need a classifier that summarizes what kind of life path an entity followed.

This should use traces/events, not hidden labels.

## Initial arc families

```text
cautious_growth
risky_growth
craft_growth
information_growth
combat_growth
party_growth
recovery_loop
failed_adventurer
stagnant
world_avoidance
death_arc
```

## Example classification

```text
cautious_growth:
  - avoided high danger after warning/loss
  - selected recovery/preparation
  - completed safer route later

craft_growth:
  - detected equipment gap
  - learned/used recipe
  - gathered/kept materials
  - crafted/equipped upgrade

information_growth:
  - unknown fact detected
  - asked source
  - followed lead
  - verified/contradicted information
```

## Proposed service

```python
class LifeArcClassifier:
    def classify(
        self,
        entity_id: int,
        trace: EntityTrace,
    ) -> EntityArcReport:
        ...
```

## Checklist

- [x] Classifier uses event/trace evidence.
- [x] Entity can have multiple arc labels.
- [x] `stagnant` is detected if no meaningful progress/change.
- [x] `death_arc` is valid if entity dies after traceable decisions.
- [x] Arc classification includes evidence event IDs.
- [x] Classifier does not inspect hidden world truth.
- [x] Classifier is deterministic.

## TDD tests

```text
tests/unit/campaigns/test_phase9_life_arc_classifier.py
```

Test cases:

```text
test_craft_growth_arc_detected_from_trace
test_information_growth_arc_detected_from_trace
test_party_growth_arc_detected_from_trace
test_failed_adventurer_arc_detected_from_death_with_prior_decisions
test_stagnant_arc_detected_when_no_meaningful_change
test_arc_report_contains_evidence_event_ids
```

---

# Task 5 — Implement behavior-change proof detector

## Description

This is the most important Phase 9 task.

A life arc is only meaningful if past experience changes future behavior.

Examples:

```text
lost to wolf
-> later avoids wolf or seeks help

learned iron source
-> later travels to iron source

crafted better weapon
-> later accepts harder combat

heard danger rumor
-> later avoids or scouts region

partner abandoned entity
-> later rejects same partner
```

## Proposed model

```python
@dataclass(frozen=True)
class BehaviorChangeProof:
    entity_id: int
    cause_event_id: str
    later_event_id: str
    change_kind: str
    explanation: str
    confidence: float
```

## Service

```python
class BehaviorChangeProofDetector:
    def detect(
        self,
        entity_trace: EntityTrace,
    ) -> tuple[BehaviorChangeProof, ...]:
        ...
```

## Checklist

- [x] Detects combat loss -> later avoidance/help.
- [x] Detects information learned -> later route change.
- [x] Detects upgrade -> later harder objective.
- [x] Detects betrayal -> later partner rejection.
- [x] Detects world warning -> later route avoidance.
- [x] Requires temporal ordering.
- [x] Requires evidence before and after.
- [x] Avoids claiming causality without trace support.

## TDD tests

```text
tests/unit/campaigns/test_phase9_behavior_change_proof_detector.py
```

Test cases:

```text
test_loss_then_avoidance_creates_behavior_change_proof
test_info_learned_then_route_change_creates_proof
test_upgrade_then_harder_quest_creates_proof
test_betrayal_then_partner_rejection_creates_proof
test_same_action_without_later_change_does_not_create_proof
test_proof_requires_temporal_order
```

---

# Task 6 — Implement route-diversity analyzer

## Description

If 30 entities all make identical choices, the system is still shallow.

Phase 9 should measure diversity.

Diversity should come from:

```text
traits
class
knowledge
memory
world scarcity
risk tolerance
social trust
resource access
```

Not pure random noise.

## Metrics

```text
unique_route_families_used
route_family_distribution
trait_to_route_correlation
class_to_route_correlation
world_pressure_to_route_change
stagnant_entity_ratio
repeated_failure_ratio
```

## Proposed service

```python
class RouteDiversityAnalyzer:
    def analyze(
        self,
        entity_arc_reports: tuple[EntityArcReport, ...],
    ) -> RouteDiversityReport:
        ...
```

## Checklist

- [x] Counts route family distribution.
- [x] Detects identical-behavior collapse.
- [x] Detects stagnant entities.
- [x] Detects repeated failure loops.
- [x] Reports trait/class correlations.
- [x] Reports whether world pressure changed routes.
- [x] Does not require every entity to be unique.
- [x] Output is deterministic.

## TDD tests

```text
tests/unit/campaigns/test_phase9_route_diversity_analyzer.py
```

Test cases:

```text
test_route_diversity_counts_multiple_route_families
test_identical_behavior_collapse_is_flagged
test_stagnant_entity_ratio_is_reported
test_repeated_failure_loop_is_reported
test_trait_to_route_correlation_is_reported
```

---

# Task 7 — Implement semantic campaign scorecard

## Description

Phase 9 needs a scorecard that evaluates life quality.

Not pass/fail only.

## Proposed score dimensions

```text
self_model_usage
route_decision_quality
combat_learning
information_learning
reward_conversion
cooperation_usage
world_feedback_usage
behavior_change_proofs
route_diversity
forbidden_behavior_count
stagnation_ratio
performance_budget
```

## Example

```yaml
semantic_scorecard:
  self_model_usage: pass
  route_decision_quality: pass
  combat_learning: partial
  information_learning: pass
  reward_conversion: pass
  cooperation_usage: partial
  world_feedback_usage: pass
  behavior_change_proofs: 18
  route_diversity_score: 0.72
  stagnant_entity_ratio: 0.12
  forbidden_behavior_count: 0
  verdict: pass
```

## Checklist

- [x] Scorecard separates semantic failure from performance failure.
- [x] Scorecard reports partial pass.
- [x] Scorecard reports evidence.
- [x] Scorecard reports forbidden behaviors.
- [x] Scorecard reports stagnant entities.
- [x] Scorecard reports route diversity.
- [x] Scorecard reports behavior-change proofs.
- [x] Scorecard writes machine-readable JSON.

## TDD tests

```text
tests/unit/campaigns/test_phase9_semantic_campaign_scorecard.py
```

Test cases:

```text
test_scorecard_passes_when_required_semantic_proofs_exist
test_scorecard_fails_when_forbidden_behavior_detected
test_scorecard_flags_high_stagnation_ratio
test_scorecard_flags_missing_behavior_change_proofs
test_scorecard_reports_partial_pass_for_optional_arc
```

---

# Task 8 — Implement forbidden behavior detector

## Description

Long-run campaigns need safety rails.

Forbidden behavior examples:

```text
entity repeats same failed action forever
entity uses hidden knowledge
entity acts after death
entity directly mutates reward state
entity ignores critical survival need forever
entity attacks impossible target repeatedly
entity globally scans all facts every tick
entity knows far-away world pressure without exposure
```

## Proposed service

```python
class ForbiddenBehaviorDetector:
    def detect(
        self,
        campaign_trace: CampaignTrace,
    ) -> tuple[ForbiddenBehaviorReport, ...]:
        ...
```

## Checklist

- [x] Detects repeated same failed action loop.
- [x] Detects action after death.
- [x] Detects hidden knowledge usage.
- [x] Detects ignored critical survival need.
- [x] Detects impossible combat retry loop.
- [x] Detects omniscient world signal exposure.
- [x] Detects missing trace for major decision.
- [x] Reports evidence event IDs.

## TDD tests

```text
tests/unit/campaigns/test_phase9_forbidden_behavior_detector.py
```

Test cases:

```text
test_repeated_failed_action_loop_is_detected
test_action_after_death_is_detected
test_hidden_knowledge_usage_is_detected
test_critical_need_ignored_forever_is_detected
test_missing_decision_trace_is_detected
```

---

# Task 9 — Add campaign report generator

## Description

Human review matters.

You need readable reports, not only JSON.

Generate:

```text
campaign_summary.md
campaign_scorecard.json
entity_arcs.json
world_arcs.json
forbidden_behaviors.json
performance_summary.json
```

## Report sections

```text
campaign overview
feature flags
world pack
entity population
top entity arcs
world arcs
route diversity
behavior-change proofs
forbidden behaviors
performance summary
recommended failures to inspect
```

## Checklist

- [x] Markdown report generated.
- [x] JSON scorecard generated.
- [x] Entity arc summaries generated.
- [x] World arc summaries generated.
- [x] Top failures listed.
- [x] Reports include evidence event IDs.
- [x] Reports are deterministic enough for tests.
- [x] Reports avoid universal claims.

## TDD tests

```text
tests/unit/campaigns/test_phase9_campaign_report_generator.py
```

Test cases:

```text
test_report_generator_writes_markdown_and_json
test_report_contains_entity_arc_summary
test_report_contains_world_arc_summary
test_report_contains_forbidden_behavior_section
test_report_uses_bounded_language
```

---

# Task 10 — Add Phase 9 campaign scenarios

These are the real validation scenarios.

---

## Campaign 9.1 — First 30 days adventurers

```text
30 level-1 entities
same hometown
different classes/traits
basic adventure world
limited resources
several easy/hard quests
danger region
guide/guild/blacksmith/shop available
```

Expected:

```text
multiple route families appear
some entities grow through combat
some grow through crafting
some grow through information
some recover after failure
some die validly
some stagnate but under threshold
```

Forbidden:

```text
all entities choose same route
hidden knowledge use
infinite repeated failed action
no behavior-change proof
```

---

## Campaign 9.2 — Scarcity-driven divergence

```text
many entities need iron
old_mine iron nodes limited
blacksmith recipes depend on iron
```

Expected:

```text
early entities use iron craft route
scarcity emerges
later entities diversify:
  gather elsewhere
  ask info
  buy
  choose different quest
  defer
```

---

## Campaign 9.3 — Dangerous region reputation

```text
north_ruin kills several entities
rumor/guild warning spreads locally
```

Expected:

```text
cautious entities avoid
brave entities may still go
some entities seek party
some ask for information
clear-threat quest pressure emerges
```

---

## Campaign 9.4 — Cooperation career

```text
several hard objectives require help
entities have mixed trust and roles
some partners succeed
some abandon
```

Expected:

```text
trusted partners become preferred
bad partners get rejected later
survival can override leader objective
party route appears but not for everyone
```

---

## Campaign 9.5 — Knowledge-driven progression

```text
rare material needed for strong item
source unknown
guide gives partial lead
rumor may be wrong
observation can confirm/contradict
```

Expected:

```text
entities ask sources
some follow partial lead
some find contradiction
some choose alternate upgrade
knowledge changes route choice
```

---

## Campaign 9.6 — Combat learning career

```text
entities repeatedly encounter enemy types
some lose, some win
enemy hidden skill appears
```

Expected:

```text
loss changes future posture
known enemy uncertainty decreases
entities stop blindly engaging stronger targets
monsters can retreat
```

## Test file

```text
tests/integration/campaigns/test_phase9_life_arc_campaigns.py
```

## Checklist

- [x] Campaigns assert semantic scorecard.
- [x] Campaigns assert behavior-change proofs.
- [x] Campaigns assert route diversity.
- [x] Campaigns assert world-to-entity feedback.
- [x] Campaigns assert no forbidden behavior.
- [x] Campaigns are deterministic under fixed seed.
- [x] Campaigns do not assert exact action sequence.

---

# Task 11 — Add Phase 9 performance budget

## Description

Phase 9 runs many systems together.

Do not duplicate long-run certification, but add a semantic-campaign performance gate.

## Required metrics

```text
campaign_ticks
entity_count
avg_tick_ms
p95_tick_ms
semantic_event_count
trace_event_count
arc_classification_ms
scorecard_generation_ms
behavior_proof_count
forbidden_behavior_count
route_diversity_score
```

## Performance tests

```text
30 entities, 3000 ticks
100 entities, 3000 ticks
300 entities, 1000 ticks
feature flags OFF vs ON comparison
```

## Checklist

- [x] Campaign tracing has bounded memory.
- [x] Arc classification is post-run or cadence-limited.
- [x] Reports do not retain unbounded raw event history.
- [x] Feature flags OFF matches old baseline behavior.
- [x] Feature flags ON stays within agreed overhead.
- [x] Determinism stable under fixed seed.
- [x] Performance report written.

## Test file

```text
tests/perf/test_phase9_campaign_semantic_budget.py
```

---

# Phase 9 test files to add

```text
tests/unit/campaigns/test_phase9_campaign_spec.py
tests/unit/campaigns/test_phase9_life_arc_classifier.py
tests/unit/campaigns/test_phase9_behavior_change_proof_detector.py
tests/unit/campaigns/test_phase9_route_diversity_analyzer.py
tests/unit/campaigns/test_phase9_semantic_campaign_scorecard.py
tests/unit/campaigns/test_phase9_forbidden_behavior_detector.py
tests/unit/campaigns/test_phase9_campaign_report_generator.py

tests/integration/campaigns/test_phase9_campaign_runner.py
tests/integration/campaigns/test_phase9_life_arc_campaigns.py

tests/perf/test_phase9_campaign_semantic_budget.py

docs/test_coverage/phase9_life_arc_campaign_coverage.md
```

---

# Phase 9 non-goals

Do **not** implement these yet:

```text
full narrative generator
dialogue generation
hardcoded story scripts
romance/family life simulation
large political world simulation
complex settlement economy
full biography writing system
LLM-based story evaluator
```

Also do **not** duplicate existing tests for:

```text
long-run pure/runtime stability
determinism parity
arena combat stress
API observability
websocket behavior
release proof gate
basic certification envelope
```

Those are already covered in the uploaded test export.

---

# Phase 9 completion criteria

Phase 9 is done when this is true:

```text
The engine can run a multi-entity campaign
and prove that entities produce coherent life arcs:
they fail, learn, adapt, grow, cooperate, avoid, retry,
and respond to world changes over time.
```

Minimum proof:

```text
at least 5 major life-arc families are detected
behavior-change proofs exist
route diversity is above threshold
stagnation is below threshold
world pressure changes future decisions
hidden knowledge is not used
repeated failure loops are bounded
campaign overhead remains acceptable
```

---

# Priority Plan

## What changes in Phase 9

Before Phase 9:

```text
systems work individually
```

After Phase 9:

```text
systems combine into readable entity lives
```

## Implementation order

```text
1. Coverage audit
2. Campaign spec
3. Campaign runner
4. Life-arc classifier
5. Behavior-change proof detector
6. Route-diversity analyzer
7. Semantic scorecard
8. Forbidden behavior detector
9. Report generator
10. Campaign scenarios
11. Performance budget
```

## What to stop

Stop only asking:

```text
Did the simulation run?
Did the entity complete quest?
Did combat resolve?
Did memory remain bounded?
```

Start asking:

```text
Did this entity’s past change its future?
Did this entity’s route make sense from its knowledge?
Did the world change what later entities did?
Did entities diverge for explainable reasons?
```

## Consequence if ignored

You may build all previous phases correctly in isolation, but still fail the real target.

The engine may have:

```text
self-awareness
combat learning
beliefs
progression
cooperation
world emergence
```

but no proof that they combine into coherent life.

Phase 9 is where the engine proves it is no longer just a pile of systems.
