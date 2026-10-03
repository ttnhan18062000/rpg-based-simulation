---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# Test Plan: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION

## New tests — `tests/unit/observability/test_event_shapers_narrative.py` (13 tests)

| Test | Behavior verified |
|---|---|
| `test_quest_registry_contains_narrative_shaper` | Registry wiring |
| `test_run_shadow_shapers_default_includes_quest_events` | Default (flag absent) delivers quest_event |
| `test_run_shadow_shapers_explicit_off_excludes_quest_events` | Rollback path: explicit OFF suppresses shaper delivery |
| `test_run_shadow_shapers_shadow_mode_constructs_but_excludes` | SHADOW constructs but doesn't deliver |
| `test_run_shadow_shapers_on_mode_includes_quest_events` | Explicit ON delivers |
| `test_quest_shaper_independent_of_phase2_flag` | Phase 2 flag OFF doesn't suppress quest_event (own flag confirmed independent) |
| `test_quest_started_when_no_prior_quest` | New quest → `status="started"`, correct payload |
| `test_quest_status_transition_emits_event_with_payload` | Status transition → correct status string + payload |
| `test_no_event_when_quest_status_unchanged` | Same-status tick → no event |
| `test_non_quest_project_produces_no_event` | Non-`QuestState` project never mislabeled (same bug class as `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`) |
| `test_no_event_when_entity_has_no_strategic_update` | No `strategic` update → no event |
| `test_no_event_when_prior_entity_missing` | Missing prior entity → no event |
| `test_project_removal_does_not_emit_a_started_event_for_a_different_quest` | `_current_projects()` reconstruction correctness under removal |

## Updated tests

- `tests/unit/config/test_phase10_feature_flags.py`: `_DELIBERATE_ON_DEFAULT_FLAGS` gained
  `ENABLE_PUSH_EVENT_SHAPERS_QUEST`.

## Regression coverage
- `tests/unit/observability/` (full suite, 936 tests) — confirms the `MagicMock`-based existing
  `event_extractor.py` tests (which implicitly exercise the rollback path, same pattern as every
  prior migrated domain) are unaffected.
- `tests/simulation_quality/` (excluding `test_grade_regression.py`, a pre-existing, unrelated
  failure class — see below) — 460 tests.
- `tests/unit/quest/` — quest generator/evaluator tests, to confirm no interaction with the
  quest-generation work from earlier in this session.

## Pre-existing unrelated failure (disclosed, not caused by this ticket)
`tests/simulation_quality/test_grade_regression.py` has 53-54 failures comparing static,
pre-generated `data/calibration/*/quality_report.json` files against `grade_anchors.json`. These
tests read STATIC files, not live kernel output — this ticket's source diff cannot affect them.
Confirmed via `git stash` A/B: 54 failures + 1 error on the clean baseline (without this ticket's
changes) vs. 53 failures with them — same failure class, pre-existing calibration-data drift
unrelated to this ticket.

## Real-kernel-adjacent verification
Built a real `AuthoritativeState`/`StateUpdate`/`StrategicUpdate` (via `V2EntityBuilder`) with a
quest transitioning `ACTIVE`→`COMPLETED`, called `EventExtractor.extract()` and
`run_shadow_shapers()` directly in both default and explicit-OFF modes — confirmed exactly 1
`quest_event` delivered per mode, from the correct source (shaper in default, extractor in OFF),
zero double-fire.

## Results
`tests/unit/observability/`: 936/936 pass. `tests/simulation_quality/` (excluding the
pre-existing unrelated file): 460/460 pass. `tests/unit/config/test_phase10_feature_flags.py`:
7/7 pass.
