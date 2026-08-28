---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260824-WIRE-ORPHANED-MECHANISMS
artifact_type: test_plan
tags: [social, cognition, progression]
---

# Test Plan — TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**Unit — cognition**
- `tests/unit/cognition/test_information_seeking.py` (all classes, especially
  `TestInformationNeedDetectorNormalFlow`, `TestInformationNeedDetectorEdgeCases`,
  `TestLeadRoutingSystem`, `TestLeadContradiction`) — must not regress when
  `detect_and_generate()` gains a real caller.
- `tests/unit/cognition/test_phase2_*.py` (5 files) — unrelated self-model services sharing
  `src/engine/domain/` — regression guard against accidental import/order changes in
  `cognition.py`/`cognition_extras.py`.

**Unit — domains/emotion**
- `tests/unit/domains/emotion/test_phase16_emotion_update_service.py` — direct unit coverage of
  `EmotionUpdateService.update_on_event()`; must keep passing unchanged (pure function, no
  signature change expected).
- `tests/unit/domains/emotion/test_phase16_emotional_model.py`,
  `test_phase16_recovery_readiness_service.py`, `test_phase16_recovery_state_model.py`,
  `test_phase16_habit_bias_service.py`, `test_phase16_habit_memory_model.py`,
  `test_phase16_opportunity_cost_evaluator.py`.

**Unit — domains/commitment**
- `tests/unit/domains/commitment/test_phase15_reputation_update.py` — direct unit coverage of
  `ReputationUpdateService.process_witnessed_event()`.
- `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`,
  `test_phase15_commitment_pressure.py`, `test_phase15_route_impact.py`.

**Unit — domains/demographics**
- `tests/unit/world/test_demographics.py` — all `compute_elder_attribute_update` and
  `get_age_bracket` tests (`test_elder_modifier_reduces_combat_effectiveness`,
  `test_non_elder_returns_none`, `test_elder_knowledge_bonus_positive`,
  `test_elder_mortality_modifier_reduces_vitality_endurance`,
  `test_elder_modifier_entity_id_preserved`), plus migration/density/cohort tests in the same
  file.

**Unit — progression**
- `tests/unit/progression/test_evolution.py` (`test_goblin_evolution`,
  `test_no_evolution_before_threshold`) — must keep passing unmodified; this is the proof that
  `EvolutionSystem` remains the sole live goblin evolution path if `EvolutionService` is
  deleted/folded.
- `tests/unit/progression/test_lifecycle.py`, `test_leveling.py`, `test_leveling_veterancy.py`,
  `test_phase8_progression.py`, `test_progression_v2.py`, `test_rpg_advancement.py`,
  `test_progression_quests.py`, `test_breakthroughs.py`, `test_classes_loadouts.py`,
  `test_genetics.py` — broad regression net for anything touching `src/progression/`.

**Unit — world / building sabotage**
- `tests/unit/world/test_building_sabotage.py` (`test_building_sabotage_damage`,
  `test_building_destruction_and_trauma`, `test_sabotage_proximity_validation`) — currently
  exercises `SabotageAction.apply()` directly; if `SabotageAction` is deleted/folded, these tests
  must be updated or removed as part of that specific sub-change (not silently left failing).

**Unit — social**
- `tests/unit/social/test_social_memory.py`, `test_social_memory_service.py`,
  `test_betrayal_consequence.py`, `test_reputation_learning.py`, `test_appraisal_logic.py` —
  regression guard for anything adjacent to consequence events / reputation / emotion appraisal.

**Unit — engine**
- `tests/unit/engine/test_lifecycle_supervisor.py` — adjacent to `LifecycleSystem.resolve_lifecycle()`,
  the target insertion point for `compute_elder_attribute_update`.
- `tests/unit/engine/test_objective_evaluator.py`, `test_information_intent_execution_phase.py` —
  adjacent to `CognitionDomain`/lead routing.

**Integration**
- `tests/integration/pipeline/test_strategic_cadence.py` — exercises `BuildingSabotageSystem`
  directly; must not regress from any `SabotageAction` duplicate-resolution change.
- `tests/integrity/test_logic_guards.py` — exercises `BuildingSabotageSystem`; also likely the
  home for a determinism/architecture guard against two competing sabotage paths.
- `tests/integration/scenarios/test_demographics.py` — full demographic cycle scenario.
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`,
  `test_phase16_emotion_recovery_habit_scenarios.py` — full-scenario coverage adjacent to items
  4/5.
- `tests/integration/scenarios/test_social_memory.py` — full social-memory scenario, adjacent to
  item 7.
- `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` — end-to-end cognition
  hierarchy; must not regress from `execute_brain()` insertion (item 1).
- `tests/integration/observability/test_cognition_report_section.py`,
  `test_cognition_pattern_mining_flow.py`, `test_cognition_snapshot_artifact.py`,
  `test_cognition_diff_events.py` — observability surfaces reading cognition state; regression
  guard against `cognition_bundle_set` changes leaking unexpected fields into event
  extraction/reporting.

## New Tests Required

Per acceptance criteria, one entry per mechanism actually wired (duplicate-check items produce a
different kind of test — see notes):

1. **InformationNeedDetector wiring (AC #1)**
   - Test name: `test_information_need_detector_fires_from_execute_brain` (or equivalent, matching
     whatever insertion point planning resolves per investigation Risk 1)
   - Category: integration (real Kernel/tick run, per AC's explicit "verified via a real Kernel
     run" wording — a unit-level call of `execute_brain()` in isolation is not sufficient to meet
     this AC)
   - Verifies: an entity with a qualifying `UnknownFact` (`priority > 0.5`,
     `seeking_project_id is None`) produces an `INFORMATION_SEEKING` project after a real
     `Kernel`/pipeline tick, not just after a direct `detect_and_generate()` call.
   - Location: `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` (extend) or a
     new `tests/integration/scenarios/test_information_seeking_wiring.py`.

2. **EvolutionService/EvolutionSystem duplicate-check (AC #2/#3 duplicate-check requirement)**
   - Test name: `test_evolution_service_removed_or_never_diverges_from_evolution_system` (shape
     depends on chosen disposition — delete vs. fold)
   - Category: architecture guard (if `EvolutionService` is deleted: a guard test asserting
     `src/progression/evolution.py` no longer exists or exports nothing conflicting; if folded: a
     parity test asserting `EvolutionSystem`'s thresholds match whatever `EvolutionService` used to
     claim, so the two can never silently diverge again)
   - Verifies: no second, independently-triggerable goblin-evolution code path exists with
     different thresholds than `EvolutionSystem`.
   - Location: `tests/unit/progression/test_evolution.py` (extend) or
     `tests/integrity/test_logic_guards.py` (if framed as an architecture guard).

3. **SabotageAction/BuildingSabotageSystem duplicate-check**
   - Test name: `test_no_duplicate_building_damage_path` / update
     `tests/unit/world/test_building_sabotage.py` to target whichever class remains live.
   - Category: architecture guard + unit (whichever tests survive the fold/delete decision)
   - Verifies: building HP reduction has exactly one authoritative source of truth in the pipeline
     (`BuildingSabotageSystem`, per the investigation's recommended disposition); if
     `SabotageAction`'s ATK-scaling is folded into `BuildingSabotageSystem`, a new test proves
     damage now scales with attacker ATK there instead of the flat 50.
   - Location: `tests/unit/world/test_building_sabotage.py`, `tests/integrity/test_logic_guards.py`.

4. **EmotionUpdateService wiring (AC #4)**
   - Test name: `test_near_death_hardening_updates_emotional_model`
   - Category: integration
   - Verifies: `NearDeathHardeningPhase.apply()` (or wherever planning lands the call), when it
     detects a near-death survival, produces an `EntityUpdate` with `cognition_bundle_set` carrying
     an `EmotionalModel` with `fear`/`panic` increased and `confidence` decreased per
     `EmotionUpdateService.update_on_event(model, "near_death")`'s existing deltas — and that this
     is distinct from, and does not replace, `AppraisalSystem.evaluate_emotional_state()`'s
     existing per-tick output.
   - Location: `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py`
     (extend) or a new test alongside `tests/unit/world/` hardening-phase tests (check for an
     existing `test_hardening.py`/near-death test file first; none was found in this investigation
     under `tests/unit/engine/` or `tests/unit/world/` — likely needs a new file, e.g.
     `tests/unit/engine/test_near_death_hardening_emotion.py`).

5. **ReputationUpdateService wiring (AC #5)**
   - Test name: TBD — depends entirely on planning's resolution of investigation Risk 2 (no real
     event source currently exists for any of the 3 recognized `event_kind` strings). At minimum:
     `test_reputation_update_fires_on_<chosen event source>`.
   - Category: integration
   - Verifies: whatever real detection site planning selects (e.g., quest completion via
     `QuestResolutionSystem.enforce()`, or an activated `CooperationLearningService.learn()`
     betrayal branch) produces a `cognition_bundle_set` `EntityUpdate` carrying an updated
     `PublicReputationProfile.labels`.
   - Location: `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`
     (extend).
   - **Flag for planner**: if planning cannot identify a real event source without expanding scope
     (e.g. adding a new `QuestKind.ESCORT`), this AC may need re-scoping rather than a test being
     written against a synthetic/unreachable trigger.

6. **compute_elder_attribute_update wiring (AC #6)**
   - Test name: `test_elder_attribute_modifier_applies_once_on_bracket_transition` and
     `test_elder_attribute_modifier_does_not_reapply_every_tick`
   - Category: integration + regression-prone-path (must explicitly cover the cadence risk from
     investigation Risk 3)
   - Verifies: (a) an entity crossing `age_ticks >= 7000` for the first time receives the elder
     `AttributeUpdate` deltas exactly once, via `LifecycleSystem.resolve_lifecycle()`; (b) an
     entity that is already elder and remains elected does NOT receive the deltas again on a
     subsequent tick (guards against the compounding-modifier bug flagged in investigation).
   - Location: `tests/unit/world/test_demographics.py` (extend) or
     `tests/integration/scenarios/test_demographics.py`.

7. **consequence_events wiring (item 7, no explicit numbered AC but in Scope)**
   - Test name: `test_consequence_events_fire_at_episode_entity_spawn`
   - Category: integration (episode-level, not a per-tick Kernel test — matches the
     architecturally distinct insertion point found in investigation)
   - Verifies: `evaluate_social_consequence()` is called for entities carried into a new episode
     via `CampaignOrchestrator._build_initial_state()` (or wherever planning lands it), that
     returned events are emitted through the authoritative/observability event path (not silently
     dropped), and that the function remains read-only (no mutation of `campaign_state` or the
     newly-built `AuthoritativeState` beyond the emitted events).
   - Location: `tests/integration/scenarios/test_social_memory.py` (extend).

## Scoped Pytest Commands

```bash
# Cognition (item 1)
pytest tests/unit/cognition/ tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py -m "not slow"

# Progression / evolution duplicate-check (item 2)
pytest tests/unit/progression/ -m "not slow"

# Building sabotage duplicate-check (item 3)
pytest tests/unit/world/test_building_sabotage.py tests/integration/pipeline/test_strategic_cadence.py tests/integrity/test_logic_guards.py -m "not slow"

# Emotion domain (item 4)
pytest tests/unit/domains/emotion/ tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py -m "not slow"

# Commitment/reputation domain (item 5)
pytest tests/unit/domains/commitment/ tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py -m "not slow"

# Demographics / elder modifiers (item 6)
pytest tests/unit/world/test_demographics.py tests/integration/scenarios/test_demographics.py -m "not slow"

# Social memory / consequence events (item 7)
pytest tests/unit/social/ tests/integration/scenarios/test_social_memory.py -m "not slow"

# Engine-level regression net (lifecycle + cognition adjacency)
pytest tests/unit/engine/ -m "not slow"

# Observability adjacency (cognition_bundle_set leakage guard)
pytest tests/integration/observability/test_cognition_report_section.py tests/integration/observability/test_cognition_pattern_mining_flow.py tests/integration/observability/test_cognition_snapshot_artifact.py tests/integration/observability/test_cognition_diff_events.py -m "not slow"
```

Never `pytest tests/` — always scoped per domain per the Testing Rule.

## Anti-Drift Test Guards

- **Determinism guard**: any new integration test for items 1/4/6 must run the same scenario twice
  with the same seed and assert identical resulting state (or reuse an existing determinism
  fixture if the repo has one under `tests/integrity/`) — these are exactly the kind of
  event-triggered, delta-applying changes that could silently introduce non-determinism if the
  insertion point reads any non-deterministic ordering (e.g., dict iteration without `sorted()`).
- **Single-source-of-truth guard for sabotage** (item 3): a guard test in
  `tests/integrity/test_logic_guards.py` asserting that building HP changes trace to exactly one
  system per tick — prevents a future regression where both `SabotageAction` and
  `BuildingSabotageSystem` end up wired simultaneously.
- **Single-source-of-truth guard for evolution** (item 2): a guard test asserting
  `src/progression/evolution.py` is either absent or, if kept, is provably never imported by
  `src/engine/pipeline.py` or any phase file — prevents silent re-introduction of the conflicting
  20-vs-25 threshold duplicate.
- **`cognition_bundle_set` shape guard**: a test asserting that when
  `EmotionUpdateService`/`ReputationUpdateService` wiring emits `cognition_bundle_set`, only the
  intended sub-field (`.emotion` or `.public_reputation`) actually changed relative to the
  entity's prior `CognitionModel` — guards against an accidental full-bundle overwrite clobbering
  unrelated cognition state (self-model, knowledge, commitments) that a whole-bundle-replace
  update type makes easy to get wrong.
- **Elder-modifier idempotency guard** (item 6): explicit regression test (see New Tests Required
  #6b) proving the modifier does not reapply on subsequent ticks — this is the single most
  concrete gameplay-breaking regression risk identified in this investigation and must not be
  covered only implicitly by an integration scenario that happens not to run long enough to expose
  it.
- **`ESCORT` quest-kind scope guard** (item 5, if planning introduces a new `QuestKind`): if
  wiring `ReputationUpdateService` requires adding `QuestKind.ESCORT`, a guard test confirming this
  addition doesn't change existing `HUNT`/`GATHER`/`EXPLORE`/`LIBERATE`/`BOUNTY` quest resolution
  behavior (enum value stability, no renumbering of existing `auto()` values in ways that could
  affect serialized quest state).
