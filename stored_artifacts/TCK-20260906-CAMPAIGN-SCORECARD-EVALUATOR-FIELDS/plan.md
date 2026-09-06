---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS
date: 2026-09-06
---

# Plan: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS

## Scope Guards
- Additive only to `CampaignScorecard`/`CampaignScorecardEvaluator` — the existing 7 fields are untouched.
- No changes to `LifecycleSystem`, `ReputationService`, `FidelityExporter`, `CampaignOrchestrator`, or `EntityCarryForward` — this ticket adds tests and 2 new scorecard fields only.
- No wiring of `CampaignScorecardEvaluator` into `CampaignOrchestrator` (out of scope, confirmed with orchestrator).

## Ordered Steps

1. **Add `reputation_inheritance_check`/`nemesis_transfer_check` to `CampaignScorecard`** (`src/domains/campaigns/schema.py`) — two new `str` fields (`"pass"|"fail"|"partial"`), appended after `world_feedback_usage` matching the existing field ordering convention (test-relevant fields grouped before the numeric/count fields).
2. **Compute both fields in `CampaignScorecardEvaluator.evaluate()`** (`src/domains/campaigns/scorecard.py`) by scanning `entity_arc_reports`' `major_events` for `event_type == "died"` entries (already in the classifier's existing whitelist — no `classifier.py` change needed):
   - Default both to `"partial"` (no death observed this run — matches this evaluator's existing "not exercised" semantics, e.g. `route_decision_quality`'s `"partial"` default).
   - For each "died" event with `details.get("heir_entity_id")` truthy: if `details.get("inherited_reputation_seed")` is `None` → `reputation_inheritance_check = "fail"` (once failed, stays failed — never overwritten back to pass by a later, unrelated death); else if not already `"fail"` → `"pass"`.
   - For each "died" event with `details.get("heir_entity_id")` truthy AND `details.get("had_nemesis")` truthy: if `details.get("nemesis_transferred")` is falsy → `nemesis_transfer_check = "fail"`; else if not already `"fail"` → `"pass"`.
3. **Unit tests** in `tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py` — the 4 cases from test_plan.md, constructing `EntityArcReport(major_events=({"tick":..,"event_type":"died","details":{...}},), ...)` by hand, matching the file's existing construction style.
4. **New integration test file A** `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py` — one real `Kernel.tick_once()` test (idea 55+58), per test_plan.md piece 2.
5. **New integration test file B** `tests/integration/campaigns/test_nemesis_relation_and_chronicle_fidelity_campaign.py` — real 4-episode `CampaignOrchestrator` test (idea 55 cross-episode + idea 62), plus idea 53's reputation-inheritance test as a 3rd function in the same file (keeps all 4 "M9 ticket 1" mechanics in one clearly-labeled module, matching AC2's spirit of "one shared test surface" as closely as the real architecture allows).
6. **Docs**: add a short note to `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`'s item 1 section documenting the 3 corrections (decoupling, no cross-episode path for 55/58, idea 53/55 are unrelated mechanisms).
7. **Parity ledger**: new entry in `docs/parity_ledger/social_narrative.yaml` for the 2 new `CampaignScorecard` fields via `tools/parity_ledger_writer.py::write_entry()`.
8. Update ticket's own Implementation Notes with the 3 corrections (per orchestrator's explicit instruction), Files Changed, Completion Summary.

## Dependency Map
Step 1 → Step 2 → Step 3 (evaluator must exist before its unit tests). Steps 4/5 are independent of 1-3 (different subsystem, no shared code) and independent of each other.

## Acceptance Criteria Map
- AC1 (new fields exist) → Steps 1-2.
- AC2 (4-episode-shaped test suite exercising all 4 ideas) → Steps 4-5 (split across 2 files per the real architecture's own boundary, disclosed).
- AC3 (fail-path is real, not tautological) → Step 3's fail-path test cases.

## Unresolved Questions
None — all real architecture questions were resolved with the orchestrating session before this plan was written (see investigation.md's 3 corrections).
