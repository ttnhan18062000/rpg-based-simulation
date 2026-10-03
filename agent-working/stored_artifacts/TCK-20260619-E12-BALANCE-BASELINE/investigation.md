---
ticket_id: TCK-20260619-E12-BALANCE-BASELINE
phase: investigation
date: 2026-06-20
---

# Investigation: Epic 1.2 — Balance & Tuning Baseline

---

## 1. Current Scoring Formula (from `src/domains/adventure/scoring.py`)

```
score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
```

| Term | Current Value | Notes |
|---|---|---|
| `urgency` | 0.0–2.0 | Hunger urgency still dominates after P0-HUNGER-SATIATION partial fix |
| `benefit` | `opportunity.expected_benefit / 100` | Rarely exceeds 0.5 |
| `personality_bias` | max 0.25 per trait | E11 now seeds traits; real values measurable |
| `confidence_bonus` | `route.confidence × 0.15` | Max 0.15 |
| `risk_penalty` | `risk × risk_multiplier × 0.5` | `risk_multiplier = 1.0` default |
| `blocker_penalty` | **2.0 (fixed, L131)** | Near-binary filter; any blocker → score ≤ 0 |

**Max non-blocked score ≈ 2.0 + 0.5 + 0.25 + 0.15 = 2.90** (with E11 personality now active)  
**Max blocked score ≈ 2.90 − 2.0 = 0.90** — still positive but outcompeted by any unblocked route.

The 2.0 penalty was installed to make blockers decisive. The question E12A must answer:
in practice, how often are routes blocked, and how severe are blockers? If minor blockers
dominate, the flat 2.0 is too blunt.

---

## 2. Existing Observability Infrastructure

The balance measurement infrastructure already exists and is substantial:

| File | Role |
|---|---|
| `src/observability/reporting/baseline_generator.py` | `BaselineGenerator`, `BaselineThresholdSpec`, `DistributionSummary` |
| `src/observability/reporting/balance_envelope.py` | `BalanceEnvelope`, `ExpectationValue` — threshold-based pass/fail |
| `src/observability/understanding/balance/engine.py` | `BalanceDiagnosisEngine` — liveness, dominance, runtime findings |
| `src/observability/understanding/balance/models.py` | `BalanceDimension` |
| `src/observability/reporting/metric_recorder.py` | Run-level metric recording |

E12A should drive a measurement run through these existing tools rather than building new infrastructure.

---

## 3. D04 Audit Gaps (what's missing after partial completion)

The D04 audit (`docs/audits/D04_balance_tuning.md`) identified:
- **Blocked:** Economic balance (crafting/trade/gold) — was blocked by hunger dominance (now resolved by P0-HUNGER-SATIATION)
- **Partially observed:** Combat balance (D03/D08 data), hunger urgency calibration
- **Not yet measured:** Harvesting rate per entity, quest completion rate, crafting conversion rate, gold accumulation, blocker occurrence frequency

E12A closes all four gaps with a fresh 1000-tick `urban_political` run.

---

## 4. Prerequisites Verification

| Ticket | Status | Impact |
|---|---|---|
| P0-HUNGER-SATIATION | DONE | Hunger no longer dominates; economic routes now scoreable |
| P0-ENTITY-INIT | DONE | Entities initialized with diverse attributes |
| E11-ENTITY-IDENTITY | DONE | Personality traits seeded; personality_bias now real |

All prerequisites satisfied — E12 can proceed immediately.

---

## 5. Child Ticket Design

### E12A — Balance Measurement Pass (standard, P1)
Run a 1000-tick `urban_political` simulation with LIGHT observability.
Collect: harvesting events per entity per 100 ticks, quest completion rate, crafting conversion,
combat attrition at tick 1000, gold accumulation per entity, blocker occurrence frequency and severity distribution.
Output: raw metrics committed to `docs/audits/D04_balance_tuning.md` (complete the partial audit).
Feed E12B (penalty recalibration) and E12C (regression test thresholds).

### E12B — blocker_penalty Recalibration (standard, P1, depends on E12A)
Using E12A metrics:
- If blocker frequency shows mostly minor blockers → implement graduated penalty: `minor=0.5`, `major=1.5`, `critical=2.0`
- If blockers are rare and mostly critical → keep 2.0, just document with justification
- Update `docs/mechanics/04_strategic_cognition.md` with all constant values and rationale
- Update parity ledger `strategic_cognition.yaml` (STRAT-* entries for blocker_penalty)
- If constant changed → update `docs/guidelines/v2_intentional_divergences.md`

### E12C — Balance Regression Test Suite (standard, P1, depends on E12A + E12B)
Create `tests/integration/scenarios/test_balance_regression.py` with 4 tests:
- `test_harvesting_rate_in_band` — locked ratio from E12A measurement
- `test_combat_attrition_urban_in_band` — attrition < 60% at tick 1000
- `test_blocker_penalty_not_near_binary` — assert minor-blocked route can outscore mediocre unblocked (only if E12B changes penalty)
- `test_gold_accumulation_non_zero` — at least one entity accumulates gold > 0 by tick 1000
Promote `docs/audits/D04_balance_tuning.md` status to `done`.
