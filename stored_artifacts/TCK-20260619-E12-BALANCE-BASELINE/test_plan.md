---
ticket_id: TCK-20260619-E12-BALANCE-BASELINE
phase: test_plan
date: 2026-06-20
---

# Test Plan: Epic 1.2 — Balance & Tuning Baseline

## Test Scope

Epic-level test plan; each child ticket owns its own test changes.
The primary test deliverable is `tests/integration/scenarios/test_balance_regression.py` (E12C).

## Tests by Child Ticket

### E12A — Balance Measurement Pass

No new tests; this ticket drives a measurement run and documents outputs.
Verify measurement run completes without error:
```bash
python3 -m pytest tests/integration/scenarios/ -k "urban_political" -m "not slow" -x
```

### E12B — blocker_penalty Recalibration

If penalty constant changes:
- Unit test: `tests/unit/domains/adventure/test_scoring.py`
  - `test_minor_blocked_route_not_universally_rejected` — assert minor-blocked route with high urgency can outscore unblocked mediocre route
  - `test_critical_blocked_route_still_rejected` — critical blocker still produces near-zero score
- Parity: `docs/parity_ledger/strategic_cognition.yaml` STRAT-* entries must be `verified`

If constant unchanged: no new tests required.

### E12C — Balance Regression Test Suite

New file: `tests/integration/scenarios/test_balance_regression.py`

| Test | Assertion | Marks |
|---|---|---|
| `test_harvesting_rate_in_band` | `0.05 < harvesting_events/entity/100ticks < 0.8` (widen until E12A measurement) | slow, integration |
| `test_combat_attrition_urban_in_band` | attrition_rate < 0.60 at tick 1000 | slow, integration |
| `test_blocker_penalty_not_near_binary` | minor-blocked high-urgency route can outscore unblocked low route (only if E12B changed penalty) | slow, integration |
| `test_gold_accumulation_non_zero` | at least one entity: gold > 0 by tick 1000 | slow, integration |

## Regression Scope (existing tests to run)

After E12B (if scoring.py changes):
```bash
pytest tests/unit/domains/adventure/ -x -v
pytest tests/unit/combat/test_combat_ecology.py -x -v
pytest tests/unit/strategy/ -x -v -m "not slow"
```

After E12C:
```bash
pytest tests/integration/scenarios/test_balance_regression.py -v --timeout=120
```
