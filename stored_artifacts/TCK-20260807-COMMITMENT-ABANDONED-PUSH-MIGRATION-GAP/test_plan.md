---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# Test Plan: TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP

Shared test file with the sibling ticket: `tests/unit/observability/test_event_shapers_agency.py`
(16 tests total). This ticket's own `commitment_abandoned`-half tests:

| Test | Behavior verified |
|---|---|
| `test_agency_registry_contains_agency_shaper` | Registry wiring (shared) |
| `test_run_shadow_shapers_default_includes_agency_events` | Default delivers commitment_abandoned |
| `test_run_shadow_shapers_explicit_off_excludes_agency_events` | Rollback path |
| `test_run_shadow_shapers_shadow_mode_constructs_but_excludes` | SHADOW constructs-only |
| `test_run_shadow_shapers_on_mode_includes_agency_events` | Explicit ON delivers |
| `test_agency_shaper_independent_of_quest_flag` | Independent of `ENABLE_PUSH_EVENT_SHAPERS_QUEST` |
| `test_commitment_abandoned_emitted_on_abandoned_transition_not_survival` | Correct emission, correct payload |
| `test_commitment_abandoned_not_emitted_for_survival_category` | SURVIVAL classification suppressed |
| `test_commitment_abandoned_not_emitted_for_non_abandonment_transition` | Non-ABANDONED transitions ignored |
| `test_commitment_abandoned_uses_reconstructed_hp_from_combat_update` | hp reconstruction correctly applies same-tick delta |
| `test_commitment_abandoned_no_event_when_no_strategic_update` | No-op without a strategic update |

## Regression coverage
`tests/unit/observability/` full suite (952 tests), `tests/unit/config/test_phase10_feature_flags.py`,
`tests/simulation_quality/` (excluding the pre-existing unrelated `test_grade_regression.py`).

## Real-kernel-adjacent verification
Real `AuthoritativeState`/`StateUpdate`/`StrategicUpdate` (via `V2EntityBuilder`) with a project
transitioning `ACTIVE`→`ABANDONED` at hp=80/100: default delivers exactly 1
`commitment_abandoned` from the shaper (0 from extractor); explicit OFF delivers exactly 1 from
the extractor (0 from shaper).

## Results
`tests/unit/observability/test_event_shapers_agency.py`: 16/16 pass. Full
`tests/unit/observability/`: 952/952 pass. `tests/unit/config/test_phase10_feature_flags.py`:
7/7 pass. `tests/simulation_quality/` (excluding `test_grade_regression.py`): 1419 combined with
sibling-ticket regression sweep, all pass.
