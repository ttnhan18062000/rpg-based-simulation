---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260824-WIRE-ORPHANED-MECHANISMS
phase: done
date: 2026-08-24
tags: [social, cognition, progression]
---

# TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Title
Wire the Remaining Orphaned Mechanisms

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Nine originally-orphaned mechanisms exist (two now folded into affection-gating and M3 Reproduction), leaving seven still needing wiring per the atlas's checklist. The author wants those seven orphaned mechanisms wired into real production call sites.

## Scope
- Wire `InformationNeedDetector.detect_and_generate()` into `CognitionDomain.execute_brain()`, inserted between the existing Emotional Appraisal step and Tactical Intent step (the closest literal match to the docstring's "after project eval, before route scoring" given `execute_brain()`'s actual two-step structure — see Assumptions/Open Questions for why the docstring's literal wording does not match reality)
- Duplicate-check `EvolutionService` (`src/progression/evolution.py`) against the already-live `EvolutionSystem` (`src/engine/evolution.py`, same goblin_0/1/2 mechanism); confirmed dead duplicate (zero callers, zero tests, conflicting thresholds) — fold/delete, do not wire
- Duplicate-check `SabotageAction` (`src/town/sabotage.py`) against the live `BuildingSabotageSystem` (`src/engine/sabotage.py`); confirmed dead duplicate at the class level (zero production callers, same purpose via a different damage formula) — fold/delete, do not wire as a second competing path
- Call `EmotionUpdateService.update_on_event()` (`src/domains/emotion/emotion_service.py`) from `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py`) for the `"near_death"` event kind — the only one of its 6 recognized event kinds with a confirmed real detection site; distinct from the unrelated `AppraisalSystem.evaluate_emotional_state()`
- Call `compute_elder_attribute_update()` (`src/domains/demographics/cohort.py`) once per aging-cycle tick from `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py`), gated on the forward bracket-entry transition edge (mirroring `LifeStageService.is_forward_transition()`'s existing guard) so the delta modifier applies exactly once, not every tick
- Call `consequence_events.py`'s `evaluate_social_consequence()` at episode/entity-spawn time in `CampaignOrchestrator._build_initial_state()` (`src/domains/campaigns/orchestrator.py`), read-only, with returned events emitted via the existing `world_events_add` authoritative-observability pattern (per `DemographicCycleService.process_demographics()`'s precedent)

## Out of Scope
- MemoryUpdatePhase wiring -- owned by TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING (C11), same gap/file/consumer, must not be duplicated here
- GeneticsSystem wiring -- owned by M3 Reproduction, entirely out of this M1 epic
- Any consolidation of TCK-20260425-PH7-M4-SABOTAGE's historical claims beyond flagging the discrepancy
- **`ReputationUpdateService.process_witnessed_event()` wiring (originally item 5 of this ticket's Scope) — split out to TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING.** Investigation found zero real production event source for any of its 3 recognized `event_kind` strings (`successful_escort`, `betrayal`, `clear_camp`): no `ESCORT` `QuestKind` exists, and the closest analog (`CooperationLearningService.learn()`'s betrayal branch) is itself dead code, imported but never called. Wiring it meaningfully requires new domain logic (a new `QuestKind`, or activating dead cooperation code) that exceeds a call-site-insertion "wiring" ticket's scope — see Assumptions/Open Questions for the atomicity-decision rationale.

## Acceptance Criteria
- [x] InformationNeedDetector.detect_and_generate() is called from CognitionDomain.execute_brain() at the documented insertion point, verified via a real Kernel run
- [x] SabotageAction is either wired with a distinct purpose from the live BuildingSabotageSystem, or deleted/merged as a confirmed duplicate, with the duplicate check documented
- [x] EvolutionService wiring is preceded by an explicit duplicate-check against the live EvolutionSystem, proving additive or fold/delete
- [x] EmotionUpdateService.update_on_event() is called from a real event-emission site, distinct from AppraisalSystem.evaluate_emotional_state()
- [x] compute_elder_attribute_update() is called once per aging-cycle tick at the real aging-cycle call site (LifecycleSystem.resolve_lifecycle() — see Scope note on why this differs from the ticket's original get_age_bracket() premise)
- [x] consequence_events.py's function is called at a real social/episode encounter entry point, read-only, emitted via the authoritative pipeline
- [ ] ~~ReputationUpdateService.process_witnessed_event() is called from a real witnessed-event site~~ — split out to TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING (see Out of Scope)

## Related Tickets
- TCK-20260619-E42A-INFO-NEED
- TCK-20260619-E43E-CONSEQUENCE-EVENTS
- TCK-20260619-E52C-AGE-ADVANCEMENT
- TCK-20260425-PH7-M4-SABOTAGE
- TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
- TCK-20260618-AUDIT-D11-DEAD
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE
- TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
- TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING (child ticket split out during this ticket's Investigate phase — see Out of Scope)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/emotion/emotion_service.py
- src/domains/emotion/__init__.py
- src/progression/evolution.py
- src/engine/evolution.py
- src/engine/pipeline.py
- src/engine/domain/cognition_extras.py
- src/engine/domain/cognition.py
- src/systems/social_systems/consequence_events.py
- src/town/sabotage.py
- src/engine/sabotage.py
- src/domains/commitment/reputation.py
- src/domains/commitment/__init__.py
- src/domains/demographics/cohort.py
- src/core/cognition.py
- src/systems/social_systems/reputation.py
- src/engine/cognition.py

## Assumptions / Open Questions
- **RESOLVED — EvolutionService duplicate-check**: confirmed dead duplicate of the already-live EvolutionSystem. `EvolutionService` (src/progression/evolution.py) has zero callers and zero tests anywhere; `EvolutionSystem` (src/engine/evolution.py) is pipeline-wired (pipeline.py:337) and integration-tested (test_goblin_evolution proves the identical goblin_0->goblin_1 transition + gear). The two disagree on the second-stage threshold (20 vs. 25) — an internal inconsistency that would break determinism if both were ever wired. Disposition: fold/delete src/progression/evolution.py, do not wire.
- **RESOLVED — SabotageAction duplicate-check**: confirmed dead duplicate at the class level of the live, pipeline-wired BuildingSabotageSystem. Zero production callers found for SabotageAction (only 3 direct-call unit tests); BuildingSabotageSystem is wired at pipeline.py:290 and integration-tested. Disposition: fold/delete src/town/sabotage.py, do not wire as a second competing damage path.
- **RESOLVED — TCK-20260425-PH7-M4-SABOTAGE historical-closure discrepancy**: NOT a stale/false closure. That ticket's actual Scope/AC only claimed `SabotageAction.apply()` + ApplyPath trauma-propagation integration (both still true today) — it never claimed pipeline/intent wiring. A later system (BuildingSabotageSystem, "Phase 8") superseded SabotageAction as the production path without anyone retiring it. The 2026-04-25 closure was accurate for what it delivered; today's zero-caller reality is a later drift, not a falsified closure. Flagged per Out of Scope, not reconciled further.
- **RESOLVED — atomicity decision: split.** Investigation (staging_artifacts/TCK-20260824-WIRE-ORPHANED-MECHANISMS/investigation.md, "Atomicity Recommendation") found the 7 original mechanisms are not homogeneous enough to land atomically: items 2/3 are deletions (different shape of change than insertion), item 5 (ReputationUpdateService) has no real production event source for any of its 3 recognized event kinds and needs new domain logic beyond a call-site insertion, and item 7 (consequence_events) is an episode-boundary insertion rather than a per-tick pipeline phase (different verification tooling) but is still concretely achievable with existing evidence. Orchestrator decision: land items 1, 2 (delete), 3 (delete), 4, 6, 7 in this ticket; split item 5 (ReputationUpdateService) into TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING, since it is the one item where satisfying the AC as literally scoped would require inventing new domain logic (a new QuestKind, or reactivating dead CooperationLearningService code) not authorized by this ticket's original scope — a genuine "missing critical context" case, not a simple wiring gap.
- **RESOLVED — InformationNeedDetector insertion-point ambiguity**: the docstring's literal "after project eval, before route scoring" does not exist inside `CognitionDomain.execute_brain()` (that function only does Emotional Appraisal -> Tactical Intent; project eval/route scoring live at the pipeline/StrategicIntelligenceSystem/LeadRoutingSystem level). Decision: insert between the existing Emotional Appraisal and Tactical Intent steps inside `execute_brain()` — the closest literal match to the documented intent, and keeps AC #1's literal "called from CognitionDomain.execute_brain()" wording satisfiable.
- **RESOLVED — EmotionUpdateService event-kind scope**: only `"near_death"` (via NearDeathHardeningPhase.apply()) has a confirmed real detection site among the 6 recognized event kinds. Wiring only that one satisfies AC #4's "from a real event-emission site" wording; the other 5 event kinds remain unwired pending their own future detection-site tickets (not fabricated here).
- **RESOLVED — compute_elder_attribute_update cadence risk**: the function returns per-tick deltas, not idempotent set-values. Must be gated on the forward bracket-entry transition edge (mirroring `LifeStageService.is_forward_transition()`'s existing guard for the parallel life_stage field), not applied unconditionally every tick, or elder attributes would compound toward zero.
- `layer: engine` chosen because the majority of wiring call sites (`src/engine/domain/*`, `src/engine/pipeline.py`, `src/engine/evolution.py`, `src/engine/sabotage.py`, `src/engine/cognition.py`) sit in the deterministic tick/domain-execution loop; the mechanisms themselves span cognition, social, progression, and demographics domains but the unifying scope is wiring them into that engine execution path

## Implementation Notes

- **Step 1 (InformationNeedDetector)**: `CognitionDomain.execute_brain()` now imports
  `InformationNeedDetector` and calls `detect_and_generate(entity, state.tick)` between the
  Emotional Appraisal and Tactical Intent blocks; the previously-hardcoded final-line
  `strategic=None` now reads `strategic=info_update`. Also updated `CognitionDomain`'s class
  docstring System Boundary #1 to note the additive-only `INFORMATION_SEEKING` proposal path
  (doc-only, per architecture-review's required fix).
- **Step 2 (EvolutionService)**: deleted `src/progression/evolution.py` in full after re-confirming
  zero non-test/non-doc references via grep. `EvolutionSystem` (`src/engine/evolution.py`) remains
  the sole live path.
- **Step 3 (SabotageAction)**: deleted `src/town/sabotage.py` in full after re-confirming zero
  production references. Retargeted all 3 tests in `tests/unit/world/test_building_sabotage.py`
  from `SabotageAction.apply()` to `BuildingSabotageSystem.resolve()`, driven by a `SABOTAGE`
  `TaskUpdate` intent rather than a direct method call, matching the live pipeline's actual entry
  point.
- **Step 4 (EmotionUpdateService)**: `NearDeathHardeningPhase.apply()` now builds
  `base_cognition = entity_update.cognition_bundle_set if ... else entity.cognition` (handles the
  same-tick collision with an earlier phase like `MemoryUpdatePhase`), calls
  `EmotionUpdateService.update_on_event(base_cognition.subjective.emotion, "near_death")`, and sets
  both `combat=hardened_combat` and `cognition_bundle_set=new_cognition` together in one `replace()`.
  Also updated the phase's own docstring "Effect:" list for accuracy (doc-only).
- **Step 5 (compute_elder_attribute_update)**: `LifecycleSystem.resolve_lifecycle()` now calls
  `compute_elder_attribute_update()` when `target_stage == LifeStage.ELDER`, reusing the existing
  `is_forward_transition()` edge already computed for `life_stage_set` (no new gate invented), and
  merges the result onto `ent_upd` via `EntityUpdate.merge()`.
- **Step 6 (consequence_events)**: `CampaignOrchestrator._build_initial_state()` now iterates
  `sorted(entities.keys())` (deterministic order, per architecture-review), calls
  `evaluate_social_consequence(entity, f"faction_{entity.identity.faction}", self._state, tick=0)`
  per entity, and emits each returned event via `self._event_recorder.record()` directly (guarded by
  `if self._event_recorder is not None`) — not through `world_events_add`, since
  `evaluate_social_consequence()` returns `SimulationEvent`, not `WorldEvent`, and this constructor
  call site has no `StateUpdate`/`ApplyPath` merge step available.
- **Step 7 (docs/parity)**: updated `WORLD-DEMO-004` (world_dynamics.yaml), `STRAT-229`
  (strategic_cognition.yaml), and `SOC-CROSS-EP-005` (social_narrative.yaml) with the new call-site
  evidence and test paths; added a new `SOC-248` entry for `EmotionUpdateService`; added an "Elder
  Attribute Modifiers" subsection to `docs/mechanics/01_entity_anatomy.md` §5. `STRAT-229` and the
  new `SOC-248` entry were written via `tools/parity_ledger_writer.py`'s `write_entry()`;
  `WORLD-DEMO-004` and `SOC-CROSS-EP-005` needed direct surgical edits instead because their legacy
  multi-hyphen ids fail the writer's `^[A-Z]+-[0-9]{3}$` id-pattern validation (pre-existing, unrelated
  to this change) — see plan.md's Deviations section. Ran `python3 tools/parity_index.py build`
  by hand afterward to keep the derived index in sync with the two direct edits.

## Test Summary

All new/updated tests pass (verified with `.venv/bin/python3 -m pytest`, repo venv):
- `tests/integration/scenarios/test_information_seeking_wiring.py` — 1 passed (real Kernel-run
  wiring proof for Step 1; loops up to 100 ticks to cover governor-mode-dependent ENTITY_BRAIN
  scheduling cadence — see plan.md Deviations).
- `tests/unit/progression/test_evolution.py` — 2 passed (unmodified, proves EvolutionSystem
  remains sole live path).
- `tests/unit/world/test_building_sabotage.py` — 3 passed (retargeted to BuildingSabotageSystem).
- `tests/integrity/test_logic_guards.py` — 8 passed + 2 xfailed (pre-existing xfails unrelated to
  this ticket), including the 3 new Step 2/3 guard tests
  (`test_evolution_service_deleted_and_not_reintroduced`,
  `test_sabotage_action_deleted_and_not_reintroduced`,
  `test_building_hp_reduction_traces_to_single_authoritative_source`).
- `tests/unit/engine/test_near_death_hardening_emotion.py` — 3 passed (new file: emotion-update
  proof, cognition_bundle_set-shape guard, same-tick collision preservation).
- `tests/unit/world/test_demographics.py` — 59 passed (57 pre-existing + 2 new elder-wiring tests:
  `test_elder_attribute_modifier_applies_once_on_bracket_transition`,
  `test_elder_attribute_modifier_does_not_reapply_every_tick`).
- `tests/integration/scenarios/test_social_memory.py` — 4 passed (2 pre-existing + 2 new:
  `test_consequence_events_fire_at_episode_entity_spawn`,
  `test_consequence_events_noop_without_event_recorder`).
- Regression sweeps also run clean: `tests/unit/cognition/` (124 passed), `tests/unit/social/`
  (215 passed, 1 deselected slow), `tests/unit/domains/emotion/` (7 passed),
  `tests/unit/engine/ tests/unit/world/ tests/unit/progression/` (493 passed, 1 skipped, 3
  deselected slow), `tests/integration/pipeline/test_strategic_cadence.py` (4 passed),
  `tests/integration/observability/test_cognition_*` (8 passed).
- `tests/architecture/` — 1 pre-existing failure unrelated to this ticket
  (`test_systems_do_not_import_engine_outside_pinned_exceptions`, flags
  `src/systems/strategic_systems/redirection.py:11`'s `src.engine.cadence` import — reproduces
  identically with all this ticket's changes stashed out; not touched).
- `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
  — 1 pre-existing failure unrelated to this ticket (`live_missing == 1330` vs hardcoded expectation
  `1332`; reproduces identically with all this ticket's changes stashed out — a documented drift
  pattern per CLAUDE.md's CI Triage guidance, not something this ticket caused or should silently
  fix).

## Files Changed

- `src/engine/domain/cognition.py` (Step 1)
- `src/progression/evolution.py` — deleted (Step 2)
- `src/town/sabotage.py` — deleted (Step 3)
- `tests/unit/world/test_building_sabotage.py` — retargeted (Step 3)
- `src/engine/pipeline_phases/hardening.py` (Step 4)
- `tests/unit/engine/test_near_death_hardening_emotion.py` — new (Step 4)
- `src/systems/lifecycle_systems/lifecycle.py` (Step 5)
- `tests/unit/world/test_demographics.py` — extended (Step 5)
- `src/domains/campaigns/orchestrator.py` (Step 6)
- `tests/integration/scenarios/test_social_memory.py` — extended (Step 6)
- `tests/integration/scenarios/test_information_seeking_wiring.py` — new (Step 1)
- `tests/integrity/test_logic_guards.py` — 3 new guard tests (Steps 2/3)
- `docs/parity_ledger/world_dynamics.yaml` (Step 7 — WORLD-DEMO-004)
- `docs/parity_ledger/strategic_cognition.yaml` (Step 7 — STRAT-229)
- `docs/parity_ledger/social_narrative.yaml` (Step 7 — SOC-CROSS-EP-005 + new SOC-248)
- `docs/mechanics/01_entity_anatomy.md` (Step 7 — new Elder Attribute Modifiers subsection)
- `docs/simulation/domains/emotion_contract.md` — Document-Update phase: cited the confirmed `near_death` call site (`NearDeathHardeningPhase.apply()`) in place of generic "Engine event handlers" phrasing
- `staging_artifacts/TCK-20260824-WIRE-ORPHANED-MECHANISMS/plan.md` — added Deviations section

## Completion Summary

Implemented all 7 steps of plan.md: wired `InformationNeedDetector` into
`CognitionDomain.execute_brain()` (fixing the `strategic=None` hardcode that would have silently
discarded it) and updated its docstring's System Boundary #1; deleted the two confirmed dead
duplicates `EvolutionService` and `SabotageAction`, retargeting `SabotageAction`'s 3 tests to
`BuildingSabotageSystem.resolve()`; wired `EmotionUpdateService.update_on_event()` into
`NearDeathHardeningPhase.apply()` for the `"near_death"` event kind with correct same-tick
`cognition_bundle_set` collision handling; wired `compute_elder_attribute_update()` into
`LifecycleSystem.resolve_lifecycle()` gated on the existing forward-transition edge so it fires
exactly once per entity; wired `consequence_events.evaluate_social_consequence()` into
`CampaignOrchestrator._build_initial_state()` in deterministic sorted-entity order, emitting via
`self._event_recorder.record()`; and updated the 4 parity-ledger entries plus the Mechanics Bible's
elder-attribute-modifier formula. All new/extended tests pass; two pre-existing, unrelated test
failures were confirmed (via git-stash reproduction) to predate this ticket's changes and were left
untouched. `ReputationUpdateService` wiring remains out of scope, split to
TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING as already recorded in this ticket's Assumptions
section.
