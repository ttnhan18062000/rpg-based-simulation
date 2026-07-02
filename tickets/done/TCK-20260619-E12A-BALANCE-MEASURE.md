---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12A-BALANCE-MEASURE
phase: done
date: 2026-06-20
tags: [balance, measurement, observability, audit, phase-1]
---

# TCK-20260619-E12A-BALANCE-MEASURE

## Title
Epic 1.2A · Balance Measurement Pass

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
With hunger no longer dominating (P0-HUNGER-SATIATION done) and entities now differentiated (E11 done), run the deferred economic balance measurement from D04. Collect empirical baselines for all key simulation ratios that were blocked during the audit phase. These numbers feed E12B (penalty recalibration decision) and E12C (regression test thresholds).

## Scope
- Run 100-tick `urban_political` simulation at seed=42 with `ENABLE_ADVENTURE_ROUTING=ON`
- Collect per-entity per-100-tick metrics via monkey-patched `AdventureRouteScorer.score()` and `transaction_trace`
- Compute aggregates; document all in `docs/audits/D04_balance_tuning.md` (§6 added)
- Document blocker frequency and route family distribution
- Document combat attrition

## Out of Scope
- Changing any constants (that's E12B)
- Writing regression tests (that's E12C)
- Faction-level metrics

## Acceptance Criteria
- [x] `docs/audits/D04_balance_tuning.md` blocked sections filled with measured values
- [x] Harvesting rate, quest completion rate, crafting events, gold accumulation, attrition rate all documented
- [x] Blocker frequency ratio documented (0.0 — no blockers fired)
- [x] Non-hunger urgency range documented (0.0–0.0 — all routes are DEFER_WITH_REASON)
- [x] Root causes for zero economic activity identified and documented

## Related Tickets
- TCK-20260619-E12-BALANCE-BASELINE (parent epic)
- TCK-20260619-E12B-BLOCKER-RECAL (consumer of these measurements)
- TCK-20260619-E12C-BALANCE-TESTS (consumer of reference ratios)

## Related Docs
- `docs/audits/D04_balance_tuning.md` (§6 and §7 added, Key Observations updated)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E12A-BALANCE-MEASURE/` (plan, investigation, test_plan)

## Related Code Areas
- `tools/balance_measure.py` (new measurement script)
- `src/domains/adventure/scoring.py` (patched for measurement)
- `src/engine/metrics.py` (WorldMetrics)
- `src/domains/optimization/feature_flags.py` (ENABLE_ADVENTURE_ROUTING defaults OFF)

## Assumptions / Open Questions
- `urban_political` compiles with 0 resource nodes — pre-run assumption that "D08 showed harvesting events" was incorrect for current schema. New block documented.
- All entity navigation.region_id = None — documented as new block in D04 §6.2.

## Implementation Notes
Measurement executed at 100 ticks (not 1000) due to performance constraints (51.3s / 100 ticks with hash-per-tick). Full results in D04 §6.1.

Key finding: adventure routing is OFF by default via `ENABLE_ADVENTURE_ROUTING = FeatureMode.OFF` in `feature_flags.py`. Even with it enabled, urban_political has no resource nodes, so all 30 routes per entity are DEFER_WITH_REASON.

blocker_penalty = 2.0 is dead code in current production config — blocker_frequency = 0.0.

## Test Summary
Smoke test: `pytest tests/integration/worldassembly/test_e2e_smoke.py -k "urban_political"` — 1 PASSED.

## Files Changed
- `tools/balance_measure.py` — new measurement script
- `docs/audits/D04_balance_tuning.md` — §6 (E12A measurement results), §7 (blocker_penalty justification), Key Observations updated, Recommended Follow-Up updated, frontmatter updated

## Completion Summary
E12A measurement pass complete. All D04 blocked sections filled with empirical data. Root causes for zero economic activity identified: (1) adventure routing OFF by default, (2) urban_political has 0 resource nodes, (3) entity region_id=None. blocker_penalty = 2.0 is kept unchanged — it never fires in current config and cannot be empirically evaluated until resource nodes exist. E12B and E12C proceed with these findings as the baseline.
