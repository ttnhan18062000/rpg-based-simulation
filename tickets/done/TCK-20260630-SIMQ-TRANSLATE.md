---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-TRANSLATE
phase: done
date: 2026-06-30
tags: [simulation-quality, observability, event-translation, audit]
---

# TCK-20260630-SIMQ-TRANSLATE

## Title
Translation table completeness audit and event type coverage doc

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Audit every `event_type` emitted by the engine (via `event_extractor.py` and the event bus)
against the `SCORER_REGISTRY` in `QualityHub`. Produce a coverage document that classifies
every emitted event type as: (a) scored by SimQ, (b) P0-A blocked (never emitted yet),
(c) translation gap (emitted but not reaching the right scorer), or (d) intentionally unscored.

## Scope
1. Extract all `event_type` values emitted in `simulation_events.jsonl` from a long
   calibration run (1000-tick sandbox_world after TCK-20260630-SIMQ-CALFIX)
2. Extract all `event_type` values registered in `SCORER_REGISTRY` (from scorer EVENT_TYPES)
3. Extract all `event_type` → `contract_type` mappings from `_TRANSLATE_SIMPLE` and
   `_TRANSLATE_CONDITIONAL` in `quality_hub.py`
4. For each emitted type: classify against the registry
5. For each registry type with zero calibration hits: confirm P0-A blocked or find gap
6. Write `docs/simulation_quality/event_type_coverage.md` with the full classification table
7. If any translation gaps are found: fix them in the same ticket (scope is small)

## Out of Scope
- Adding new scoring rules (only translation/routing fixes, not new scorer logic)
- Fixing P0-A blocked events (they're not emitted, nothing to translate)

## Acceptance Criteria
- [x] `docs/simulation_quality/event_type_coverage.md` committed with full classification table
- [x] Every emitted event_type accounted for (scored / blocked / unscored with reason)
- [x] Every scorer EVENT_TYPE with zero calibration hits marked as P0-A blocked or gap
- [x] Any translation gaps found: fixed in `quality_hub.py` with a test (none found)
- [x] `make knowledge-index-update` run after doc committed

## Related Tickets
- TCK-20260630-SIMQ-CALFIX (prerequisite — need world-loaded calibration runs)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track D
- `docs/simulation_quality/quality_scoring_contract.md` §8.1 (event routing)
- `docs/simulation_quality/event_type_coverage.md` (created by this ticket)

## Related Code Areas
- `src/simulation_quality/quality_hub.py` — `_TRANSLATE_SIMPLE`, `_TRANSLATE_CONDITIONAL`, `SCORER_REGISTRY`
- `src/observability/event_extractor.py` — all `event_type=` literals (source of truth)
- `src/simulation_quality/scorers/*.py` — `EVENT_TYPES` tuples

## Assumptions / Open Questions
- Some event types are emitted conditionally (e.g., `boss_spawned` requires world_boss kind).
  These should be classified as "world-infrastructure-gated" (subset of P0-A blocked).
- The `InvariantViolation` engine event → `combat_hard_law_violation` / `conservation_law_violated`
  conditional translation should be verified against real hard law events.

## Implementation Notes

**Calibration data:** `data/calibration/` has quality_scores.jsonl (not simulation_events.jsonl).
Event type source-of-truth was event_extractor.py + typed events in events.py + engine kernel.py.

**Translation table status:** COMPLETE. All 8 `_TRANSLATE_SIMPLE` and 5 `_TRANSLATE_CONDITIONAL`
entries verified correct. No translation gaps found. Zero changes needed to quality_hub.py.

**Translation test coverage:** 3 entries in _TRANSLATE_SIMPLE were previously untested:
- `leadership_changed` → `diplomatic_transition`
- `alliance_formed` → `alliance_accepted`
- `betrayal_desertion` → `faction_tension_delta` / `contract_lapsed` (conditional)
4 new tests added to `test_quality_hub_event_translation.py` (28 total, all passing).

**Key findings:**
- 55 event_types classified as `scored`
- 0 translation_gaps
- 27 engine_emission_gaps (scorer infrastructure ready, engine doesn't emit yet)
- 3 p0_a_blocked (campaign/scenario-gated in calibration)
- 13 unscored_intentional

**Notable engine_emission_gaps (require follow-on engine work):**
- `paid_info_transaction` (EconomyScorer) — contract §5 says separate from `paid_information_transaction`; engine_extractor needs second emit on INFORMATION_PURCHASE
- `lead_certainty_updated` (InformationScorer) — contract §5 distinguishes from `lead_certainty_changed`; separate engine emit needed
- `defer_with_reason`, `commitment_abandoned`, `rejection_cascade_tick`, `route_family_first_use` (AgencyScorer) — adventure routing domain stubs
- 5 ProgressionScorer types — progression system stubs
- 5 WorldDynamicsScorer types — world dynamics system stubs

## Test Summary
- `tests/simulation_quality/test_quality_hub_event_translation.py`: 28 tests, all PASSED
- `tests/simulation_quality/` full suite: 309 passed, 11 deselected (not slow), 0 failures
- No scorer behavior changed — no scorer unit tests needed beyond translation tests

## Files Changed
- `docs/simulation_quality/event_type_coverage.md` — new; full classification table
- `tests/simulation_quality/test_quality_hub_event_translation.py` — 4 new tests for leadership_changed, alliance_formed, betrayal_desertion
- `docs/parity_ledger/infrastructure.yaml` — SIMQ-CALIBRATED-001 divergence_note updated

## Completion Summary
Audited all engine event_type sources (event_extractor.py, typed events in events.py, engine/kernel.py, campaigns, scenario_runtime). Cross-referenced against SCORER_REGISTRY (10 scorer files). Verified all 13 translation table entries in quality_hub.py are correct. Produced docs/simulation_quality/event_type_coverage.md classifying 98 event_type/scorer combinations. Added 4 tests for previously untested translation entries. No behavior changes. 27 engine_emission_gaps documented as future work surface.
