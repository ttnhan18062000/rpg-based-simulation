---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12-BALANCE-BASELINE
phase: done
date: 2026-06-19
tags: [balance, tuning, scoring, blocker-penalty, regression-tests, epic, phase-1]
---

# TCK-20260619-E12-BALANCE-BASELINE

## Title
Epic 1.2 · Balance & Tuning Baseline

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Economic/crafting balance is unmeasurable because hunger dominates (D06 F1, fixed by P0-3). The `blocker_penalty = 2.0` fixed constant is near-binary — max non-blocked score is ~2.65, so any blocked route is near-universally rejected. After P0-3, a full balance measurement pass is needed to establish documented baselines with regression tests.

Score: 8/10 · Effort: M · Source: `docs/audits/D04_balance_tuning.md`

## Scope
- **Prerequisites:** TCK-20260619-P0-HUNGER-SATIATION complete ✓; TCK-20260619-P0-ENTITY-INIT complete ✓
- Run D04 completion: 1000-tick `urban_political` runs measuring gold accumulation rate, harvesting frequency per entity-hour, quest completion rate, crafting conversion, combat attrition rate
- Audit `blocker_penalty = 2.0` in `src/domains/adventure/scoring.py`: if max non-blocked score is ~2.65, 2.0 may be too severe — consider graduated penalty curve or tiered penalty by blocker severity
- Audit hunger urgency vs. benefit calibration: does completing a food-provision opportunity score above the next hunger project?
- Write balance regression tests: reference-run locked assertions on key ratios (e.g. `0.1 < harvesting_rate < 0.5` per entity per 100 ticks)
- Document all scoring formula constants in `docs/mechanics/04_strategic_cognition.md` with justification
- Promote D04 audit detail file from `partial` to `done`
- Child tickets: (a) measurement pass + metric collection, (b) blocker_penalty recalibration, (c) regression test suite

## Out of Scope
- Faction-level supply/demand (Phase 5)
- Full economic macro-model (Epic 3.3)
- Personality calibration (Epic 1.1 scope)

## Acceptance Criteria
- `docs/audits/D04_balance_tuning.md` promoted to status=done
- All scoring formula constants documented in `docs/mechanics/04_strategic_cognition.md`
- Balance regression tests run in CI; reference ratios locked
- At least one economic event (harvesting, crafting, or trade) observable per entity per 100-tick window in a 1000-tick `urban_political` run

## Related Tickets
- TCK-20260619-P0-HUNGER-SATIATION (prerequisite — DONE)
- TCK-20260619-P0-ENTITY-INIT (prerequisite — DONE)
- TCK-20260619-E11-ENTITY-IDENTITY (prerequisite for personality-driven route differentiation measurement — DONE)
- **TCK-20260619-E12A-BALANCE-MEASURE** (child — measurement pass + metric collection)
- **TCK-20260619-E12B-BLOCKER-RECAL** (child — blocker_penalty recalibration)
- **TCK-20260619-E12C-BALANCE-TESTS** (child — balance regression test suite)

## Related Docs
- `docs/audits/D04_balance_tuning.md` (promote status to `done` on completion)
- `docs/mechanics/04_strategic_cognition.md` (document all formula constants with rationale)
- `docs/mechanics/03_economic_laws.md` (update if economic rate baselines change)
- `docs/plans/long_term_development_roadmap.md` § Epic 1.2
- `docs/parity_ledger/strategic_cognition.yaml` (scoring formula entries — update blocker_penalty entry if changed)
- `docs/parity_ledger/town_resource.yaml` (harvesting/crafting rate entries — add baseline measurement as `v2_evidence`)
- `docs/plans/idea_cognition_graph_analytics_pipeline.md` (idea: wire `CognitionFeatureExtractor` into post-run pipeline before this epic's measurement pass)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/domains/adventure/scoring.py:L131` (`blocker_penalty = 2.0` constant)
- `src/observability/reporting/baseline_generator.py` (BaselineGenerator, BaselineThresholdSpec)
- `src/observability/understanding/balance/engine.py` (BalanceDiagnosisEngine)
- `src/observability/reporting/balance_envelope.py` (BalanceEnvelope)

## Assumptions / Open Questions
- What is the realistic urgency range for non-hunger needs? → answered by E12A measurement pass
- Should blocker_penalty be a graduated function of blocker severity? → decided in E12B based on E12A data

## Implementation Notes
See `staging_artifacts/TCK-20260619-E12-BALANCE-BASELINE/plan.md` for child ticket sequencing and implementation notes.

## Test Summary
Regression tests are the primary deliverable of E12C. Each test asserts that a key ratio stays within an empirically-derived band (values locked by E12A run data), run against a reference seed.

## Files Changed
_To be filled when child tickets complete._

## Completion Summary
_Epic completes when E12A + E12B + E12C are all DONE._ This epic-scoped ticket closes now that all
three child tickets are complete.
