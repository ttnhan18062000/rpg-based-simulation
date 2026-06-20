---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12A-BALANCE-MEASURE
phase: open
date: 2026-06-20
tags: [balance, measurement, observability, audit, phase-1]
---

# TCK-20260619-E12A-BALANCE-MEASURE

## Title
Epic 1.2A · Balance Measurement Pass

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
With hunger no longer dominating (P0-HUNGER-SATIATION done) and entities now differentiated (E11 done), run the deferred economic balance measurement from D04. Collect empirical baselines for all key simulation ratios that were blocked during the audit phase. These numbers feed E12B (penalty recalibration decision) and E12C (regression test thresholds).

## Scope
- Run 1000-tick `urban_political` simulation at seed=42, observability=LIGHT
- Collect per-entity per-100-tick metrics via existing `src/observability/reporting/metric_recorder.py`:
  - Harvesting events per entity per 100 ticks
  - Quest completion rate
  - Crafting conversion events
  - Net gold accumulation per entity
  - Combat attrition rate at tick 1000
  - Routes-with-blockers / total-routes-scored ratio
  - Blocker severity distribution (minor / major / critical counts)
- Compute aggregates; document all in `docs/audits/D04_balance_tuning.md` (fill blocked sections)
- Measure realistic urgency range for non-hunger needs (what's the max urgency of a crafting or trade need?)
- Cross-check against `BalanceDiagnosisEngine` findings

## Out of Scope
- Changing any constants (that's E12B)
- Writing regression tests (that's E12C)
- Faction-level metrics

## Acceptance Criteria
- `docs/audits/D04_balance_tuning.md` blocked sections filled with measured values
- Harvesting rate, quest completion rate, crafting events, gold accumulation, attrition rate all documented with actual run-data values
- Blocker frequency ratio and severity distribution documented
- Non-hunger urgency range documented (min/max observed)

## Related Tickets
- TCK-20260619-E12-BALANCE-BASELINE (parent epic)
- TCK-20260619-E12B-BLOCKER-RECAL (consumer of these measurements)
- TCK-20260619-E12C-BALANCE-TESTS (consumer of reference ratios)

## Related Docs
- `docs/audits/D04_balance_tuning.md` (fill blocked sections)
- `docs/mechanics/04_strategic_cognition.md` (urgency range to document there)

## Related Code Areas
- `src/observability/reporting/metric_recorder.py`
- `src/observability/reporting/baseline_generator.py` (`BaselineGenerator`, `BaselineThresholdSpec`)
- `src/observability/understanding/balance/engine.py` (`BalanceDiagnosisEngine`)
- `src/domains/adventure/scoring.py` (formula reference)

## Assumptions / Open Questions
- Does `urban_political` scenario exist and run cleanly post-P0 fixes? Verify before full 1000-tick run.
- Is `metric_recorder.py` already wired into the engine tick loop, or does it need explicit calls?

## Implementation Notes
Measurement-first: run the scenario, capture output, aggregate numbers, document them. Do not change any simulation constants in this ticket.

After run: if `BalanceDiagnosisEngine` flags unexpected findings (e.g., entities still hunger-cycling), log them as open questions in the D04 audit — do not attempt to fix in this ticket.

## Test Summary
No new tests. Verify the measurement run completes without error. Scope: `pytest tests/integration/scenarios/ -m "not slow" -x`.

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
