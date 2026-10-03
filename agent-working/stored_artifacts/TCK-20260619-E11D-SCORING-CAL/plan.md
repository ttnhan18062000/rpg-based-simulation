---
ticket_id: TCK-20260619-E11D-SCORING-CAL
phase: plan
date: 2026-06-19
---

# Plan: E11D — Calibrate Personality Bias Weights in Adventure Scoring

---

## Scope Guard

**No scoring formula changes are permitted.** The baseline measurement (SEED=42, TICKS=400) confirms the existing bravery coefficient (0.6) and caution coefficient (0.8) already produce a 4.92× combat_engage rate ratio — well above the ≥2× acceptance criterion. All deliverables are documentation, parity ledger, and test-marker changes only.

---

## Dependency Map

```
Step 1 (confirm test passes strictly)
    └── Step 2 (remove xfail marker)           [depends on Step 1 pass confirmation]
        └── Step 3 (add STRAT-226 to ledger)   [independent of Step 2, but logically after]
            └── Step 4 (update adventure_contract.md)  [independent; document facts already known]
                └── Step 5 (regression: unit tests)    [depends on Steps 2+4 complete]
                    └── Step 6 (regression: integration) [depends on Step 2 complete]
                        └── Step 7 (ticket finalization) [depends on all prior steps]
```

Steps 3 and 4 have no code dependency on each other and may be done in parallel after Step 2.

---

## Ordered Steps

### Step 1 — Confirm test passes strictly before marker removal

**Purpose:** Verify the current test body produces PASS (not merely XPASS) before removing the safety net.

**Action:**
Run the integration test without changing any source, observing that it exits with status XPASS (passing under xfail — which means the body passes):
```
pytest tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x -v
```
Expected: `XPASS` (xfail strict=False, body passes). If the result is `XFAIL` (body still fails), stop — do not proceed to Step 2.

**Files read:** `tests/integration/scenarios/test_entity_differentiation.py` (read-only, no edits)

**AC mapped:** Pre-condition for AC-1 (test must pass strictly after marker removal)

---

### Step 2 — Remove `@pytest.mark.xfail` decorator from `test_bravery_quartile_combat_rate_2x`

**Purpose:** Promote the test to strict-pass status so any future regression produces a hard FAIL.

**File:** `tests/integration/scenarios/test_entity_differentiation.py`

**Change:** Remove lines:
```python
@pytest.mark.xfail(
    strict=False,
    reason="...",
)
```
Retain `@pytest.mark.slow` and `@pytest.mark.integration` decorators unchanged.

Also update the test docstring: replace the sentence "Marked xfail(strict=False) until E11D calibrates the bravery coefficient. Either xfail or xpass is acceptable; a crash or import error is not." with "Strict-pass test (E11D confirmed 4.92× ratio at SEED=42, TICKS=400 — bravery coefficient 0.6, caution coefficient 0.8)."

**Scope guard:** No changes to test logic, fixture, SEED, TICKS, entity counts, or assertion thresholds.

**AC mapped:** AC-1 — `test_bravery_quartile_combat_rate_2x` passes strictly (no xfail)

---

### Step 3 — Add STRAT-226 to `docs/parity_ledger/strategic_cognition.yaml`

**Purpose:** Record the adventure route scorer bravery/caution coefficients as a verified parity entry, closing the ledger gap identified in the investigation.

**File:** `docs/parity_ledger/strategic_cognition.yaml`

**Action:** Append the following entry after STRAT-225:
```yaml
- id: STRAT-226
  text: >-
    AdventureRouteScorer applies a bravery/caution risk multiplier
    (max(0.1, (1.0 + caution×0.8) - bravery×0.6)) that produces ≥2× combat_engage
    rate differential between bottom and top bravery quartiles (measured 4.92× at
    SEED=42, TICKS=400, 8 heroes).
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >-
    src/domains/adventure/scoring.py line 103 — bravery coefficient 0.6, caution
    coefficient 0.8, floor max(0.1,...) preserved; measured 4.92× ratio confirmed
    by E11D investigation (TCK-20260619-E11D-SCORING-CAL).
  proof_type: parity
  test_path: tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x
  divergence_note: null
  support_boundary: null
```

**Validation command (run after write):**
```
python3 -c "import yaml; data = yaml.safe_load(open('docs/parity_ledger/strategic_cognition.yaml')); ids = [e['id'] for e in data]; assert 'STRAT-226' in ids, 'STRAT-226 missing'; print('OK:', len(data), 'entries')"
```

**AC mapped:** AC-3 — Parity ledger personality-scoring entries updated to `verified`

---

### Step 4 — Update `docs/simulation/domains/adventure_contract.md`

**Purpose:** Document that the bravery coefficient (0.6) and caution coefficient (0.8) in the risk_multiplier formula are calibration-tested, with the measured baseline, so the contract is in full parity with the code.

**File:** `docs/simulation/domains/adventure_contract.md`

**Action:** In the Scoring section, locate the risk_multiplier row in the formula table (currently: `risk_multiplier = max(0.1, (1.0 + caution×0.8) - bravery×0.6)`). Add a **Calibration note** subsection immediately after the formula table:

```markdown
#### Calibration Note (E11D, 2026-06-19)

The bravery coefficient (`0.6`) and caution coefficient (`0.8`) are calibration-tested.
Measured baseline: SEED=42, TICKS=400, 8 heroes → **4.92× combat_engage rate ratio**
between bottom and top bravery quartiles (acceptance criterion: ≥2×).

- At bravery=0.0 (caution=1.0): `risk_multiplier = 1.8` (maximum risk aversion)
- At bravery=1.0 (caution=0.0): `risk_multiplier = 0.4` (minimum risk aversion, floor preserved)
- The `max(0.1, …)` floor ensures survival-tier dominance is never zeroed out.

Parity ledger entry: STRAT-226 (`docs/parity_ledger/strategic_cognition.yaml`).
```

**Scope guard:** Do not fix the `elif` ordering (greed before industry) noted in the investigation — that is out of scope and could affect existing test baselines.

**AC mapped:** AC-2 — Bravery coefficient documented (contract doc is the authoritative location for formula parameters)

---

### Step 5 — Run adventure scoring unit tests (regression check)

**Purpose:** Confirm no regression in unit-level scoring behavior after Step 4 doc-only changes (and as a baseline guard if any accidental edit occurred).

**Command:**
```
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -v
pytest tests/unit/domains/adventure/ -v
```

**Expected:** All tests PASS. Zero failures, zero errors.

**AC mapped:** AC-1 (regression guard — no existing tests broken)

---

### Step 6 — Run integration harness strictly (final acceptance verification)

**Purpose:** Confirm `test_bravery_quartile_combat_rate_2x` now shows as PASS (not XPASS) after the marker removal in Step 2, and that `test_no_identical_personality_vectors_at_spawn` still passes.

**Command:**
```
pytest tests/integration/scenarios/test_entity_differentiation.py -v -m "integration and slow"
```

**Expected:**
- `test_bravery_quartile_combat_rate_2x` → PASSED
- `test_no_identical_personality_vectors_at_spawn` → PASSED

**AC mapped:** AC-1 — `test_bravery_quartile_combat_rate_2x` passes strictly (no xfail)

---

### Step 7 — Finalize ticket and working log

**Purpose:** Close the ticket per Definition of Done.

**Actions (in order):**

1. Fill **Implementation Notes** in `tickets/inprogress/TCK-20260619-E11D-SCORING-CAL.md`:
   - Bravery coefficient: `0.6`; caution coefficient: `0.8`
   - Formula: `risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)`
   - Measured ratio: 4.92× at SEED=42, TICKS=400 — no coefficient changes required
   - No formula changes made; deliverables are test marker removal, parity ledger entry, and contract doc update

2. Fill **Files Changed**, **Test Summary**, and **Completion Summary** sections.

3. Update **Status** to `DONE`.

4. Move ticket: `tickets/inprogress/TCK-20260619-E11D-SCORING-CAL.md` → `tickets/done/TCK-20260619-E11D-SCORING-CAL.md`

5. Move staging artifacts: `staging_artifacts/TCK-20260619-E11D-SCORING-CAL/` → `stored_artifacts/TCK-20260619-E11D-SCORING-CAL/` (include `plan.md`, `investigation.md`, `test_plan.md`)

6. Append to `tickets/working_log.csv` (bottom only, never insert):
   ```
   TCK-20260619-E11D-SCORING-CAL,E11-D · Calibrate personality bias weights in adventure scoring,DONE,2026-06-19,standard,feature,P1,simulation
   ```

7. Run `make knowledge-index-update` (docs under `docs/` were modified in Steps 3 and 4).

8. Write agent-monitoring records:
   - Append run entry to `agent-monitoring/runs.jsonl`
   - Append at least one event entry to `agent-monitoring/events.jsonl`

9. Clean up: `rm -rf data/runs/* reports/release_proof/*`

**AC mapped:** All ACs (Definition of Done gate)

---

## Acceptance Criteria → Step Mapping

| AC | Description | Covered by |
|---|---|---|
| AC-1 | `test_bravery_quartile_combat_rate_2x` passes strictly (no xfail) | Steps 1, 2, 6 |
| AC-2 | Bravery coefficient documented in Implementation Notes | Steps 4, 7 |
| AC-3 | Parity ledger personality-scoring entries updated to `verified` | Step 3 |

---

## Files Changed (complete list)

| File | Change type |
|---|---|
| `tests/integration/scenarios/test_entity_differentiation.py` | Edit — remove `@pytest.mark.xfail(...)` decorator, update docstring |
| `docs/parity_ledger/strategic_cognition.yaml` | Edit — append STRAT-226 entry |
| `docs/simulation/domains/adventure_contract.md` | Edit — add Calibration Note subsection to Scoring section |
| `tickets/inprogress/TCK-20260619-E11D-SCORING-CAL.md` → `tickets/done/` | Edit + move |
| `tickets/working_log.csv` | Append |
| `staging_artifacts/TCK-20260619-E11D-SCORING-CAL/` → `stored_artifacts/` | Move |
| `agent-monitoring/runs.jsonl` | Append |
| `agent-monitoring/events.jsonl` | Append |

---

## Deviations from Plan

### Step 1 — XFAIL instead of XPASS (pre-existing E11C harness defects)

The plan assumed Step 1 would confirm XPASS. Instead the test was XFAIL due to two pre-existing defects in the E11C harness that were never triggered because the test was always xfail:

1. **Tick-padding sleep**: `_test_profile()` sets `max_tick_budget_ms=200.0`. The kernel sleeps to pad each tick to 200ms. 400 ticks × 200ms = 80s minimum wall time, exceeding the 60s conftest `medium` timeout. Fix: added `"no_frame_pacing": True` to the kernel flags dict — a supported flag already gated at `kernel.py:329`.

2. **QueueDrainWorker thread leak**: The kernel was never shut down after the tick loop, leaving a background drain-worker thread alive past the test session, triggering the session-scoped sentinel in conftest. Fix: wrapped the tick loop in `try/finally: kernel.shutdown()`, matching the pattern used in all other Kernel-creating tests.

Neither fix changes test logic, seed, tick count, entity count, or assertion thresholds — both are infrastructure corrections required to make the test runnable under the production conftest constraints. The 4.92× ratio is confirmed (test passes in 2.95s after fixes).
