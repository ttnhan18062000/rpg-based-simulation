---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-GRIEF-NEMESIS-REACHABILITY
artifact_type: test_plan
tags: [cognition, social, observability]
---

# Test Plan — TCK-20260824-GRIEF-NEMESIS-REACHABILITY

## Regression Surface

### unit

- `tests/unit/domains/campaigns/test_grief_urgency.py` — all 30 tests (importer injection/no-mutation/
  overwrite/source-naming for both `GriefUrgencyImporter` and `NemesisRelationImporter`;
  `_advance_grief_urgencies`/`_advance_nemesis_relations` detection/decay logic;
  `CampaignState` round-trip for `grief_urgencies`/`nemesis_relations`). Must keep passing
  unchanged — these lock in the existing episode-boundary contract that the mid-episode addition
  must not disturb.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — all 12 tests, especially
  `test_advance_state_extracts_entity_carry_forward`, `test_run_episode_appends_to_episode_history`,
  `test_alive_uses_lifecycle_active_not_combat_alive`, `test_state_module_has_no_engine_imports`
  (architecture guard — `CampaignState` must stay import-clean of `src.engine`/`src.core.state`).
- `tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py` — progression-plan wiring through
  `_build_initial_state()`; must not regress if `GriefUrgencyImporter`/`NemesisRelationImporter`'s
  internal shape changes.
- `tests/unit/domains/campaigns/test_narrative_ledger.py` — `_extract_narrative_entries()`
  conversion logic, including the `ENTITY_DEATH` → `entity_death` mapping (TC-D12 and related).
  Must keep passing to confirm the conversion logic itself is untouched even though its real-world
  producer path is a separate, pre-existing gap (see investigation.md).
- `tests/unit/domains/faction/test_siege_ledger.py`, `test_betrayal_ledger.py`, `test_diplomacy.py`
  — these import `CampaignOrchestrator`/`CampaignManifest` for unrelated faction-narrative
  scenarios; must not regress from any signature change to `GriefUrgencyImporter.apply()`/
  `NemesisRelationImporter.apply()`.
- `tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py`,
  `test_phase8_regional_pressure_model.py`, `test_phase8_world_emergence_boundary.py` — cover
  `WorldEventCategory.ENTITY_DEATH` consumers; must stay green untouched since this ticket does not
  add an `ENTITY_DEATH` `WorldEvent` producer (see investigation.md Anti-Drift Hazards — that would
  activate a currently-dormant `QuestOpportunityGenerator.from_threat_signal()` path, out of
  scope).
- `tests/unit/tools/test_simq_audit_gaps.py` — SimQ gap-detection tooling; relevant if a new
  event_type is added without full pillar wiring (would surface as a newly-detected gap, which is
  the correct outcome mid-implementation but must be closed by Verify).

### integration

- `tests/integration/scenarios/test_campaign_runtime.py` — all 4 tests, especially
  `test_narrative_ledger_populated_with_cross_episode_events` (exercises a real multi-episode
  `CampaignOrchestrator` run end-to-end) and `test_episode_history_accumulates`. These are the
  closest existing regression coverage for "does a real `run_episode()` call still work" and must
  keep passing after `ScenarioRuntimeService(spec, initial_state=..., event_recorder=...)` wiring
  changes at `orchestrator.py:172`.
- `tests/integration/campaigns/test_progression_planner_three_episode.py` — three-episode carry
  forward; sensitive to any change in `_build_initial_state()`'s call order or the importer
  contract.
- `tests/integration/scenarios/test_social_memory.py` — social memory export/import across
  episodes; the data source `_advance_grief_urgencies()`/`_advance_nemesis_relations()` read from.
- `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py`,
  `tests/integration/scenarios/test_phase8_world_emergence_scenarios.py` — must stay green
  (ENTITY_DEATH producer non-goal, same as unit-level guard above).

### arena-combat / SimQ

- `tests/perf/test_phase8_world_emergence_budget.py` — perf budget touching `ENTITY_DEATH`-tagged
  synthetic events; unaffected by this ticket but should be run once if the mid-episode trigger
  hooks into `event_extractor.py`'s per-tick loop (perf-sensitive hot path).
- `tests/tools/test_evaluate_simq_scenario_scope.py` — scenario-scope validation for
  `tools/evaluate_simq.py`; relevant if a new campaign-aware profile/run_key is added to
  `config/simulation_quality/corpus_registry.yaml` via `tools/generate_corpus_registry.py`.

## New Tests Required

Per acceptance criteria:

1. **AC1 — `CampaignOrchestrator.run_episode()` reachable via a real production entry point**
   - Test name: `test_<new_entry_point>_invokes_run_episode` (exact name depends on the chosen
     mechanism from plan.md — e.g. `test_calibrate_simq_campaign_profile_runs_multiple_episodes` if
     a `calibrate_simq.py` branch is chosen, or `test_campaign_runner_script_invokes_run_episode` if
     a small parallel script is chosen)
   - Category: integration
   - Verifies: the new entry point actually constructs a `CampaignManifest` with 2+ episodes and
     calls `CampaignOrchestrator.run_episode()` at least twice, producing a non-empty
     `episode_history` — i.e., this is not test scaffolding calling the orchestrator directly, but
     the same code path a real SimQ/production invocation would exercise.
   - Where: `tests/integration/` (exact path depends on chosen mechanism — e.g.
     `tests/integration/tools/test_calibrate_simq_campaign_mode.py` or
     `tests/integration/scenarios/test_campaign_reachability.py`)

2. **AC2 — new event_type(s) emitted via `SimulationEvent`, queryable by a SimQ pillar**
   - Test name: `test_grief_urgency_triggered_event_shape` / `test_nemesis_relation_formed_event_shape`
   - Category: unit
   - Verifies: the event class (or bare `SimulationEvent(event_type=...)` call, per the pattern
     chosen) has the correct `event_type`, `event_category`, `source_system`, and payload fields,
     following the `LegendaryArrivalEvent`/`KnownTraitorSpottedEvent` pattern
     (`src/observability/events.py:357-431`).
   - Where: `tests/unit/observability/test_events.py` (or wherever sibling social-consequence event
     tests live)
   - Test name: `test_<pillar>_scorer_scores_grief_urgency_triggered` /
     `test_<pillar>_scorer_scores_nemesis_relation_formed`
   - Category: unit
   - Verifies: the chosen `PillarScorer` subclass (`NarrativeScorer` or `SocialScorer`, per the
     ticket's own open decision) returns a non-`None` `ScoreRecord` with the correct `pillar`,
     `delta` (matching a new weight key added to `config/simulation_quality/scoring_weights.yaml`),
     and `tags` for the new event_type(s) — following the pattern of existing tests in
     `tests/simulation_quality/test_narrative_scorer.py` or
     `tests/simulation_quality/test_social_scorer.py` (confirmed to exist; extend the file matching
     the chosen pillar).
   - Where: `tests/simulation_quality/test_narrative_scorer.py` or
     `tests/simulation_quality/test_social_scorer.py` (exact file per chosen pillar)

3. **AC3 — in-episode `entity_death` causes grief-urgency concern injection within the same
   episode, via an authoritative-pipeline-compliant path**
   - Test name: `test_grief_urgency_importer_returns_strategic_update`
   - Category: unit
   - Verifies: the reconciled `GriefUrgencyImporter` (or its new mid-episode-facing method) returns
     a `StrategicUpdate(concerns_add_or_update=[...])` rather than a whole `EntityState`, for the
     new mid-episode call path — while the existing `apply()` used by `_build_initial_state()`
     keeps its current direct-`EntityState`-return contract and existing tests
     (`test_grief_importer_injects_social_threat_concern` etc.) keep passing unchanged.
   - Where: `tests/unit/domains/campaigns/test_grief_urgency.py` (extend existing file — same
     module under test)
   - Test name: `test_mid_episode_entity_death_triggers_grief_concern_via_apply_path`
   - Category: integration
   - Verifies: an end-to-end scenario where an ally-trusted entity dies mid-episode (via
     `event_extractor.py`'s `lifecycle.active` transition detection at line 483) results in a
     `ConcernState(kind=SOCIAL_THREAT)` appearing in the grieving entity's
     `entity.strategic.concerns` **within the same episode** (not requiring `run_episode()` to be
     called again), applied through `ApplyPath`/`StrategicPatch` — not via a direct `EntityState`
     mutation. Assert the update flowed through `StrategicPatch.apply()` (e.g. by checking
     `DirtySet`/dirty-entity tracking picked up the change, per the architecture-test requirement
     in CLAUDE.md: "verify... authoritative application path was used").
   - Where: `tests/integration/scenarios/test_campaign_runtime.py` (extend — same file already
     covers real multi-episode `CampaignOrchestrator` runs) or a new
     `tests/integration/campaigns/test_mid_episode_grief_trigger.py` if the existing file's fixture
     shape doesn't fit a mid-episode-death scenario cleanly.
   - Test name: `test_mid_episode_death_does_not_duplicate_episode_boundary_grief`
   - Category: integration
   - Verifies: when a death is caught mid-episode AND the episode later ends, the episode-boundary
     `_advance_grief_urgencies()` path does not double-inject a second, conflicting
     `GriefUrgencyModifier`/concern for the same death (dedup/idempotency check) — a likely
     regression seam once two trigger paths exist for what was previously a single one.
   - Where: `tests/integration/scenarios/test_campaign_runtime.py` or the same new file as above.

4. **Architecture guard — event_recorder wiring**
   - Test name: `test_run_episode_passes_event_recorder_to_scenario_runtime`
   - Category: architecture guard / unit
   - Verifies: `CampaignOrchestrator.run_episode()` constructs
     `ScenarioRuntimeService(spec, initial_state=..., event_recorder=self._event_recorder)` — i.e.
     the event recorder is no longer silently dropped at `orchestrator.py:172` (currently omitted;
     see investigation.md). Use a spy/mock `EventRecorder` and assert it received at least one
     event from the in-episode kernel run.
   - Where: `tests/unit/domains/campaigns/test_campaign_orchestrator.py` (extend existing file)

## Scoped Pytest Commands

```
# Campaign domain (unit + integration) — primary regression surface
pytest tests/unit/domains/campaigns/ tests/integration/scenarios/test_campaign_runtime.py \
  tests/integration/campaigns/ tests/integration/scenarios/test_social_memory.py -v

# Cross-domain callers of CampaignOrchestrator/CampaignManifest (faction narrative)
pytest tests/unit/domains/faction/test_siege_ledger.py \
  tests/unit/domains/faction/test_betrayal_ledger.py \
  tests/unit/domains/faction/test_diplomacy.py -v

# Observability event pattern (new event_type shape)
pytest tests/unit/observability/ -v

# SimQ pillar scoring (new event_type wiring)
pytest tests/simulation_quality/ -v

# World-emergence ENTITY_DEATH consumers — anti-drift guard, must stay untouched
pytest tests/unit/domains/world_emergence/ \
  tests/integration/domains/world_emergence/ \
  tests/integration/scenarios/test_phase8_world_emergence_scenarios.py -v

# SimQ tooling (if a new corpus profile/run_key is added)
pytest tests/tools/test_evaluate_simq_scenario_scope.py tests/unit/tools/test_simq_audit_gaps.py -v
```

Never `pytest tests/` — all commands above are scoped to the campaign domain, its direct
cross-domain callers, observability event/scoring, and the world-emergence anti-drift guard.

## Anti-Drift Test Guards

- `tests/unit/domains/campaigns/test_grief_urgency.py::test_grief_importer_does_not_mutate_original`
  and `::test_nemesis_importer_does_not_mutate_original` must keep passing unchanged — guards
  against the reconciliation work accidentally introducing in-place mutation on the
  `_build_initial_state()` path while adding the new `StrategicUpdate`-returning path.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py::test_state_module_has_no_engine_imports`
  must keep passing — guards against any new mid-episode trigger wiring accidentally introducing an
  `src.engine`/`src.core.state` import into `src/domains/campaigns/state.py` (the pure-data-model
  boundary documented in that file's own module docstring).
- New test `test_mid_episode_death_does_not_duplicate_episode_boundary_grief` (above) directly
  guards against the most likely scope-creep/regression seam: two trigger paths (mid-episode +
  episode-boundary) double-counting the same death.
- `tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py` and siblings (listed
  under Regression Surface) guard against this ticket accidentally wiring an `ENTITY_DEATH`
  `WorldEvent` producer as a side effect — a producer appearing would change aggregation counts
  these tests assert on with hand-constructed fixtures, an early warning signal even though these
  tests don't test production code paths directly.
- New architecture-guard test `test_run_episode_passes_event_recorder_to_scenario_runtime` (above)
  guards against a partial fix that adds a mid-episode trigger but forgets the event-recorder
  wiring prerequisite, which would make AC2 (event queryable by SimQ) silently unreachable despite
  AC3's concern-injection logic being correct.
- Existing `tests/simulation_quality/test_narrative_scorer.py`/`test_social_scorer.py` tests guard
  against the new event_type(s) being added to one pillar's `EVENT_TYPES` tuple without a
  corresponding `if et ==` branch, or vice versa (tuple entry without weight key would raise a
  `KeyError` at `ScoringWeights.__getitem__` — should be caught by whichever test exercises that
  scorer against `scoring_weights.yaml`).
