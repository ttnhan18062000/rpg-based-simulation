# Review verdict

You implemented a **large amount of phase-shaped code**, but this is **not yet a complete implementation of the 10-phase roadmap**.

The core problem is architectural:

```text
Most phase modules exist.
Many unit tests pass.
But the enhanced phases are not actually wired into the authoritative engine loop.
```

So the current implementation is closer to:

```text
domain service prototypes + unit tests + partial scenario harness
```

not yet:

```text
engine-integrated cognition/world/action lifecycle
```

That distinction matters. If you claim this is “implemented,” you are fooling yourself. If you claim this is “a strong first implementation scaffold,” that is accurate.

---

# What I checked

I inspected both uploaded files:

* `src_export_impl.py`
* `test_export_impl.py`

I also extracted them into a temporary source/test tree and ran basic checks.

Results:

| Check                                      |                          Result |
| ------------------------------------------ | ------------------------------: |
| Python compile check                       |                          Passed |
| Targeted unit tests for new phase domains  |                      272 passed |
| Targeted phase 2–7 integration/perf subset |             54 passed, 1 failed |
| Targeted phase 8–10 subset                 |                       70 passed |
| Full pytest collection                     | Failed before running all tests |

The full collection failure is serious. Pytest collected 2314 tests but failed with 8 import-mismatch errors because duplicated test module filenames exist in different folders. Until that is fixed, you do **not** have a trustworthy full CI signal.

Examples of duplicate-name conflicts included:

```text
tests/integration/kernel/test_phase10_replay.py
vs
tests/engine/test_phase10_replay.py

tests/unit/social/test_social_bonds.py
vs
tests/social/test_social_bonds.py

tests/world/test_camp_lifecycle.py
vs
tests/unit/world/test_camp_lifecycle.py
```

---

# High-level phase audit

|    Phase | Status        | Verdict                                                                                                        |
| -------: | ------------- | -------------------------------------------------------------------------------------------------------------- |
|  Phase 1 | Partial       | Registries/providers exist, but scenario runner is fake/mocked and providers are not truly state-driven enough |
|  Phase 2 | Strongest     | Self-model components/services exist and are reasonably tested                                                 |
|  Phase 3 | Partial       | Adventure route schema/scoring exists, but route generation is not properly fed by live world opportunities    |
|  Phase 4 | Partial       | Combat engagement modules exist, but performance fails and engine integration is weak                          |
|  Phase 5 | Partial       | Information/belief modules exist, but assimilation persistence looks suspicious                                |
|  Phase 6 | Partial       | Progression/conversion logic exists, but likely not live-loop integrated                                       |
|  Phase 7 | Partial       | Cooperation logic exists, but mostly service-level, not proven as a life-loop behavior                         |
|  Phase 8 | Partial       | World emergence modules exist, but mostly synthetic-event driven                                               |
|  Phase 9 | Weak as proof | Campaign tests use injected semantic events; not proof of emergent life arcs                                   |
| Phase 10 | Partial       | Budget/cache/dirty scheduler utilities exist, but not enforcing the real enhanced stack                        |

---

# Critical finding 1 — New phases are not wired into the authoritative pipeline

The authoritative pipeline still shows the older phase graph: trust boundary, actor validity, contracts, blacksmith, action routing, movement, interaction, world dynamics, quest rewards, shop, resource transactions, evolution, strategic intelligence, near-death hardening, lifecycle, groups, capacity enforcement. I did not find the new Phase 2–10 domain phases wired into that authoritative path. 

That means modules such as:

```text
SelfModelUpdatePhase
AdventureDecisionPhase
CombatEngagementPhase
InformationBeliefPhase
ProgressionConversionPhase
CooperationPhase
WorldEmergencePhase
```

may exist, but they are not yet part of the actual engine tick lifecycle.

This is the biggest gap.

You have built side engines, not yet a unified engine.

---

# Critical finding 2 — Phase 1 scenario runner is not a real TDD harness yet

The `ScenarioRunner` currently simulates a deterministic loop that always emits:

```text
selected_route_family = defer_with_reason
reason = world_capability_not_fully_implemented_yet
provider_calls = 0
```

That is a placeholder behavior, not a real scenario runner. 

This violates the point of Phase 1.

Phase 1 was supposed to prove:

```text
world exposes meaningful choices
entity sees options
route families emerge from real provider/action/world state
```

Current behavior proves only:

```text
the scenario runner can write a scorecard file
```

That is not enough.

---

# Critical finding 3 — Phase 2 is the best implemented phase

`SelfModelBundle` exists and groups:

```text
SelfAwarenessComponent
NeedInterpretationComponent
CapabilityEstimateComponent
KnowledgeModelComponent
```

It is explicitly treated as derived/debug-oriented rather than authoritative mutation source, which is the correct direction. 

`SelfAssessmentService` and `SelfModelUpdatePhase` also exist, with deterministic threshold-based logic for weaknesses, stress, confidence, and self-model orchestration. 

This phase is structurally aligned with the roadmap.

Main remaining problem:

```text
It is not clearly wired into the live authoritative tick path.
```

So Phase 2 is implemented as a good service layer, but not proven as an always-available engine capability.

---

# Critical finding 4 — Phase 3 route logic exists, but live opportunity flow is broken

The Phase 3 route schema and scoring exist. `RouteFamily`, `AdventureRouteOption`, `AdventureDecisionResult`, and subjective scoring are implemented. 

`AdventureRouteGenerator` also consumes `Opportunity` objects and maps opportunity kinds like:

```text
gather_resource
buy_item
craft_item
repair_gear
ask_information
rest_inn
```

into route families. 

But the issue is this:

```text
The phase-level integration appears to call the route generator without real opportunities.
```

So the generator can map opportunities, but the engine phase does not yet prove:

```text
world providers -> opportunities -> route generator -> route scorer -> project/objective -> action intent
```

That means Phase 3 is currently more of a decision service than a working adventure loop.

---

# Critical finding 5 — Phase 4 has a real performance failure

The Phase 4 perf test expects combat engagement over 100 entities to stay under 5 ms. The test itself encodes that strict target. 

My local targeted run measured:

```text
11.2147 ms
```

So Phase 4 currently fails its own performance pillar.

This is not minor. Combat engagement can become the worst all-vs-all explosion risk in the whole design.

The likely fix is not “micro-optimize Python.” The likely fix is architectural:

```text
use spatial/sensory candidate caps
do not evaluate all nearby pairs blindly
cache subjective estimates per target window
skip entities without relevant combat trigger
```

---

# Critical finding 6 — Phase 5 information assimilation likely has a persistence bug

`InformationBeliefPhase` processes pending responses and calls `InformationAssimilationService.assimilate(...)`, but the entity update appears to reattach `actor.self_model` rather than the updated knowledge model. The comment says:

```text
Re-attach updated self-model components later in engine loop
```

but from the visible snippet, that later reattachment is not proven. 

This is dangerous because it can create a false-positive test situation:

```text
unit service returns updated knowledge
but engine phase does not persist it
```

You need an integration test that proves:

```text
information response at tick T
-> ApplyPath / authoritative update
-> entity.self_model.knowledge contains new fact at tick T+1
```

Without that, Phase 5 is not real.

---

# Critical finding 7 — Phase 8 exists, but is not proven as live emergence

`WorldEmergencePhase` exists and orchestrates:

```text
event aggregation
regional pressure
scarcity
opportunity pressure
quest seeds
rumor seeds
service pressure
entity signal bridging
```

That matches the roadmap structurally. 

But the key missing proof is:

```text
real entity actions produce events
events produce world pressure
world pressure changes future entity route decisions
```

Most visible Phase 8 logic is still synthetic-event-friendly. That is okay for unit tests, but not enough for claiming emergence.

The missing test is not:

```text
death aggregate increases danger pressure
```

The missing test is:

```text
heroes die in live run
-> danger pressure rises
-> later cautious hero avoids region because it heard/observed that pressure
```

---

# Critical finding 8 — Phase 9 is mostly a report/classifier layer, not true life-arc proof

The Phase 9 tests inject handcrafted `CampaignEvent`s like:

```text
recipe_learned
item_crafted
combat_loss
avoided_danger
quest_completed
died
```

to prove the classifier can recognize arcs. 

The classifier itself detects arc types from event labels like `party_formed`, `quest_completed`, `item_crafted`, `died`, and marks stagnant arcs when there are too few meaningful events. 

That is useful, but it does **not** prove the engine generated those arcs.

Right now Phase 9 proves:

```text
given story-like events, the reporter can classify story-like arcs
```

It does not prove:

```text
the simulation naturally produced those events through phases 1–8
```

This is the difference between a semantic analyzer and a life simulation.

---

# Critical finding 9 — Phase 10 utilities exist, but are not controlling the real system

Budget manager and cache strategy exist. The budget manager tracks ms, entities, provider calls, and trace events; the cache strategy supports bounded LRU-like behavior and invalidation for resources/shop/service/region signals. 

That is good.

But the hard question is:

```text
Are these budgets actually governing Phase 2–8 execution inside the authoritative tick?
```

From the pipeline evidence, not yet.

So Phase 10 is currently:

```text
optimization utility implementation
```

not yet:

```text
rollout hardening of the full enhanced stack
```

---

# Biggest structural issue

You have two systems now:

## Existing real engine

```text
AuthoritativeApplyPipeline
PhaseDependencyGraph
StrategicIntelligenceSystem
WorldDynamicsSystem
ShopSystem
BlacksmithSystem
CombatResolutionSystem
InteractionSystem
```

## New enhanced domain stack

```text
SelfModelUpdatePhase
AdventureDecisionPhase
CombatEngagementPhase
InformationBeliefPhase
ProgressionConversionPhase
CooperationPhase
WorldEmergencePhase
CampaignRunner
Optimization utilities
```

They are not yet fused.

That is the real gap.

The codebase now has the shape of the roadmap, but not the execution contract.

---

# Test suite problems

## 1. Full pytest cannot be trusted yet

Full collection fails due duplicate module basenames. This must be fixed before judging coverage.

Until then, any claim like:

```text
all tests pass
```

is false.

## 2. Too many tests are service-level

Many tests prove:

```text
service returns expected dataclass
scorer changes score
classifier detects label
provider returns option
```

Those are useful, but they do not prove closed-loop behavior.

## 3. Several scenario tests are synthetic

The worst examples are:

```text
ScenarioRunner always returns defer_with_reason
Campaign tests inject semantic events
```

Those are scaffolds, not simulation proofs.

## 4. Performance tests use wall-clock thresholds

Tests like:

```text
duration_ms < 5.0
```

are fragile unless the environment is controlled. The fact that Phase 4 fails at 11.2 ms is still meaningful, but long-term you need budget counters plus algorithmic assertions:

```text
targets_considered_per_entity <= cap
no all-pairs scan
provider_calls <= budget
```

not only wall-clock time.

---

# Phase-by-phase status table

| Phase | Implementation status                        | Test status                   | Real gap                                                                        |
| ----: | -------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------- |
|     0 | Existing hardening is strong                 | Many old tests exist          | Need verify original critical fixes: train skill field, town scorer, enum drift |
|     1 | Content/registries/providers partially exist | Some tests exist              | Scenario runner is fake; providers not truly live-state driven                  |
|     2 | Good model/services                          | Strong unit coverage          | Not clearly integrated into tick lifecycle                                      |
|     3 | Route/scoring/service exists                 | Unit/scenario-like tests pass | Opportunities not fed from live providers into phase                            |
|     4 | Combat engagement modules exist              | Unit tests pass, perf fails   | Candidate filtering/perf + pipeline integration missing                         |
|     5 | Info/belief modules exist                    | Unit tests likely pass        | Assimilation persistence into entity state suspicious                           |
|     6 | Progression/conversion modules exist         | Service tests likely pass     | Not proven in live reward→conversion loop                                       |
|     7 | Cooperation modules exist                    | Service tests likely pass     | Not proven as actual party-life behavior                                        |
|     8 | Emergence modules exist                      | Synthetic/event tests pass    | Not proven from real entity actions to future decisions                         |
|     9 | Campaign analyzer exists                     | Injected-event tests pass     | Does not prove emergent life arcs                                               |
|    10 | Budget/cache/scheduler utilities exist       | Unit tests pass               | Not governing full enhanced engine stack                                        |

---

# Most important fixes now

## 1. Fix pytest collection first

Do this before anything else.

Rename duplicate test files or add proper package `__init__.py` isolation where appropriate.

Until full collection works, you are flying blind.

## 2. Wire phases into the real engine behind feature flags

Add the new phases to a controlled integration path:

```text
OFF
SHADOW
ON
STRICT
```

Do not immediately mutate real state. Start with SHADOW.

Expected proof:

```text
Feature OFF -> old hash unchanged
Feature SHADOW -> old hash unchanged, diagnostics emitted
Feature ON -> behavior changes deterministically
```

## 3. Replace fake scenario runner

The current Phase 1 runner must stop emitting fixed `defer_with_reason`.

It should run the real kernel or a real minimal engine loop.

Minimum requirement:

```text
provider_calls > 0
route_family comes from actual decision
forbidden behavior detector inspects real trace
```

## 4. Make Phase 1 providers read actual world state

`ResourceOpportunityProvider` cannot be mostly registry-driven.

It must inspect:

```text
state.resource_nodes
remaining_charges
position/region
known facts
visibility/knowledge
depletion
distance/proximity
```

Otherwise entities are choosing from a static catalog, not a living world.

## 5. Connect Phase 1 -> Phase 3

Adventure decision must consume opportunities from:

```text
ResourceOpportunityProvider
ServiceOpportunityProvider
InformationProvider
QuestOpportunityProvider
```

Right now Phase 3 has a route generator that can accept opportunities, but the phase integration is not proving that flow.

## 6. Fix Phase 4 performance

The combat engagement phase must avoid O(n²)-style target consideration.

Hard requirements:

```text
max targets considered per entity
spatial index
hostility/relevance filter
cooldown/reassessment cadence
skip entities with no trigger
```

## 7. Fix Phase 5 persistence

Add an integration test:

```text
pending information response
-> InformationBeliefPhase
-> AuthoritativeApplyPipeline / ApplyPath
-> entity knowledge updated next tick
```

If that fails, fix the update path.

## 8. Convert Phase 8 and 9 tests from injected events to live traces

Injected events are acceptable for classifier unit tests.

They are not acceptable for claiming life simulation.

You need at least one campaign where:

```text
real combat loss
real knowledge acquisition
real reward conversion
real cooperation
real world pressure
```

produce the life arc.

---

# Concrete next test targets

Add these tests next, in this order:

```text
test_full_pytest_collection_has_no_import_mismatch

test_feature_shadow_mode_preserves_authoritative_hash

test_self_model_phase_runs_in_shadow_without_state_mutation

test_adventure_phase_receives_nonempty_world_opportunities

test_resource_provider_uses_state_resource_nodes_and_depletion

test_information_belief_phase_persists_assimilated_knowledge

test_combat_engagement_targets_considered_are_capped

test_scenario_runner_uses_real_kernel_not_fixed_defer

test_campaign_life_arc_uses_real_events_not_injected_events

test_world_emergence_changes_future_route_decision
```

These tests will expose the real integration gaps fast.

---

# Brutal conclusion

You did a lot of work, but you are currently at this stage:

```text
phase-shaped implementation scaffold
```

not:

```text
complete integrated enhanced RPG simulation engine
```

The code is not trash. The direction is good. The unit-level foundation is much better than nothing.

But the biggest danger now is self-deception:

```text
Because the modules exist and unit tests pass,
you may think the phases are implemented.
```

They are not implemented until they participate in the live engine loop and produce behavior changes in real scenarios.

---

# Priority Plan

## What must change in mindset

Stop measuring progress by number of modules or unit tests.

Measure progress by closed-loop proof:

```text
world state
-> entity interpretation
-> decision
-> action intent
-> authoritative execution
-> consequence
-> memory/world update
-> future behavior change
```

If a phase does not complete that loop, it is partial.

## Immediate actions

1. Fix pytest collection errors.
2. Add feature flags and SHADOW integration for Phase 2–8.
3. Replace fake `ScenarioRunner` behavior.
4. Make Phase 1 providers state-driven.
5. Feed real opportunities into Phase 3.
6. Fix Phase 4 performance failure.
7. Fix/verify Phase 5 knowledge persistence.
8. Add one real end-to-end campaign proving Phase 1–6 together before touching more features.

## Stop

Stop adding more phase modules.

Stop writing more injected-event campaign tests as proof.

Stop accepting service-level unit tests as implementation completion.

## Consequence if ignored

You will end up with a codebase that looks extremely advanced but behaves like the old engine plus a diagnostics layer.

That is the worst outcome:

```text
high complexity
high maintenance cost
low actual behavior improvement
```

The next milestone should not be “more logic.”

It should be:

```text
prove the enhanced stack changes real entity lives inside the actual engine loop
```
