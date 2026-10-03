---
ticket_id: TCK-20260619-E11D-SCORING-CAL
phase: test_plan
date: 2026-06-19
---

# Test Plan: E11D — Calibrate Personality Bias Weights

---

## Objective

Verify that after this ticket:
1. `test_bravery_quartile_combat_rate_2x` passes **strictly** (xfail marker removed).
2. All existing adventure scoring unit tests continue to pass (no regressions).
3. The parity ledger entry STRAT-226 is added and correctly references the test.

---

## Test Scope

### Primary acceptance test

| Test | File | Expected outcome |
|---|---|---|
| `test_bravery_quartile_combat_rate_2x` | `tests/integration/scenarios/test_entity_differentiation.py` | PASS (no xfail) — ratio >= 2.0x |

**Run command:**
```
pytest tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x -v
```

**Acceptance criterion:** `top_rate >= 2.0 * bottom_rate` AND `bottom_rate > 0`.

Current measured baseline (SEED=42, TICKS=400): ratio = **4.92x** (bot_rate=0.1150, top_rate=0.5663).

---

### Regression surface: adventure scoring unit tests

| Test | File | Guards |
|---|---|---|
| `test_healing_need_outranks_upgrade_when_hp_critical` | `tests/unit/domains/adventure/test_phase3_route_scoring.py` | Survival-tier need > growth; must still hold |
| `test_greedy_entity_prefers_gold_route_when_risk_equal` | same | `greed * 0.25` personality_bias for GATHER_RESOURCE |
| `test_cautious_entity_prefers_recover_before_hunt` | same | caution-derived bravery effect; risk_multiplier differential |
| `test_curious_entity_prefers_information_when_unknown_exists` | same | curiosity bias for ASK_INFORMATION |
| `test_industrious_entity_prefers_craft_route_when_feasible` | same | industry bias for CRAFT_UPGRADE |
| `test_scoring_does_not_use_hidden_world_truth` | same | scorer reads only entity self-model |
| `test_route_scoring_is_deterministic` | same | determinism invariant |

**Run command:**
```
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -v
```

All must PASS with no changes.

---

### Secondary test: unique personality vectors at spawn

| Test | File | Expected outcome |
|---|---|---|
| `test_no_identical_personality_vectors_at_spawn` | `tests/integration/scenarios/test_entity_differentiation.py` | PASS (already strict) |

**Run command:**
```
pytest tests/integration/scenarios/test_entity_differentiation.py::test_no_identical_personality_vectors_at_spawn -v
```

---

## Formula Regression Check

If `bravery * 0.6` coefficient changes, manually verify these boundary conditions:

| Bravery | Caution | risk_multiplier | Notes |
|---|---|---|---|
| 0.0 | 1.0 | `max(0.1, 1.0 + 0.8 - 0.0) = 1.8` | Most cautious; highest risk penalty |
| 0.5 | 0.5 | `max(0.1, 1.0 + 0.4 - 0.3) = 1.1` | Neutral; modest risk penalty |
| 1.0 | 0.0 | `max(0.1, 1.0 + 0.0 - 0.6) = 0.4` | Most brave; lowest risk penalty |
| 0.9+ | ~0.1 | `max(0.1, 1.0 + 0.08 - 0.54) = 0.54` | High bravery; well above floor |

The `max(0.1, ...)` floor must not be reached for any bravery value in [0.0, 1.0] except at extremes. Current coefficient preserves this.

---

## Parity Ledger Test Coverage

After adding STRAT-226 to `docs/parity_ledger/strategic_cognition.yaml`:

Verify the entry is syntactically valid YAML with all required fields:
```
- id: STRAT-226
  text: ...
  status: verified
  priority: P1
  v2_evidence: ...
  proof_type: parity
  test_path: tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x
```

**Check command:**
```
python3 -c "import yaml; data = yaml.safe_load(open('docs/parity_ledger/strategic_cognition.yaml')); ids = [e['id'] for e in data]; assert 'STRAT-226' in ids, 'STRAT-226 missing'; print('OK:', len(data), 'entries')"
```

---

## Edge Cases to Verify

1. **bottom_rate > 0 precondition**: The harness asserts `bottom_rate > 0` before the 2x comparison. If the bottom-quartile entity with bravery=0.05 never takes a `combat_engage` project, the test fails with the diagnostic assertion rather than the ratio assertion. Confirm this entity picks at least 1 `combat_engage` tick across 400 ticks.

   With SEED=42 the measured bot_rate=0.1150 satisfies this (not 0.0 at group level; the individual entity at bravery=0.05 had rate=0.0 but the group average includes the bravery=0.48 entity).

2. **xfail removal**: The `@pytest.mark.xfail(strict=False, ...)` decorator must be replaced with no mark (or `@pytest.mark.integration @pytest.mark.slow`). After removal, a failure becomes a hard FAIL, not an xfail. Confirm test passes before removing the decorator.

3. **Determinism across reruns**: Run the harness twice with the same seed and confirm identical output. The RNG is seeded via `DeterministicRNG(42)` so this should be stable.

---

## Execution Order

1. Run regression suite first (fast): `pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -v`
2. Run the full integration test (slow, 400 ticks): `pytest tests/integration/scenarios/test_entity_differentiation.py -v -m integration`
3. Verify parity YAML entry is valid.
4. Confirm no other tests in the adventure domain broke: `pytest tests/unit/domains/adventure/ -v`

---

## Non-Goals for This Test Plan

- Performance benchmarks (tick budget is not a test criterion here)
- Full suite execution (`pytest tests/` is explicitly out of scope)
- Testing `CombatEngagementDecisionPhase` bravery tuning (separate domain)
- Testing non-bravery personality traits (greed, industry, sociability) beyond regression
