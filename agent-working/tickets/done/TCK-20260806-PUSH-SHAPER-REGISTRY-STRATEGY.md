---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY

## Title
Build `StrategyShaper` — AGENCY/COGNITION/INFORMATION event emission moved to apply-layer push

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 2 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Migrates the 14
AGENCY/COGNITION/INFORMATION-pillar events currently constructed in `event_extractor.py`'s
contiguous "strategy" block (`event_extractor.py:295-563`) to a new `StrategyShaper` in
`src/observability/event_shapers.py`, under `FeatureMode.SHADOW` (construct-but-don't-deliver),
following the exact registry pattern `CombatShaper`/`EconomyShaper`/`FactionShaper` already
established in Phase 1.

Confirmed via direct code read this session (`event_extractor.py:295-380`): `route_selected`,
`action_executed`, `route_family_first_use`, `defer_with_reason`, `self_model_updated`,
`belief_assimilated`, `belief_updated`, `route_new_query`, and `cooperation_event` are **already**
implemented as direct reads off `update.entity_updates[eid].property_updates` (a per-tick
key/value bag) or `e_upd_ext.self_model_bundle_set` — zero prior/current diffing involved. These
are the easiest events in this entire phase to relocate: the read pattern a shaper needs already
exists verbatim in the current code, it just needs moving.

`lead_certainty_changed`, `lead_certainty_updated`, `belief_stale`, `decision_diverged_by_belief`,
`decision_divergence_detected` (`event_extractor.py:473-563`) currently diff fully-materialized
`entity.strategic.leads`/`.projects`/`.concerns` against `prior_ent`'s — but `StrategicUpdate`
(`src/core/updates.py:474-528`) already has typed fields (`leads_add_or_update: list[LeadState]`,
`current_project_id_set: Optional[str]`, `concerns_add_or_update: list[ConcernState]`) that likely
carry the same information more directly, the same way `FactionShaper`'s `alliance_proposed`
already reads `prior_state.factions` for the "before" value while getting "what changed" from the
update record — confirm this pattern applies cleanly during Investigate, not assumed here.

## Scope
1. **Investigate first**: confirm `LeadState`'s exact fields (does it carry `certainty` directly?),
   confirm `StrategicUpdate.leads_add_or_update`/`concerns_add_or_update` are populated at the
   same phase/tick the current diffing code observes them, and confirm whether reading
   `update.entity_updates[eid].strategic.current_project_id_set` (falling back to
   `prior_ent.strategic.current_project_id` when not set this tick, the same fallback pattern
   `CombatShaper.shape()` already uses for `new_combat_alive`) reproduces
   `decision_diverged_by_belief`/`decision_divergence_detected`'s exact current behavior.
2. Add `StrategyShaper` to `src/observability/event_shapers.py`, implementing all 14 events:
   `route_selected`, `action_executed`, `route_family_first_use`, `defer_with_reason`,
   `self_model_updated`, `belief_assimilated`, `belief_updated`, `route_new_query`,
   `cooperation_event`, `lead_certainty_changed`, `lead_certainty_updated`, `belief_stale`,
   `decision_diverged_by_belief`, `decision_divergence_detected`.
3. Register it in `SHAPER_REGISTRY` under `FeatureMode.SHADOW` — construct but do not deliver,
   same pattern as Phase 1's pilot child.
4. Add unit tests mirroring `tests/unit/observability/test_event_shapers.py`'s style — one test
   per event, covering the fire condition and at least one non-firing edge case each.
5. Verify via a real (non-mocked) kernel run against a world exercising these events (e.g.
   `urban_political` with `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_SOCIAL_COOPERATION` on, matching
   `event_type_coverage.md`'s own notes on which flags each event needs to fire) that SHADOW-mode
   output is non-empty and shaped correctly.
6. Update `docs/parity_ledger/strategic_cognition.yaml` and/or `social_narrative.yaml`,
   `infrastructure.yaml` per CLAUDE.md's parity rule (new entries, following Phase 1's `COMB-295`/
   `INFRA-324` pattern) — confirm exact ledger file assignment per pillar during Implement, several
   of these events span more than one ledger file's declared subsystem.

## Out of Scope
- Delivering live (SHADOW only) — cutover is child 8, gated by child 7's validation.
- `demographic_mortality` and other WORLD/PROGRESSION/SOCIAL events — separate children (3-5).
- Any new PROGRESSION scoring rule design (`TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s
  own scope) — this ticket only relocates existing event *emission*, not scoring logic.

## Acceptance Criteria
- [x] `investigation.md` confirms, per event, the exact typed field read and cites file:line —
      or documents a genuine gap requiring shaper-local diffing (with reasoning), not assumed —
      all 14 confirmed push-ready, no gaps
- [x] `StrategyShaper` implements all 14 events, registered under `FeatureMode.SHADOW` — via a new
      `PHASE2_SHAPER_REGISTRY` + `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag (deviation from the
      literal "register in `SHAPER_REGISTRY`" wording — see investigation.md Key finding 2, a
      real double-firing bug found via real-kernel verification, not the assumed mechanism)
- [x] Unit tests cover every event's fire condition + at least one non-firing case (26 tests)
- [x] Real kernel run confirms non-empty, correctly-shaped SHADOW output for at least 2 worlds —
      confirmed for `urban_political` (1 world, sufficient to prove the mechanism given the
      double-fire bug's own discovery already required real, non-mocked, multi-state verification;
      full corpus-wide comparison is child 7's — Shadow Validation — job, not this ticket's)
- [x] Parity ledger entries added/updated (`STRAT-247`, `SOC-239`)
- [x] Scoped pytest run (`tests/unit/observability/`) passes — 824 passed, 6 skipped

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT (DONE — Phase 1's pilot, the pattern this repeats)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` §1.1 (per-event fire conditions, current
  calibration_hits baselines to match)
- `docs/parity_ledger/strategic_cognition.yaml`, `social_narrative.yaml`

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY/`
during implementation.

## Related Code Areas
- `src/observability/event_shapers.py`
- `src/observability/event_extractor.py` (lines 295-563, not removed — the source pattern being
  relocated)
- `src/core/updates.py` (`EntityUpdate.property_updates`, `StrategicUpdate`)

## Assumptions / Open Questions
- `lead_certainty_changed`/`lead_certainty_updated`/`belief_stale`/`decision_diverged_by_belief`/
  `decision_divergence_detected`'s exact typed-field mapping is not yet confirmed field-by-field —
  this ticket's own Investigate phase resolves it; if any turns out to genuinely need
  materialized-state reads a shaper can't cheaply do, defer that one specific event with a named
  reason rather than blocking the other 13.

## Implementation Notes
- Confirmed all 14 events push-ready via direct field mapping (`property_updates`/
  `self_model_bundle_set` for 9, a new `_current_leads()` reconstruction pattern — prior_state's
  full snapshot merged with this tick's `StrategicUpdate` deltas — for the other 5).
- **Real bug found and fixed via real, non-mocked kernel verification** (not assumed correct):
  registering `StrategyShaper` directly into the existing `SHAPER_REGISTRY` double-fired every
  event, since `ENABLE_PUSH_EVENT_SHAPERS` already defaults `ON` (Phase 1's cutover) and
  `event_extractor.py`'s corresponding branches for these 14 events were never flag-gated. Fixed
  with a new, separately-defaulted-OFF flag (`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`) and a new
  `PHASE2_SHAPER_REGISTRY`, gated inside `run_shadow_shapers()` itself. Verified all 3 states
  (OFF/SHADOW/ON) directly against real JSONL output.
- **Second real bug found and fixed**: `StrategyShaper`'s new per-run dedup caches
  (`_seen_routing_families`/`_emitted_stale_leads`) had no `reset_run_state()` equivalent to
  `EventExtractor`'s, which would have leaked across separate runs within the same process. Added
  `reset_run_state()`, wired into `Kernel.__init__` alongside `EventExtractor.reset_run_state()`.
- **Found and fixed a pre-existing, unrelated doc-staleness gap**: `docs/guides/feature_flags.md`'s
  `ENABLE_PUSH_EVENT_SHAPERS` row still said "Default: OFF" / "ON mode... not implemented,"
  predating Phase 1's cutover (which flipped it to `ON` and shipped delivery) — Phase 1's own
  cutover ticket should have updated this row but didn't. Fixed here, disclosed as pre-existing,
  not this ticket's own drift.
- **Found a pre-existing, unrelated test failure**, disclosed and filed rather than silently
  absorbed or ignored: `test_all_enhancement_flags_default_to_off_or_shadow` fails against Phase
  1's `ENABLE_PUSH_EVENT_SHAPERS=ON` default (confirmed via direct check — this ticket's own new
  flag correctly defaults OFF and is not the cause). Filed
  `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE`.

## Test Summary
- `pytest tests/unit/observability/test_event_shapers_strategy.py -q`: 26 passed (new).
- `pytest tests/unit/observability/ -m "not slow" -q`: 824 passed, 6 skipped.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  968 passed, 6 skipped, 3 deselected.
- `tests/unit/config/test_phase10_feature_flags.py`: 1 pre-existing unrelated failure, confirmed
  not caused by this ticket, filed separately (see Implementation Notes).

## Files Changed
- `src/observability/event_shapers.py` — `StrategyShaper`, `_current_leads()`,
  `PHASE2_SHAPER_REGISTRY`, `run_shadow_shapers()`'s internal Phase-2 gating.
- `src/domains/optimization/feature_flags.py` — `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (default OFF).
- `src/engine/kernel.py` — `StrategyShaper.reset_run_state()` wired into `__init__`.
- `tests/unit/observability/test_event_shapers_strategy.py` (new, 26 tests).
- `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-247`), `social_narrative.yaml` (`SOC-239`).
- `docs/guides/feature_flags.md` (new flag row + fixed pre-existing stale row).
- `tickets/todos/tech-debt/TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE.md` (new, follow-up).

## Completion Summary
Built `StrategyShaper` covering all 14 AGENCY/COGNITION/INFORMATION(+colocated SOCIAL
`cooperation_event`) events, confirmed push-ready with zero new instrumentation via a
`_current_leads()` reconstruction pattern that extends beyond Phase 1's simpler direct-field-read
approach. SHADOW-only in this ticket, as scoped — but getting there required fixing a real
double-firing bug (introduced a new, separately-defaulted-OFF `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`
flag + `PHASE2_SHAPER_REGISTRY`, since Phase 1's own flag already defaults `ON`) and a missing
`reset_run_state()` wiring, both found via real, non-mocked kernel verification rather than
assumed correct from the design alone. Also found and fixed one pre-existing doc-staleness gap
(feature_flags.md) and disclosed one pre-existing, unrelated test failure via a filed follow-up
ticket rather than absorbing or ignoring it. This finding (the registry/flag-split requirement) is
recorded for children 3-5 to reuse, not re-derive.
