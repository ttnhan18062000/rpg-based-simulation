---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION
artifact_type: test_plan
tags: [feature-flags, combat]
---

# Test Plan — TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION

## Regression Surface

This ticket is evidence-gathering (a real corpus trial), not a code change to
`CombatEngagementPhase` or the `pipeline.py` merge fix — the regression surface exists to confirm
nothing in the surrounding code drifted since TCK-20260809, not because this ticket is expected to
touch any of it.

**Unit — `src/domains/combat_engagement/`:**
- `tests/unit/domains/combat_engagement/test_combat_engagement_phase_merge.py` — the direct
  TCK-20260809 regression guard (prior-phase `EntityUpdate` survives `combat_engagement` when the
  flag is ON; flag-OFF path unaffected). Must still pass unmodified.
- `tests/unit/domains/combat_engagement/test_phase4_combat_engagement_events.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_engagement_boundary.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_learning.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_postures.py`
- `tests/unit/domains/combat_engagement/test_phase4_combat_reassessment.py`
- `tests/unit/domains/combat_engagement/test_phase4_engagement_risk.py`
- `tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py`
- `tests/unit/domains/combat_engagement/test_phase4_posture_selector.py`
- `tests/unit/domains/combat_engagement/test_phase4_posture_to_intent.py`
- `tests/unit/domains/combat_engagement/test_phase4_self_combat_estimate.py`

**Integration:**
- `tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py`
- `tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py`

**Performance:**
- `tests/perf/test_phase4_combat_engagement_budget.py` — covers the already-disclosed
  0.85ms-avg/17.3ms-peak per-tick cost noted in TCK-20260809's own investigation; relevant context
  if the real corpus trial re-observes elevated tick-budget-exceeded rates, but not itself expected
  to change.

**Feature-flag config / allowlist (touches `ENABLE_COMBAT_ENGAGEMENT`'s own default):**
- `tests/unit/config/test_phase10_feature_flags.py` (`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist and
  the general "all Phase 10 flags default OFF except the documented exceptions" sentinel) — must
  still pass with `ENABLE_COMBAT_ENGAGEMENT` absent from the ON-default allowlist, since this
  ticket does not flip the flag itself.
- `tests/integration/test_scenario_feature_flag_defaults.py`
- `tests/certification/test_phase10_enhanced_determinism_parity.py`
- `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off`
  (DEV-002's own sentinel — not this flag specifically, but the same default-OFF policy class;
  confirms the mechanism this ticket's trial exercises hasn't drifted).

## New Tests Required

**None.** This ticket produces evidence (a real corpus ON/OFF trial) and a decision document, not
new gameplay code or a new code path — there is no new behavior to unit-test. The existing
TCK-20260809 regression guard (`test_combat_engagement_phase_merge.py`) already covers the
mechanism this ticket's trial re-confirms at the unit level; the trial itself is not a pytest
artifact but a real `tools/calibrate_simq.py` run whose output (raw event counts, `quality_report.
json`) is the evidence, documented in `investigation.md`'s Corpus Trial Plan and in whatever
decision doc Implement produces. If the real trial surfaces a genuine new regression (not
expected, but not ruled out either), that would warrant a new hotfix ticket with its own new
regression test — not a new test authored preemptively here for a bug that may not exist.

## Scoped Pytest Commands

```
pytest tests/unit/domains/combat_engagement/ tests/integration/domains/combat_engagement/ \
  tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py \
  tests/perf/test_phase4_combat_engagement_budget.py -m "not slow"
```

```
pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/certification/test_phase10_enhanced_determinism_parity.py
```

```
pytest tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off
```

Never `pytest tests/` — always scoped to the combat-engagement domain and the feature-flag-default
sentinels above, per the Testing Rule.

## Anti-Drift Test Guards

- **`test_combat_engagement_phase_merge.py` must still pass unmodified.** If the real corpus trial
  somehow motivates touching `pipeline.py`'s `combat_engagement` registration, that is out of this
  ticket's own Scope (no code change is called for) — a failing merge test here would mean the
  ticket has drifted into fixing/changing behavior instead of validating it, and should stop and be
  re-scoped, not patched through.
- **`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist test must keep rejecting `ENABLE_COMBAT_ENGAGEMENT`**
  as an ON-default flag unless and until a separate, explicit flip decision is made and
  implemented (not this ticket) — this ticket's own trial output feeds that future decision, it
  does not enact it. A passing trial must not be used as justification to quietly add the flag to
  the allowlist inside this ticket.
- **`test_adventure_routing_defaults_off`-class sentinels (DEV-002 policy)** guard that the
  blanket Phase-10 default-OFF policy itself hasn't eroded elsewhere while this ticket is
  in flight (shared-directory concurrency risk per CLAUDE.md's Hard Rules) — a failure here
  unrelated to `ENABLE_COMBAT_ENGAGEMENT` specifically is a signal another concurrent session's
  work needs investigating, not something this ticket should absorb or silently work around.
- **Corpus trial evidence-capture must include the OFF/baseline run's own absolute event counts**,
  not just an ON-vs-OFF diff (see investigation.md's Anti-Drift Hazards) — a test/trial design that
  only checks "ON events == OFF events" without confirming OFF produces genuinely nonzero combat
  activity would silently pass on a degenerate, combat-free world and prove nothing.
