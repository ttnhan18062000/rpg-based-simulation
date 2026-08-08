---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-PHASE2
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-CUTOVER-PHASE2

## Real-kernel verification — default (post-cutover) state, 5 worlds

Ran a real, non-mocked kernel event-stream check with **no explicit flag override** (the real
post-cutover default) across 5 worlds. Before the `run_shadow_shapers()` default-lockstep fix
(see investigation.md and `docs/parity_ledger/infrastructure.yaml` `INFRA-326`): every world showed
`event_extractor=0` AND `event_shapers=0` — total blackout. After the fix: every world shows
`event_extractor=0` (no leak from the legacy path) and real, non-zero `event_shapers` delivery
counts (43–845 depending on world activity level).

## Real-kernel verification — explicit rollback

`ENABLE_PUSH_EVENT_SHAPERS_PHASE2=OFF` explicit override on `hero_guild_routing`: restores
`event_extractor=911` delivery (old path), confirming a genuine, working rollback — not merely a
flag that's never read.

## Scoped pytest — unit tests

`tests/unit/observability/test_event_shapers_strategy.py`,
`test_event_shapers_progression.py`, `test_event_shapers_world_dynamics.py`,
`test_event_shapers_social.py`, `test_event_shapers_deferred_instrumentation.py`,
`test_event_extractor.py` (existing, unmodified — MagicMock-based `prior_state.feature_flags`
fixtures naturally exercise the old-path default, same mechanism Phase 1's cutover relied on) —
all passing. `test_event_shapers_strategy.py`'s
`test_run_shadow_shapers_default_off_excludes_phase2_events` renamed to
`test_run_shadow_shapers_default_includes_phase2_events` (new correct default assertion) and a
new `test_run_shadow_shapers_explicit_off_excludes_phase2_events` added (explicit rollback
coverage the old test never had).

## Full `tests/perf/` suite

1046 passed, 6 skipped, 3 deselected, excluding 2 disclosed pre-existing failures unrelated to
this ticket (`test_observability_scale_validation.py::test_scale_performance_and_footprint`,
`test_profiler_integrity.py::test_recorded_tick_compute_includes_all_phases` — see
`TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG`, filed not silently absorbed).

## Full calibration corpus (`make simq-full-audit-full`) — ran to completion

79 scenarios, real non-mocked kernel. `test_grade_regression.py`: **37 failed, 32 passed, 18
deselected** — up from Phase 1's own cutover (32/69). Root-caused via a decisive
differential-repro (`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` forced OFF vs ON, driving the kernel
directly for `urban_political_selfmodel_probe_seed42_200t`): COMBAT and PROGRESSION pillar scores
byte-identical between the two pipelines; SOCIAL showed only ~1.5% event-count variance with the
same letter grade — with real `WatchdogTrip` CRITICAL alerts firing in *both* runs. Confirmed as
the same pre-existing `INFRA-273` tick-budget-watchdog mechanism, not a Phase 2 regression, now
visible on more pillars because Phase 2 widened live delivery to AGENCY/COGNITION/INFORMATION/
PROGRESSION/WORLD/SOCIAL. `grade_anchors.json` left unrecalibrated, per plan.md's Scope Guards.
Full repro in investigation.md; recorded in `docs/parity_ledger/infrastructure.yaml`'s `INFRA-273`
2026-08-07 update and `docs/audits/D20_simq_quality_status_review.md`'s Finding 13.

## Coverage

- Normal flow: default-state delivery verified real, non-mocked, across 5 worlds.
- Edge case: rollback path verified real, non-mocked.
- Failure mode: the default-lockstep blackout itself was caught by this exact verification
  methodology (a real kernel run under the real default state), not by unit tests alone — unit
  tests use `MagicMock`-based `prior_state.feature_flags` fixtures that never exercise the
  real-default fallback the way an unset flags dict from a real kernel run does. Two new/renamed
  tests now cover both the fixed default and the rollback explicitly.
- Regression: full scoped `tests/perf/` suite and full calibration corpus, both run to
  completion, both disclosed truthfully (2 pre-existing unrelated failures, not silently
  absorbed).
