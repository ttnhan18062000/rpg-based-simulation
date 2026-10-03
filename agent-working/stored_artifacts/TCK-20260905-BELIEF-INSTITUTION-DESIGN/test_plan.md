---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-BELIEF-INSTITUTION-DESIGN
artifact_type: test_plan
tags: [social, strategy]
---

# Test Plan — TCK-20260905-BELIEF-INSTITUTION-DESIGN

## Regression Surface (existing tests that must pass)

- `tests/unit/domains/fame/` (whatever exists from the sibling ticket) — confirm zero behavior change to `FameState`/`FameCarryForward`/`FameExporter`/`FameImporter`/`LegendFact`/`LegendFactService`.
- `tests/unit/domains/fidelity/` — confirm zero behavior change.
- `tests/unit/domains/faction/test_clan_state.py`, `test_clan_lifecycle.py` — confirm zero behavior change to `ClanState` (read-only consumer).
- `tests/unit/strategic/test_belief_cycle.py`, `test_belief_integration.py` — confirm `BeliefEntry` untouched.
- `tests/unit/cognition/test_phase2_self_model_phase.py` — confirm `KnowledgeFact` untouched.
- `tests/unit/domains/campaigns/` (orchestrator tests) — confirm `_advance_state()`'s existing behavior (Culture/Fidelity/Fame exports) is unaffected by the new 4th call.

## New Tests Required (per AC)

- AC1 (blocked-until-DONE guard): a source-text or process check confirming this ticket's Implement phase ran only after `TCK-20260905-FAME-DERIVER-LEGEND-FACT` was DONE — documented in Implementation Notes, not necessarily a runtime test (the dependency is a process/sequencing fact, already satisfied by the time this runs).
- AC2 (BeliefInstitution shape/round-trip): `test_belief_institution_round_trip_serialization` — `to_dict()`/`from_dict()` preserve all fields.
- AC3 (formation requires a real LegendFact): `test_no_belief_institution_without_qualifying_legend_fact` — a subject below `FAME_THRESHOLD` produces zero `BeliefInstitution` entries.
- AC4 (divergent interpretation): `test_two_clans_form_different_belief_strength_for_same_origin_event` — one clan contains the legendary subject as a member (in-group), another does not (out-group); assert both clans' resulting `belief_strength` differ, and the in-group value is strictly higher.
- AC5 (no cross-contamination): `test_belief_institution_design_does_not_modify_belief_entry_or_knowledge_fact` — source-text guard confirming no import/mutation of `BeliefEntry`/`KnowledgeFact` classes from the new module.
- AC6 (no SimQ/CHURCH wiring): `test_no_new_simq_pillar_or_church_wiring` — source-text guard confirming no new SimQ pillar registration and no read/dispatch of `"BLESSING"`/`"RESURRECTION"` was added.
- Determinism: `test_belief_institution_derivation_is_deterministic` — calling the derivation twice with identical inputs produces byte-identical output.
- Non-numeric `subject_id` safety: `test_belief_institution_skips_non_numeric_subject_id_safely` — a `LegendFact` whose `subject_id` isn't int-castable produces no crash and no membership match (treated as out-group for all clans, or skipped — decided in Plan).

## Scoped Pytest Commands

```
python3 -m pytest tests/unit/domains/ tests/unit/strategic/ tests/unit/cognition/ tests/architecture/ -q
```
(Bare `tests/unit/domains/` directory required per this repo's structural test-scope-coverage backstop — every M5 ticket so far has hit this if cherry-picked files were used instead.)

## Anti-Drift Test Guards

- Guard test confirming `ClanState`/`AuthoritativeState` receive zero writes from this ticket's new code (read-only `final_state.clans` consumption only).
- Guard test confirming `CampaignState`'s new `belief_institutions` field follows the exact same mutation pattern (`CampaignOrchestrator`-direct, not `patches.py`-routed) as `entity_fame`/`historical_drift`.
