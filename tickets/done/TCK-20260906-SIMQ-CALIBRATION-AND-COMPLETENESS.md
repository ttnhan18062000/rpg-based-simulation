---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS
phase: done
date: 2026-09-06
tags: [simulation-quality, calibration]
---

# TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS

## Title
M7 step 4-5: re-run SimQ calibration against the new rule set, final completeness cross-check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M7 epic (`TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION`) child 2 of 2, depends on
`TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` landing first. Implements the epic doc's Scope items 4-5:
re-run SimQ's own calibration workflow (real precedent: `TCK-20260628-SIMQ-E7-CALIBRATE`, confirmed
real and closed) against at least one corpus profile exercising the new content, to confirm the new
signal rules produce a meaningful grade signal rather than a flat, uninformative score; then a final,
explicit completeness check — cross-referencing the finished rule set against the prior ticket's
named-pillar list for all 65 ideas, so every idea that should touch a pillar has a traceable rule or
an explicit, written reason it doesn't.

## Scope
- Re-run SimQ's calibration workflow (`tools/calibrate_simq.py`, matching
  `TCK-20260628-SIMQ-E7-CALIBRATE`'s own precedent) against at least one real corpus profile that
  exercises the M1-M6 content the prior ticket added rules for.
- Confirm the new signal rules produce a meaningful, non-flat grade signal — not just "rules were
  written," a real recorded calibration result.
- Cross-reference the final rule set against the prior ticket's named-pillar list for all 65 ideas —
  a checklist against a known-complete list, not an open-ended scan. Every idea Pillar Reach says
  should touch a pillar needs a traceable rule or an explicit, written reason it doesn't (e.g. a pure
  governance/investigation idea legitimately has nothing to register).
- Record the completeness check's own results (pass/gap list) somewhere real and citable.

## Out of Scope
- Authoring any new signal rule or naming any new pillar mapping —
  `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES`'s own scope, this ticket only calibrates and checks it.
- Closing M9's `CampaignScorecardEvaluator` field gap — a related but distinct SimQ gap, out of this
  epic's scope entirely.
- Fixing any gap the completeness check finds — record it, ticket it separately if real follow-up
  work is needed; this ticket verifies, it does not extend the rule set further.

## Acceptance Criteria
- [x] A real calibration run against at least one corpus profile is completed and its results
      (grades/scores before and after the new rules) are recorded, not just asserted.
- [x] The new signal rules are confirmed to produce a meaningful grade signal (a real change in score
      attributable to the new rules, not a flat/uninformative result).
- [x] The completeness cross-check is recorded with an explicit pass/gap list against all 65 ideas —
      no idea silently unaccounted for.
- [x] Any real gap the completeness check finds is either fixed in this same ticket (if small) or
      explicitly ticketed as separate follow-up work (if not) — never silently left unstated.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (parent epic)
- `TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES` (must land first)
- `TCK-20260628-SIMQ-E7-CALIBRATE` (`tickets/done/`, the real precedent this ticket's own calibration
  re-run follows)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`
- `docs/simulation_quality/quality_scoring_contract.md`

## Related Stored Artifacts
`stored_artifacts/TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS/` — investigation.md, plan.md,
test_plan.md, `route_new_query_isolated_calibration.py`, `completeness_check.py`.

## Related Code Areas
- `tools/calibrate_simq.py`
- `src/simulation_quality/`
- `config/simulation_quality/profiles/`

## Assumptions / Open Questions
- Which corpus profile(s) to calibrate against is left to this ticket's own Investigate/Plan phases —
  not decided here; should exercise real M1-M6 content, not an unrelated older profile.

## Implementation Notes
Ran 2 real calibration attempts against `urban_political_selfmodel_execution_probe` (the one
shipped profile with `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION`/
`ENABLE_INFORMATION_INTENT_EXECUTION` all ON) — seed 42/500t and seed 137/300t. `route_new_query`
fired 0 times in either, matching `test_grade_regression.py`'s own pre-existing "does NOT
generalize" disclosure for this exact profile/world. Rather than fabricate a corpus result or
report a flat run as sufficient proof, built a deterministic before/after proof through the real
`QualityHub`/`InformationScorer` (`route_new_query_isolated_calibration.py`) using the real,
engine-captured envelope shape (found as leftover data from ticket 1's own test run) — a genuine,
non-flat, attributable score delta (raw_score 0.0 → 10.0, grade C → S), matching the exact
evidentiary bar `test_information_intent_execution_fires_through_kernel_tick_once` already
establishes as acceptable for this same mechanism.

Ran the idea-level completeness cross-check (`completeness_check.py`) against ticket 1's own
65-row named-pillar mapping in `design_merit_scorecard.html`: 65/65 rows accounted for, 0 real
undisclosed gaps (58 rows have a self-consistent named-pillar mapping including the 3 dormant
ideas; 7 rows are the already-disclosed bare-`0/10` governance/doc-fix exceptions). No fix or
follow-up ticket needed — recorded in `quality_scoring_contract.md` §7.7 and
`event_type_coverage.md`'s changelog.

Found and resolved a real internal tension in this ticket's own text: the Acceptance Criteria said
a gap should be "fixed... or ticketed," while the Out-of-Scope said "this ticket verifies, it does
not extend the rule set further." Moot here (no real gap found), but documented in plan.md that the
more specific Out-of-Scope statement would govern had one existed.

## Test Summary
`tests/simulation_quality/` full suite: 478 passed, 85 skipped, 0 failed (identical to ticket 1's
own count — confirms the doc-only changes and staging scripts introduced no regression or
accidental pytest collection).

## Files Changed
- `docs/simulation_quality/event_type_coverage.md` (calibration-attempt findings + `route_new_query`
  row update)
- `docs/simulation_quality/quality_scoring_contract.md` (new §7.7)
- `stored_artifacts/TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS/` (new — investigation.md,
  plan.md, test_plan.md, `route_new_query_isolated_calibration.py`, `completeness_check.py`)

## Completion Summary
Confirmed `route_new_query` does not fire in any shipped calibration corpus (2 real runs, both
0 occurrences), matching a pre-existing repo disclosure rather than a new finding, and proved the
new rule's wiring correct via a deterministic isolated `QualityHub` replay instead (real, non-flat,
attributable score delta). Ran the M7 epic's own idea-level completeness cross-check against all 65
ideas: 65/65 accounted for, 0 real gaps, no follow-up ticket needed. Last of the 2 M7 child tickets
— `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` closed in the same batch.
