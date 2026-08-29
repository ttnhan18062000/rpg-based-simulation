---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION
artifact_type: test_plan
tags: [feature-flags, progression]
---

# Test Plan — TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION

## Regression Surface
This ticket does not change `ProgressionConversionPhase`, its constituent services, or the flag's
default (Out of Scope: "Actually flipping the flag's default"). The following existing tests must
keep passing unmodified — they are the full real Phase-6/flag-adjacent surface identified during
investigation, grouped by category:

**Unit — Phase-6 progression domain logic** (bypass the flag gate entirely; call
`ProgressionConversionPhase`/its services directly):
- `tests/unit/domains/progression/test_phase6_conversion_decision_service.py`
- `tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py`
- `tests/unit/domains/progression/test_phase6_conversion_option_generator.py`
- `tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py`
- `tests/unit/domains/progression/test_phase6_possession_understanding_service.py`
- `tests/unit/domains/progression/test_phase6_progression_boundary.py`
- `tests/unit/domains/progression/test_phase6_progression_events.py`
- `tests/unit/domains/progression/test_phase6_reward_interpretation_service.py`
- `tests/unit/domains/progression/test_phase6_reward_ledger_service.py`
- `tests/unit/entity/test_phase6_reward_ledger_component.py`

**Unit — observability, adjacent to (but not exercising) the flag**:
- `tests/unit/observability/test_event_extractor_equipment.py`
- `tests/unit/observability/test_event_extractor_progression.py`
- `tests/unit/observability/test_event_shapers_progression.py`

**Unit — the sibling dormant AP-allocation path (PROG-068/069, not this flag, but same divergence
family per DEV-004 — must not regress while this ticket is in flight)**:
- `tests/unit/quest/test_progression_regression.py`

**Integration — phase-level and flag-defaults gating**:
- `tests/integration/domains/progression/test_phase6_progression_conversion_phase.py`
- `tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py`
- `tests/integration/progression/test_allocate_ap_dormancy.py`
- `tests/integration/test_scenario_feature_flag_defaults.py`

**Performance**:
- `tests/perf/test_phase6_progression_conversion_budget.py`

**Feature-flag config sanity (whole-manager regression guard, not progression-specific but must
stay green since the trial run touches `FeatureFlagManager` overrides)**:
- `tests/unit/config/test_phase10_feature_flags.py`

## New Tests Required
None required, per this ticket's own Out of Scope: "Writing new test coverage beyond what's needed
to trust the trial itself (a full coverage build-out, if warranted, is its own separate scope
decision)." The investigation's Test Coverage Depth Assessment found the domain-logic coverage
already deep; the identified gaps (no real-kernel ON-toggle test, no live reward-ledger producer)
are structural findings to report and caveat in the trial evidence and keep/flip recommendation,
not gaps for this ticket to close with new test code — closing them would mean either wiring a real
ledger producer (new production logic, out of scope) or writing a redundant real-kernel gating test
that would only re-prove what `test_allocate_ap_dormancy.py` already proves for the OFF side (no
material new evidence, and the ON side is exactly what the real corpus trial itself — not a new
unit test — is meant to produce, per Acceptance Criteria).

If, during Implement, the real trial run needs a small helper to sample `last_progression_decision`
values across entities post-run (see investigation.md's Candidate World/Seed section), that is
scaffolding for interpreting the trial's own output, not new pytest coverage, and does not belong
in this section.

## Scoped Pytest Commands
```
pytest tests/unit/domains/progression/ tests/integration/domains/progression/ \
  tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py \
  tests/integration/progression/test_allocate_ap_dormancy.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/unit/entity/test_phase6_reward_ledger_component.py \
  tests/unit/observability/test_event_extractor_equipment.py \
  tests/unit/observability/test_event_extractor_progression.py \
  tests/unit/observability/test_event_shapers_progression.py \
  tests/unit/quest/test_progression_regression.py \
  tests/unit/config/test_phase10_feature_flags.py \
  -m "not slow"
```

Performance budget test (excluded from the default `-m "not slow"` run above, marked `@pytest.mark.
slow`; run separately):
```
pytest tests/perf/test_phase6_progression_conversion_budget.py
```

Never `pytest tests/` — scoped to the progression domain + flag-defaults + directly-adjacent
observability/config surfaces identified above, per CLAUDE.md Testing Rule.

## Anti-Drift Test Guards
- `tests/integration/test_scenario_feature_flag_defaults.py::test_all_flags_default_off_for_every_
  loaded_scenario` and `::test_feature_flag_defaults_are_stable_across_instances` — must keep
  asserting `ENABLE_PROGRESSION_EVOLUTION` stays `FeatureMode.OFF` by default. If this ticket's
  Implement phase's real trial run (which sets `ENABLE_PROGRESSION_EVOLUTION=ON` via env var per
  `tools/calibrate_simq.py`'s override mechanism, same pattern as the 3 sibling trials) leaves any
  process-level or module-level state mutated, these tests would catch a leaked override — the flag
  must return to `OFF` in the code default after the trial, since this ticket does not flip it.
- `tests/integration/progression/test_allocate_ap_dormancy.py` — must keep passing with the flag at
  its real code default (OFF). This is the direct regression guard against `ConversionKind
  .ALLOCATE_AP` accidentally becoming reachable through any change made while producing the trial
  evidence (e.g. an accidental default flip, or a stray ledger-producer wiring change that the Anti-
  Drift Hazards section explicitly warns against making).
- `tests/unit/quest/test_progression_regression.py::test_execute_allocate_ap_silently_no_ops_for_
  unhandled_attribute` — guards the sibling `core_actions.py::execute_allocate_ap` dormant branch
  (PROG-068/069); this ticket must not touch that path, and this test catches accidental drift into
  it.
- `tests/perf/test_phase6_progression_conversion_budget.py` — guards against any accidental
  performance regression to `ProgressionConversionPhase.execute` introduced incidentally while
  investigating/running the trial (the trial itself does not modify phase code, but this is the
  existing regression-prone-path guard per CLAUDE.md's Testing Rule).
- `tests/integration/domains/progression/test_phase6_progression_conversion_phase.py::test_phase_
  skips_when_feature_flag_disabled` — guards the phase's own internal (vestigial) `progression_
  conversion_enabled` check found during investigation; unrelated to the real pipeline gate but
  still must not regress.
- All 7 `tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py` scenario tests
  — the closest existing proxy for "does the domain logic still produce the expected conversion
  decision under a given reward/gap combination" the trial's real-world result should be
  cross-checked against qualitatively (e.g. if the trial surfaces an entity with a damaged weapon
  and a gold reward, its resulting decision should be plausible against Scenario 6.1's asserted
  gold→repair outcome) even though the trial itself runs through the real pipeline, not this
  hand-built harness.
