---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION
artifact_type: test_plan
tags: [feature-flags, world]
---

# Test Plan — TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION

## Regression Surface

This ticket is evidence-gathering (a real corpus trial), not a code change to
`WorldEmergencePhase` or the pipeline's `world_emergence` call site — the regression surface exists
to confirm nothing in the surrounding code drifted, not because this ticket is expected to touch
any of it.

**Unit — `src/domains/world_emergence/` (14 real files, reconciled from investigation.md's own
"3 test files" undercount finding):**
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py` — includes the
  vestigial `world_emergence_enabled`/`periodic_due_ticks["world_emergence_disabled"]` gate's own
  determinism/no-mutation assertions. Must still pass unmodified.
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py`
- `tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py`
- `tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py`
- `tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py`
- `tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py`
- `tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py`
- `tests/unit/domains/world_emergence/test_phase8_scarcity_model.py`
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py` — includes
  `WORLD-104`'s parity-ledger-cited cross-region propagation test.
- `tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py`
- `tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py`
- `tests/unit/domains/world_emergence/test_quest_registry_wiring.py` — `WORLD-102`'s parity-ledger
  test, the direct `quest_registry_add` durable-merge regression guard.

**Unit — adjacent domains referenced by the 8 `world_dynamics.yaml` parity entries:**
- `tests/unit/quest/test_quest_generation.py` (`WORLD-098`, `WORLD-099`)
- `tests/unit/quest/test_quest_lifecycle.py` (`WORLD-101`)
- `tests/unit/world/test_sovereignty_events.py` (`WORLD-107`)
- `tests/unit/observability/test_event_shapers_world_dynamics.py` (`WORLD-115`, 25 tests — the
  `world_emergence_event`/`narrative_milestone` push-shaper mechanism this ticket's own
  investigation traced as independent of `ENABLE_WORLD_EMERGENCE`; must keep passing unmodified
  since that mechanism is unaffected by this ticket).

**Integration:**
- `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py` — the one test
  that actually exercises the vestigial `world_emergence_disabled` gate via
  `periodic_due_ticks={"world_emergence_disabled"}`.
- `tests/integration/scenarios/test_phase8_world_emergence_scenarios.py`
- `tests/integration/scenarios/test_resource_depletion.py` — calls `WorldEmergencePhase.execute()`
  directly (bypassing the pipeline and `ENABLE_WORLD_EMERGENCE` flag entirely, per investigation.md)
  over a synthetic 1000-tick window; real coverage of the domain's core logic, useful as a sanity
  cross-check against the real corpus trial's own OFF-baseline resource-depletion activity.

**Performance:**
- `tests/perf/test_phase8_world_emergence_budget.py` — relevant context if the real corpus trial
  observes elevated tick-budget pressure (per investigation.md's degradation-controller finding
  that `world_emergence` is dropped first under `DEGRADED`/`CRITICAL` load); not itself expected to
  change.

**Feature-flag config / allowlist (touches `ENABLE_WORLD_EMERGENCE`'s own default):**
- `tests/unit/config/test_phase10_feature_flags.py` (`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist and
  the "all Phase 10 flags default OFF except the documented exceptions" sentinel) — must still pass
  with `ENABLE_WORLD_EMERGENCE` absent from the ON-default allowlist, since this ticket does not
  flip the flag.
- `tests/integration/test_scenario_feature_flag_defaults.py`
- `tests/certification/test_phase10_enhanced_determinism_parity.py`
- `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off`
  (DEV-002's own sentinel, same default-OFF policy class).
- `tests/architecture/test_adventure_routing_flag_inert.py` — the existing sibling regression guard
  this ticket's new `ENABLE_WORLD_CAPABILITY_LAYER` guard (below) is modeled on; must keep passing
  unmodified (unrelated flag, unrelated finding).

**Not included** (assessed and excluded, per investigation.md): `tests/unit/progression/
test_phase8_progression.py` and `tests/unit/observability/test_phase8_m46_m47_m48.py` — both
`phase8`-named but not confirmed to reference `world_emergence` specifically; not part of this
domain's regression surface.

## New Tests Required

**One new architecture-guard test, mirroring the sibling `ENABLE_ADVENTURE_ROUTING` inertness
precedent** (`tests/architecture/test_adventure_routing_flag_inert.py`,
`TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`):

- **Test name**: `test_enable_world_capability_layer_has_no_live_gating_call_site`
- **Category**: architecture guard
- **What it verifies**: `grep`-style source scan across `src/**/*.py` (excluding
  `feature_flags.py`'s own registration line) for any of
  `is_enabled("ENABLE_WORLD_CAPABILITY_LAYER")`, `get_flag_mode("ENABLE_WORLD_CAPABILITY_LAYER")`,
  or `feature_flag="ENABLE_WORLD_CAPABILITY_LAYER"` (both quote styles) — asserts zero matches.
  Pins investigation.md's static finding (no `WorldCapabilityLayer` class/phase exists anywhere in
  `src/`, and the flag's only non-registration reference is a test-scaffold `pressure_signals`
  entry in `src/testing/scenario_runner.py` that maps to nothing) so a future real wiring of this
  flag fails this test loudly, forcing re-examination of this ticket's own "no combination
  interaction possible with `ENABLE_WORLD_EMERGENCE`" resolution instead of the claim silently
  going stale.
- **Where it lives**: `tests/architecture/test_world_capability_layer_flag_inert.py` (new file,
  same directory and naming convention as the sibling `test_adventure_routing_flag_inert.py`).

**No new test is warranted for the vestigial `world_emergence_enabled`/`periodic_due_ticks`
in-function gate** (investigation.md's second finding) — unlike the `ENABLE_WORLD_CAPABILITY_LAYER`
case, this gate genuinely is live code with one real exercising test already
(`test_phase8_world_emergence_phase.py`); it is disclosed as a latent-footgun risk, not proposed
for removal or a new guard, since fixing/removing it is out of this ticket's scope.

**No new test is warranted for the `world_emergence_event` red-herring finding** — this is an
investigation-time observability-signal clarification for whoever runs the real corpus trial, not
a code behavior to pin with a regression test; `event_extractor.py`/`event_shapers.py`'s own
existing coverage (`WORLD-115`, `tests/unit/observability/test_event_shapers_world_dynamics.py`)
already covers the actual `world_events_add`-iteration mechanism this finding is about.

The real corpus ON/OFF trial itself (Implement's job, not a pytest artifact) is the primary new
evidence this ticket produces — its output (raw `metric_counters`, `quest_registry` growth,
`quality_report.json`) is documented in `trial_evidence.md`, not encoded as a new automated test.

## Scoped Pytest Commands

```
pytest tests/unit/domains/world_emergence/ tests/integration/domains/world_emergence/ \
  tests/integration/scenarios/test_phase8_world_emergence_scenarios.py \
  tests/integration/scenarios/test_resource_depletion.py \
  tests/perf/test_phase8_world_emergence_budget.py -m "not slow"
```

```
pytest tests/unit/quest/test_quest_generation.py tests/unit/quest/test_quest_lifecycle.py \
  tests/unit/world/test_sovereignty_events.py \
  tests/unit/observability/test_event_shapers_world_dynamics.py
```

```
pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/certification/test_phase10_enhanced_determinism_parity.py \
  tests/architecture/test_adventure_routing_flag_inert.py \
  tests/architecture/test_world_capability_layer_flag_inert.py
```

```
pytest tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off
```

Never `pytest tests/` — always scoped to the world-emergence domain, its 8 parity-cited adjacent
tests, and the feature-flag-default/inertness sentinels above, per the Testing Rule.

## Anti-Drift Test Guards

- **`test_world_capability_layer_flag_inert.py` (new) must keep failing loudly if
  `ENABLE_WORLD_CAPABILITY_LAYER` is ever given a real gating call site** — a future ticket wiring
  it up would reopen this ticket's own "no combination trial needed" resolution and require
  re-examining whether it now interacts with `ENABLE_WORLD_EMERGENCE`.
- **`test_phase8_world_emergence_boundary.py`'s `world_emergence_disabled`-gated assertions must
  keep passing unmodified** — this ticket does not touch the vestigial in-function gate; a failure
  here would mean something else changed it, not this ticket's own scope.
- **`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist test must keep rejecting `ENABLE_WORLD_EMERGENCE`** as
  an ON-default flag unless and until a separate, explicit flip decision is made and implemented
  (not this ticket) — a passing trial must not be used as justification to quietly add the flag to
  the allowlist inside this ticket.
- **`test_event_shapers_world_dynamics.py` (`WORLD-115`) must keep passing unmodified** — confirms
  the `world_emergence_event`/push-shaper mechanism this ticket's investigation traced as
  independent of `ENABLE_WORLD_EMERGENCE` hasn't itself drifted; a failure here is a signal the red
  herring finding needs re-verifying before the corpus trial's evidence-capture step trusts it.
- **Corpus trial evidence-capture must not use `world_emergence_event` counts as ON/OFF evidence**
  (see investigation.md) — a trial design that did would silently "pass" a naive suppression check
  while proving nothing about this specific flag, since that event type is produced by systems this
  flag doesn't gate.
- **Corpus trial evidence-capture must include the OFF/baseline run's own absolute
  `quest_registry`/`metric_counters["aggregates_generated"]` volume**, not just an ON-vs-OFF diff —
  a degenerate near-empty world would pass a naive "ON == OFF" check without proving real behavior
  under load, the same caveat both sibling trials already disclosed for their own domains.
