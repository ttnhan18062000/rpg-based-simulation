# Test Plan — TCK-20260629-SIMQ-EMIT-NARRATIVE

**Ticket:** TCK-20260629-SIMQ-EMIT-NARRATIVE  
**Date:** 2026-06-30  
**Test file (new):** `tests/unit/observability/test_event_extractor_narrative.py`  
**Supplementary:** `tests/unit/campaigns/test_narrative_ledger.py` (additions)  
**Supplementary:** `tests/unit/engine/test_scenario_runtime_service.py` (additions)

---

## Regression Surface (existing tests that must pass)

All of the following must continue to pass with no changes after this ticket:

| Test file | What it covers | Command scope |
|---|---|---|
| `tests/simulation_quality/test_narrative_scorer.py` | NarrativeScorer for all 10 event types | `pytest tests/simulation_quality/test_narrative_scorer.py` |
| `tests/unit/campaigns/test_narrative_ledger.py` | NarrativeLedger record/query/to_jsonl, TC-D1–TC-D15 | `pytest tests/unit/campaigns/test_narrative_ledger.py` |
| `tests/unit/engine/test_scenario_runtime_service.py` | ScenarioRuntimeService start/pause/resume/step/abort/stall | `pytest tests/unit/engine/test_scenario_runtime_service.py` |
| `tests/unit/observability/test_event_extractor_social_faction.py` | 53 social/faction event extractor tests | `pytest tests/unit/observability/test_event_extractor_social_faction.py` |
| `tests/unit/observability/test_event_extractor_economy.py` | 15 economy event extractor tests | `pytest tests/unit/observability/test_event_extractor_economy.py` |
| `tests/unit/observability/test_event_extractor_world.py` | World/region event extractor tests | `pytest tests/unit/observability/test_event_extractor_world.py` |
| `tests/simulation_quality/test_quality_hub_event_translation.py` | 34 event translation tests incl. quest mappings | `pytest tests/simulation_quality/test_quality_hub_event_translation.py` |
| `tests/unit/observability/test_event_extractor_simq.py` | SimQ-specific extractor baseline tests | `pytest tests/unit/observability/test_event_extractor_simq.py` |

Critical regression guard: `quest_started` / `quest_completed` / `quest_failed` must
NOT be double-emitted. The existing path is:
`EventExtractor` → `QuestEvent(status="started")` → `QualityHub._translate()` → `quest_started`.
No new `quest_started` emission should be added.

---

## New Tests Required (per AC)

**File:** `tests/unit/observability/test_event_extractor_narrative.py`

Follow the naming convention of `test_event_extractor_social_faction.py`:
- Test IDs as `N-01` through `N-XX` in docstrings
- Use `_make_prior_state()` / `_make_current_state()` / `_make_update()` helpers
- Use `EventExtractor.extract(prior, current, update)` as the system under test
- Assert on `event.event_type` and `event.payload` keys

### Group A: chronicle_entry_created (NarrativeLedger wiring)

These tests go in `tests/unit/campaigns/test_narrative_ledger.py` as additions
(TC-D16 onward), not in the extractor test file, since the emission is at NarrativeLedger.

| ID | Test name | What it proves |
|---|---|---|
| TC-D16 | `test_record_emits_chronicle_entry_created_when_recorder_provided` | When `event_recorder` is injected and `record()` is called, `chronicle_entry_created` SimulationEvent is produced |
| TC-D17 | `test_record_no_emission_when_recorder_none` | When `event_recorder=None`, `record()` appends entry without error (None-safe) |
| TC-D18 | `test_chronicle_entry_payload_contains_entry_fields` | Emitted event payload includes `entry_id`, `event_type`, `significance`, `episode` from the NarrativeLedgerEntry |
| TC-D19 | `test_recorder_not_called_on_query` | `query()` does not trigger event_recorder regardless of recorder presence |

### Group B: world_emergence_event (EventExtractor from world_events_add)

| ID | Test name | What it proves |
|---|---|---|
| N-01 | `test_world_emergence_event_emitted_from_world_events_add` | `world_emergence_event` is extracted when `update.world_events_add` contains an emergence-category WorldEvent |
| N-02 | `test_world_emergence_event_payload_has_region_id` | Emitted event payload carries `region_id` from the WorldEvent |
| N-03 | `test_no_world_emergence_event_without_emergence_category` | Non-emergence WorldEvent categories do not produce `world_emergence_event` |

Note: exact `WorldEventCategory` value for emergence threshold must be confirmed by
implementer (see investigation Q1). Add a gap test `N-03b` with `pytest.skip(reason=
"world_emergence_event: no WORLD_EMERGENCE_THRESHOLD category in schema — requires
design decision on threshold definition")` if the category is not added.

### Group C: narrative_milestone

| ID | Test name | What it proves |
|---|---|---|
| N-04 | `test_narrative_milestone_emitted_on_first_war_declared` | When `war_declared` event fires (first occurrence), a `narrative_milestone` event with `payload["milestone"] == "first_war"` is also emitted |
| N-05 | `test_narrative_milestone_emitted_on_boss_spawned` | When `boss_spawned` fires, `narrative_milestone` with `payload["milestone"] == "first_boss_kill"` emitted |
| N-06 | `test_narrative_milestone_emitted_on_sovereignty_shift` | When `region_ownership_changed` fires from `SOVEREIGNTY_SHIFT` WorldEvent, `narrative_milestone` with `milestone == "first_sovereignty_transfer"` emitted |
| N-07 | `test_narrative_milestone_not_emitted_for_non_milestone_events` | Other event types do not produce `narrative_milestone` |

If "first occurrence" detection is handled by scorer rather than emitter (option d from
investigation), N-04/N-05/N-06 become straightforward: `narrative_milestone` fires on
every qualifying event, not just first. Document the chosen approach in the test docstring.

### Group D: scenario_objective events (ScenarioRuntimeService)

These tests go in `tests/unit/engine/test_scenario_runtime_service.py` as additions:

| ID | Test name | What it proves |
|---|---|---|
| S-01 | `test_scenario_stalled_emits_event_when_recorder_injected` | When `event_recorder` is provided and stall threshold crossed, `scenario_stalled` event is emitted |
| S-02 | `test_scenario_objective_met_emits_completed_event` | When `OBJECTIVE_MET` is reached, `scenario_objective_completed` event is emitted |
| S-03 | `test_scenario_objective_failed_emits_failed_event` | When `OBJECTIVE_FAILED` is reached, `scenario_objective_progressed` or `scenario_objective_completed` with failure payload is emitted |
| S-04 | `test_no_event_when_recorder_none` | None-safe: no AttributeError when recorder not provided |
| S-05 | `test_scenario_stalled_gap_test` | `pytest.skip` gap test: "scenario_objective_progressed requires discrete objective progress tracking not currently modeled in ObjectiveEvaluator — only binary met/failed/running states exist" |

Note: `scenario_objective_progressed` (incremental progress) is a gap: the
`ObjectiveEvaluator` only returns binary `RUNNING / OBJECTIVE_MET / OBJECTIVE_FAILED`.
There is no partial-progress concept in the current schema. S-05 documents this gap.

### Group E: hero_death_unrecorded (EventExtractor)

| ID | Test name | What it proves |
|---|---|---|
| N-08 | `test_hero_death_unrecorded_emitted_for_hero_kind_death` | When entity with `kind == "hero"` transitions `active=True` → `active=False` and no chronicle event appears in `world_events_add`, `hero_death_unrecorded` is emitted |
| N-09 | `test_hero_death_unrecorded_not_emitted_for_non_hero_kind` | Entity deaths with `kind != "hero"` do not produce `hero_death_unrecorded` |
| N-10 | `test_hero_death_unrecorded_payload_contains_entity_id` | Emitted event payload carries `entity_id` of the dying hero |
| N-11 | `test_hero_death_unrecorded_suppressed_when_chronicle_present` | If `world_events_add` contains a chronicle entry for the entity this tick, `hero_death_unrecorded` is NOT emitted (requires confirmation of chosen detection approach from Q4) |

Note: N-11 is conditional on the chosen implementation approach for Q4. If option (c)
(always emit) is chosen, replace N-11 with a gap test:
`pytest.skip("hero_death_unrecorded suppression requires chronicle entry tracking in
StateUpdate — not implemented; always emits on hero death")`.

### Group F: quest confirmation (AC validation — no new emission needed)

| ID | Test name | What it proves |
|---|---|---|
| N-12 | `test_quest_started_confirmed_via_translation` | `quest_event` with `status="started"` in existing extractor + translation table produces `quest_started` (regression + confirmation) |
| N-13 | `test_quest_completed_confirmed_via_translation` | Same for `status="completed"` → `quest_completed` |
| N-14 | `test_quest_failed_confirmed_via_translation` | Same for `status="failed"` → `quest_failed` |

These are regression-confirmation tests in the new file, not new behavior.

### Group G: architecture gap tests

| ID | Test name | What it proves |
|---|---|---|
| N-15 | `test_no_simq_import_in_world_emergence_phase` | `assert "simulation_quality" not in imports` of `src/domains/world_emergence/phase.py` |
| N-16 | `test_no_simq_import_in_lifecycle_system` | Same for `src/systems/lifecycle_systems/lifecycle.py` |
| N-17 | `test_no_simq_import_in_narrative_ledger` | Same for `src/domains/campaigns/narrative_ledger.py` |
| N-18 | `test_no_simq_import_in_scenario_runtime` | Same for `src/engine/scenario_runtime.py` |

---

## Scoped Pytest Commands

Run only the new narrative test file:
```
uv run --with pytest python3 -m pytest tests/unit/observability/test_event_extractor_narrative.py -v
```

Run narrative ledger additions:
```
uv run --with pytest python3 -m pytest tests/unit/campaigns/test_narrative_ledger.py -v
```

Run scenario runtime additions:
```
uv run --with pytest python3 -m pytest tests/unit/engine/test_scenario_runtime_service.py -v
```

Run full observability + SimQ regression surface:
```
uv run --with pytest python3 -m pytest tests/unit/observability/ tests/simulation_quality/ tests/unit/campaigns/test_narrative_ledger.py tests/unit/engine/test_scenario_runtime_service.py -v
```

Exclude slow integration tests:
```
uv run --with pytest python3 -m pytest tests/unit/observability/ tests/simulation_quality/ -m "not slow" -v
```

---

## Anti-Drift Test Guards

1. **Double-emission guard**: Confirm `quest_started/completed/failed` count in test
   output: no new `quest_*` emission paths must appear in the narrative extractor test.
   Add an explicit assertion in N-12/N-13/N-14 that EventExtractor emits `quest_event`
   (not `quest_started`) and that the translation layer is responsible for the rename.

2. **Import guard**: N-15 through N-18 assert that `src/simulation_quality/` is not
   imported in any of the four modified files. Run as importlib/AST check:
   ```python
   import ast, pathlib
   tree = ast.parse(pathlib.Path("src/domains/world_emergence/phase.py").read_text())
   imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
   assert not any("simulation_quality" in (m or "") for m in imports)
   ```

3. **NarrativeLedger None-safe guard**: TC-D17 must pass with `event_recorder=None`
   and confirm no `AttributeError` is raised. Use `pytest.raises` negation pattern.

4. **ScenarioRuntimeService None-safe guard**: S-04 passes when no recorder is
   provided — existing tests that construct `ScenarioRuntimeService(spec)` without
   recorder must not break.

5. **Parity ledger update guard**: After implementation, manually verify INFRA-247
   `divergence_note` is cleared (the gap is resolved) and SIMQ-CALIBRATED-001
   `v2_evidence` is updated to include NARRATIVE emit. Add a comment in the test file:
   `# Parity: INFRA-247 (chronicle_entry_created gap resolved), SIMQ-CALIBRATED-001 (update required)`
