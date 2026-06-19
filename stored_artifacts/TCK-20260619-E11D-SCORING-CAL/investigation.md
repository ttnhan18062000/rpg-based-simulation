---
ticket_id: TCK-20260619-E11D-SCORING-CAL
phase: investigation
date: 2026-06-19
---

# Investigation: Calibrate Personality Bias Weights in Adventure Scoring

---

## 1. Current Scoring Formula (exact code from scoring.py)

File: `src/domains/adventure/scoring.py`

### Risk Multiplier (line 103)
```python
risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)
```
- `caution` is derived: `1.0 - bravery` (line 47)
- So for a hero with bravery=0.0: `risk_multiplier = max(0.1, 1.0 + 1.0*0.8 - 0.0*0.6) = 1.8`
- For bravery=1.0: `risk_multiplier = max(0.1, 1.0 + 0.0*0.8 - 1.0*0.6) = max(0.1, 0.4) = 0.4`
- Ratio of multipliers across full bravery range: 1.8 / 0.4 = **4.5x**

### Risk Penalty (line 104)
```python
risk_penalty = route.expected_risk * risk_multiplier * 0.5
```

### Personality Bias (lines 107–123)
None of the adventure route families in `RouteFamily` directly map to `COMBAT_ENGAGE`. The `GoalKind.COMBAT_ENGAGE` project kind is set by the `CombatEngagementDecisionPhase`, not by `AdventureRouteScorer`. The relevant route families for combat-adjacent behavior are `HUNT_WEAK_ENEMY` and `TAKE_EASY_QUEST`; neither currently receives a bravery-positive bias in the `elif` chain at lines 109–123 — the bias for those families falls through to `personality_bias = 0.0`.

### Final Score (line 134)
```python
final_score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
```
All terms rounded to 4 decimal places and clamped to `>= 0.0`.

---

## 2. Baseline Measurement (2026-06-19)

Script run against the E11C harness (SEED=42, TICKS=400, 8 heroes, 4 monsters, arena region 32x32):

```
n_heroes=8, q=2
bottom quartile bravery=[0.05, 0.48], rates=[0.0, 0.23]
top quartile bravery=[0.74, 0.79], rates=[0.138, 0.995]
bot_rate=0.1150, top_rate=0.5663, ratio=4.92x
```

**Current ratio: 4.92x** — already exceeds the 2x acceptance criterion.

### Key observations

1. The bottom quartile bravery values are [0.05, 0.48] — one entity has bravery=0.05 and a 0.0 `combat_engage` rate (it essentially never engages). The other has bravery=0.48 and a 0.23 rate.
2. The top quartile bravery values are [0.74, 0.79] — rates of 0.138 and 0.995.
3. The 4.92x ratio is driven primarily by the `CombatEngagementDecisionPhase` (separate from `AdventureRouteScorer`) whose bravery coefficient in the `EngagementRiskEvaluator` is separately tuned.
4. The `AdventureRouteScorer` bravery coefficient (currently 0.6 in the risk_multiplier) contributes to the overall effect but is not the sole mechanism driving the ratio.

---

## 3. Mechanics / Engine Constraints

Source: `docs/mechanics/04_strategic_cognition.md` (Chapter 4)

Permitted changes:
- The `risk_multiplier` formula is an implementation detail not specifically pinned in Chapter 4; the chapter establishes *that* personality traits modulate goal selection, not *exact coefficients*.
- The `personality_bias` addend per route family is configurable; adding a bravery-positive bias for `HUNT_WEAK_ENEMY` would be consistent with the spirit of Chapter 4 (bravery drives risk-seeking).

Hard constraints that must not be violated:
- Tier 1 (Survival) concerns must always dominate economic/adventure concerns: `near_death` and `flee` override scoring. The risk_multiplier `max(0.1, ...)` floor ensures a cowardly hero still considers risk (never zeroes out), preserving the survival tier semantics.
- Interruption resistance (Chapter 4, §2) is not modified by this ticket — it lives in `src/systems/strategic.py`, not `scoring.py`.
- Determinism constraint: all coefficients must be constants (no RNG in the scorer), which they are.

Source: `docs/simulation/domains/adventure_contract.md` (§Scoring)

The contract documents the formula and current coefficient values. Any coefficient change requires updating the contract doc to maintain parity.

---

## 4. Parity Ledger Overlap

File: `docs/parity_ledger/strategic_cognition.yaml`

A search through all 225 STRAT entries finds **no dedicated entry** for:
- bravery scoring coefficient in `AdventureRouteScorer`
- `personality_bias` per-family weights
- `risk_multiplier` formula constants

The closest entries are:

| ID | Text | Status |
|---|---|---|
| STRAT-035 | `test_personality_formula_impact` — personality archetypes and traits impact the capacity profile | verified |
| STRAT-103 | `test_strategic_bias_impact_on_selection` — strategic bias impact on selection | verified |
| STRAT-182 | `test_role_bias_influence` — role bias affects decisions as expected | legacy_verified |
| STRAT-183 | `test_role_aware_tactical_biases` — tactical behavior reflects role-aware biasing | legacy_verified |

None of these entries specifically cover the `AdventureRouteScorer` bravery coefficient or the `risk_multiplier` formula. There is **no existing parity ledger entry** that directly tracks the personality-scoring weights in `scoring.py`.

**Action required at implementation:** Add a new STRAT entry (e.g. `STRAT-226`) for the adventure route scorer bravery coefficient, with `status: verified`, `proof_type: parity`, and `test_path` pointing to the E11C harness test.

---

## 5. Calibration Strategy

**Current state: The ratio (4.92x) already satisfies the ≥2x acceptance criterion.**

The existing formula `risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)` produces sufficient differentiation because:
- At bravery=0.05: risk_multiplier ≈ 1.76 → heavy penalty on risky routes
- At bravery=0.79: risk_multiplier ≈ max(0.1, 1.0 + 0.21*0.8 - 0.79*0.6) = max(0.1, 0.694) ≈ 0.69

The `CombatEngagementDecisionPhase` separately uses bravery to gate engagement decisions; the two mechanisms compound.

### What to document (not change):
The coefficient `0.6` is adequately calibrated for the 2x criterion. The implementation ticket should:
1. Document the chosen bravery coefficient (0.6) and caution coefficient (0.8) with measured rationale in the ticket's Implementation Notes.
2. Add STRAT-226 parity ledger entry.
3. Remove the `xfail` marker from `test_bravery_quartile_combat_rate_2x`.
4. Update `adventure_contract.md` to call out that the coefficients are calibration-tested.

### If ratio degrades in future:
To increase ratio: raise bravery coefficient from 0.6 toward 1.0, or add a direct `personality_bias += bravery * K` for `HUNT_WEAK_ENEMY`/`TAKE_EASY_QUEST` route families.
To reduce ratio: lower bravery coefficient.
Safe range: bravery coefficient 0.4–1.2 keeps `risk_multiplier` positive across [0,1] bravery range without hitting the `max(0.1, ...)` floor for typical bravery values.

---

## 6. Risks and Open Questions

### Risk 1: Fragile bot_rate=0.0 entity
The entity with bravery=0.05 has a 0.0 `combat_engage` rate. If that entity appears in a different seed run or if arena entity counts change, `bot_rate` could drop to 0.0, triggering the harness assertion `assert bottom_rate > 0`. The ratio is not the binding risk; the bottom-rate > 0 precondition is.

Mitigation: do not change entity count or seed in E11C harness without re-running the measurement.

### Risk 2: combat_engage rate vs. bravery independence
The `CombatEngagementDecisionPhase` drives `GoalKind.COMBAT_ENGAGE` — it is separate from `AdventureRouteScorer`. The bravery used by the combat engagement domain's `EngagementRiskEvaluator` is the dominant driver of the ratio. If that phase is later recalibrated independently, the E11D relationship changes.

### Risk 3: Route family mismatch
`AdventureRouteScorer` does not handle `HUNT_WEAK_ENEMY` in its personality_bias elif chain — if `HUNT_WEAK_ENEMY` routes are generated more frequently, the bravery effect from `scoring.py` has no additive bias term, relying entirely on `risk_multiplier`. This is documented as a known gap; adding a `bravery * 0.25` bias for `HUNT_WEAK_ENEMY` would strengthen trait differentiation without violating mechanics constraints.

### Open Question
The test harness uses `ent.kind.lower() == 'hero'` to filter entities. The `EntityRole` enum (`src/core/enums.py`) has `HERO`. Check that `kind` is always lowercase 'hero' for consistency with `EntityRole.HERO` check in the harness.

---

## 7. Anti-Drift Hazards

1. **Do not change SEED or TICKS** in `test_entity_differentiation.py` without re-running this measurement. The ratio at SEED=42 is 4.92x; a new seed may produce a different distribution.
2. **`caution` is a derived trait** (1.0 - bravery). Do not add `caution` as a direct field to `PersonalityComponent` — it would require updating both the scorer's `get_trait` function and the formula.
3. **The `elif` ordering bug** (greed before industry) documented in `adventure_contract.md` must not be fixed in this ticket — it is out-of-scope and could affect existing test baselines.
4. **The `max(0.1, ...)` floor** in `risk_multiplier` must be preserved: it ensures even maximally-brave heroes retain a non-zero risk penalty (survival tier dominance).
5. **xfail removal is the primary deliverable**: the test exists and passes with 4.92x ratio; the only code change required may be removing the xfail decorator — confirm the test passes strictly before marking STRAT-226 as `verified`.
