---
ticket_id: TCK-20260619-E12-BALANCE-BASELINE
phase: plan
date: 2026-06-20
---

# Plan: Epic 1.2 — Balance & Tuning Baseline

## Approach

Measurement-first. Collect empirical data before changing any constants.
The existing balance observability stack (`BalanceDiagnosisEngine`, `BalanceEnvelope`,
`BaselineGenerator`) handles infrastructure — no new tooling needed.

## Child Ticket Sequence

```
E12A (measure) → E12B (recalibrate) → E12C (lock regression tests)
                                    ↗
                   E12A data feeds both E12B and E12C
```

All three are `standard` tier, `P1`. E12B and E12C both depend on E12A's measurement output.
E12C can begin skeleton test structure before E12A completes; threshold values filled in after.

## Child Ticket Files

| Ticket ID | Title | Tier | Depends On |
|---|---|---|---|
| TCK-20260619-E12A-BALANCE-MEASURE | Balance Measurement Pass | standard | prerequisites done |
| TCK-20260619-E12B-BLOCKER-RECAL | blocker_penalty Recalibration | standard | E12A |
| TCK-20260619-E12C-BALANCE-TESTS | Balance Regression Test Suite | standard | E12A + E12B |

## E12A Implementation Notes

- Use `urban_political` scenario at seed=42, tick_limit=1000, observability=LIGHT
- Collect metrics via existing `src/observability/reporting/metric_recorder.py`
- Key metrics to record per entity per 100-tick window:
  - `harvesting_events` count
  - `quest_completed` count
  - `crafting_events` count  
  - `gold_delta` (net accumulation)
  - `combat_attrition` (hp lost / max_hp)
  - `routes_with_blockers` / `total_routes_scored` ratio
  - `blocker_severity_distribution` (minor/major/critical counts)
- After run: compute aggregates, fill in D04 audit blocked sections
- Document the measured urgency range for non-hunger needs

## E12B Implementation Notes

Decision tree based on E12A data:

**If blocker frequency < 5% of scored routes:**
→ Keep `blocker_penalty = 2.0`, document with justification ("blockers rare, decisive filter appropriate")
→ No code change; parity ledger update only

**If blocker frequency ≥ 5% AND mostly minor severity:**
→ Implement graduated penalty:
  ```python
  # src/domains/adventure/scoring.py
  BLOCKER_PENALTY_BY_SEVERITY = {"minor": 0.5, "major": 1.5, "critical": 2.0}
  blocker_penalty = sum(BLOCKER_PENALTY_BY_SEVERITY.get(b.severity, 2.0) for b in route.blockers)
  blocker_penalty = min(blocker_penalty, 2.0)  # cap at current max
  ```
→ Record divergence in `docs/guidelines/v2_intentional_divergences.md`

**Either way:** Document all scoring constants in `docs/mechanics/04_strategic_cognition.md`

## E12C Implementation Notes

- File: `tests/integration/scenarios/test_balance_regression.py`
- Use same seed=42 + urban_political + 1000 ticks as E12A
- Threshold values come from E12A measurements (commit them as constants at test top)
- Mark with `@pytest.mark.slow` and `@pytest.mark.integration`
- Must pass in CI after E12B constants stabilize

## Docs to Update

- `docs/audits/D04_balance_tuning.md` → status: `done`
- `docs/mechanics/04_strategic_cognition.md` → all formula constants + justification
- `docs/mechanics/03_economic_laws.md` → economic rate baselines (if materially different from assumptions)
- `docs/parity_ledger/strategic_cognition.yaml` → STRAT-* blocker_penalty entries
- `docs/parity_ledger/town_resource.yaml` → harvesting/crafting rate entries (`v2_evidence`)
- `docs/guidelines/v2_intentional_divergences.md` → only if penalty constant changes

## Epic Completion Criteria

All three child tickets DONE and:
- `docs/audits/D04_balance_tuning.md` status = `done`
- `tests/integration/scenarios/test_balance_regression.py` exists and passes
- All scoring formula constants documented with measured justification
