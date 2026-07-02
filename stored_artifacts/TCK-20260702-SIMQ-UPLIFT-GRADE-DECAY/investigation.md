# Investigation: TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY

**Date:** 2026-07-02  
**Ticket:** TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY  
**Investigator phase:** seq 2

---

## Current Behavior

### Formula Location

The `normalized_score` formula lives in `src/simulation_quality/quality_report.py`, line 101 (`QualityReportBuilder.build`):

```python
effective_tick = max(1, current_tick)
# ...
normalized_score = snap["raw_score"] / effective_tick
```

This is passed to `_assign_grade(normalized_score, weights.grade_thresholds)` at line 102.

The `PillarAccumulator` (`src/simulation_quality/pillar_accumulator.py`) stores only `raw_score` and `event_count` — it has no knowledge of tick count. The division happens at report-build time only, not during accumulation. The `pillar_accumulator.py` file the ticket referenced as `accumulator.py` does not exist; the real file is `pillar_accumulator.py`.

### Contract Statement Under Investigation

`docs/simulation_quality/quality_scoring_contract.md` §4.4:

> ```
> normalized_score = raw_score / max(1, current_tick)
> ```
> Makes short and long runs comparable.

`current_tick` is the final tick count of the entire run — not the tick of the last scored event. This is the root of the decay.

---

## Evidence: H2 Confirmed — Same Raw Score, Different Grade

The following numbers come directly from `data/calibration/*/quality_report.json`. Note: the "500t" run actually terminated at tick 401 (the run stopped early — the key name uses the nominal target, not the actual tick reached).

### COMBAT pillar

| Run key | tick_count (actual) | raw_score | event_count | last_event_tick | normalized_score | grade |
|---|---|---|---|---|---|---|
| dungeon_crawl_seed42_200t | 200 | 127.0 | 65 | 172 | 0.6350 | **A** |
| dungeon_crawl_seed42_500t | 401 | 127.0 | 65 | 172 | 0.3167 | **B** |
| dungeon_crawl_seed123_500t | 401 | 127.0 | 65 | 172 | 0.3167 | **B** |

Key finding: **COMBAT raw_score is identical at 200t and 500t (127.0). Event count is identical (65). Last COMBAT event fires at tick 172 in both runs.** Zero new COMBAT events occur between tick 201 and 401. The A→B grade drop is entirely caused by the denominator growing from 200 to 401 with a frozen numerator.

### WORLD pillar

| Run key | tick_count (actual) | raw_score | event_count | last_event_tick | normalized_score | grade |
|---|---|---|---|---|---|---|
| dungeon_crawl_seed42_200t | 200 | 164.0 | 150 | ~200 (dense) | 0.8200 | **A** |
| dungeon_crawl_seed42_500t | 401 | 176.0 | 154 | 400 | 0.4389 | **B** |

WORLD is a partially different case: it gains 4 events (all `ecology_cycle_completed`, delta=+3.0 each, total +12.0) at tick 400. The raw_score grows from 164.0 to 176.0 (+7.3%) but the tick count grows from 200 to 401 (+100.5%). Even with activity continuing, the denominator outpaces the numerator — WORLD also drops A→B.

### Zero-new-COMBAT-event confirmation

From `data/calibration/dungeon_crawl_seed42_500t/quality_scores.jsonl`:
- COMBAT pillar lines in 500t run: 65 total
- COMBAT events with tick > 200: **0**
- COMBAT first event: tick 1; last event: tick 172

H2 is confirmed beyond doubt.

---

## Grade Threshold Analysis

From `config/simulation_quality/grade_thresholds.yaml`:

```yaml
S: 2.0
A: 0.5
B: 0.0
C: -0.5
D: -1.0
```

The `_assign_grade` function in `quality_report.py` uses `>` (strictly greater than), not `>=`. This means:

- **A requires normalized_score > 0.5**
- **B requires 0.0 < normalized_score <= 0.5**

The A/B boundary is the value **0.5** (exclusive from A, inclusive boundary from B).

### What raw_score is needed for A at each tick count?

| tick_count | min raw_score for A (> 0.5) | actual COMBAT raw | grade |
|---|---|---|---|
| 200 | > 100.0 | 127.0 | A |
| 401 | > 200.5 | 127.0 | B |
| 1000 | > 500.0 | 127.0 | B |
| 2000 | > 1000.0 | 127.0 | B |

COMBAT can never regain A in longer runs without ~58 additional full-cycle combat engagements per 100 ticks beyond tick 172 — which the dungeon_crawl archetype does not produce. This confirms the eval_matrix_results.md observation that COMBAT holds B across 500t, 1000t, and 2000t: it is not a regression, it is structural dilution.

---

## Design Decision: D2 — Artifact / Fix

**Recommendation: D2.** The grade decay is a calibration artifact that contradicts the stated contract purpose.

### Rationale

The contract (§4.4) asserts normalization "makes short and long runs comparable." The observed behavior is precisely the opposite: the same 127-point COMBAT performance earns A at 200t and B at 401t — solely because the denominator grows while the numerator is frozen. There is no new information in the extra 229 ticks that ought to downgrade COMBAT quality. The combat that occurred was identical in both runs.

**D1 ("sustained activity is the correct metric") is coherent only if the system is explicitly designed to penalize quiet ticks.** No such intent is stated anywhere in the contract or calibration docs. The calibration pass (TCK-20260630-SIMQ-RECALIBRATE) ran only 200-tick baseline runs — it was never designed or validated against longer runs. The grade_thresholds were calibrated against 200-tick data only; they do not represent a deliberate choice that "B is correct for 500t dungeon_crawl."

**D1 would require positive documentation of intent that currently does not exist.** Choosing D1 would mean retroactively declaring that the calibration anchors at 500t/1000t/2000t are correct — but those anchors were committed without any explanation of grade decay, and the eval_matrix_results.md explicitly notes the A→B transition without explaining it.

**D2 is the only reading consistent with the contract text.**

### Chosen Fix: Cap Divisor at `last_event_tick`

The simplest, least-destructive fix: change the divisor from `current_tick` to `max(1, last_event_tick)` where `last_event_tick` is the tick of the most recent scored event received by the accumulator. If no events were scored, fall back to `current_tick` (zero-event pillars retain existing behavior).

```python
# Before (quality_report.py line 101):
normalized_score = snap["raw_score"] / effective_tick

# After:
effective_denominator = snap["last_event_tick"] if snap["last_event_tick"] > 0 else effective_tick
normalized_score = snap["raw_score"] / effective_denominator
```

This means: **grade reflects quality of the active window, not dilution over silence**.

### Impact on WORLD (partial activity)

WORLD's last event is at tick 400 (the ecology cycle). With the fix:
- `normalized = 176.0 / 400 = 0.440` → still **B**

This is correct behavior: WORLD was genuinely active up to tick 400 (154 events spread across 0-400), and B at 0.440 reasonably represents its activity density. The fix closes the COMBAT gap (identical activity → identical grade) without inflating WORLD's grade beyond what its event density warrants.

### Impact on anchors (500t/1000t/2000t runs)

With D2, the dungeon_crawl 500t/1000t/2000t COMBAT grade changes from B to A (since last_event_tick = 172, same as 200t). WORLD likely stays B (last_event_tick = ~400, normalized ≈ 0.44).

All existing grade_anchors.json entries for dungeon_crawl 500t/1000t/2000t that show COMBAT=B must be updated to COMBAT=A. This is the expected, correct outcome — it resolves the contradiction between the 200t and 500t anchors.

---

## Implementation Plan

### Phase 1: Accumulator change (track `last_event_tick`)

In `src/simulation_quality/pillar_accumulator.py`:
1. Add `self.last_event_tick: int = 0` to `__init__`
2. In `add()`, update `self.last_event_tick = max(self.last_event_tick, record.tick)`
3. In `snapshot()`, include `"last_event_tick": self.last_event_tick`

### Phase 2: Report builder change (use `last_event_tick` as denominator)

In `src/simulation_quality/quality_report.py`, `QualityReportBuilder.build()`, line 101:
```python
last_event_tick = snap.get("last_event_tick", 0)
effective_denominator = last_event_tick if last_event_tick > 0 else effective_tick
normalized_score = snap["raw_score"] / effective_denominator
```

### Phase 3: Update contract doc

In `docs/simulation_quality/quality_scoring_contract.md` §4.4, update the formula box to:
```
normalized_score = raw_score / max(1, last_event_tick)
# last_event_tick = tick of the most recent scored event for this pillar
# Falls back to current_tick for pillars with no scored events
```
Add a rationale note citing this investigation.

### Phase 4: Re-run calibration for affected scenarios

Re-run `python3 tools/calibrate_simq.py` for:
- `dungeon_crawl` seed42/123/456 at 500t, 1000t, 2000t

Inspect `data/calibration/*/quality_report.json` for COMBAT and WORLD grade changes. Update `tests/simulation_quality/fixtures/grade_anchors.json` for all affected entries.

### Phase 5: Parity ledger

Add new entry to `docs/parity_ledger/combat_movement.yaml` (COMB-xxx, next available) documenting the normalized_score formula and the last_event_tick fix. Status: `verified` after test added.

Also check `docs/parity_ledger/world_dynamics.yaml` for any normalized_score entry — add if absent.

### Phase 6: eval_matrix_results.md

Update `docs/simulation_quality/eval_matrix_results.md` to:
- Explain the A→B decay pattern (before fix) with reference to this investigation
- Update grade tables after re-calibration to show corrected COMBAT grades at 500t+
- Note the change in normalization formula under the dungeon_crawl stability analysis section

### Phase 7: Run `make evaluate`

Confirm exit 0 (all PASS) after anchor updates.

---

## Parity Ledger Overlap

The `docs/parity_ledger/combat_movement.yaml` file contains 200+ entries (COMB-001 through COMB-200+), all focused on combat mechanics and movement legality. None relate to quality scoring normalization. A new entry is needed:

**Proposed new entry:**
```yaml
- id: COMB-NNN   # next available number
  text: >
    COMBAT pillar normalized_score uses last_event_tick as divisor, not total
    tick_count, so idle ticks after the final combat event do not dilute the grade.
  status: verified
  priority: P1
  v2_evidence: >
    src/simulation_quality/quality_report.py (QualityReportBuilder.build):
    effective_denominator = last_event_tick if last_event_tick > 0 else effective_tick
  test_path: tests/simulation_quality/test_grade_regression.py::test_combat_grade_stable_across_tick_counts
  divergence_note: >
    Introduced by TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY. Prior behavior divided by
    current_tick; same raw_score received different grades at 200t vs 500t.
    Intentional Gameplay Change: normalization reflects active-window quality only.
```

Also check `docs/parity_ledger/world_dynamics.yaml` for a normalized_score entry — likely absent, add analogously.

---

## Risks and Open Questions

### Risk R1: Scenarios where events DO fire throughout the run

For scenarios where combat/world events fire continuously across the full run (e.g., a 2000t urban_political run with steady faction conflict), `last_event_tick ≈ current_tick` and the behavior is identical to the current formula. No change, no risk.

### Risk R2: Zero-event pillar behavior

Pillars that never fire (AGENCY, COGNITION, etc. in dungeon_crawl with feature gates off) have `last_event_tick = 0`. The fallback to `current_tick` is correct — `raw_score = 0.0 / current_tick = 0.0` regardless, grade stays C. No change in behavior.

### Risk R3: Anchor churn

The 500t/1000t/2000t dungeon_crawl COMBAT anchors will flip from B to A. This is intentional. Any CI that checks against the old anchors will need updating. The ticket scope explicitly includes this.

### Risk R4: Loop detection interaction

`PillarAccumulator.last_event_tick` is only needed for report building; it does not affect loop detection (which uses the window buffer). No interaction.

### Open Question AQ2 (from ticket)

"Would capping the divisor break existing anchors for scenarios where events DO continue throughout the run?" Answer: No. When events continue to fire throughout, `last_event_tick ≈ current_tick`, so the formula is materially unchanged.

---

## Anti-Drift Hazards

1. **Calibration re-run is required before anchors are committed.** Do not update grade_anchors.json manually — re-run calibrate_simq.py and read actual output.

2. **The 500t run key is misleading:** `dungeon_crawl_seed42_500t` actually ran to tick 401. The tick_count in `quality_report.json` is authoritative; the key name is nominal. Any future calibration using `--ticks 500` should verify actual tick_count in the report.

3. **Do not use `current_tick` as the effective denominator for pillars with events.** The fallback-to-current_tick path is only valid for zero-event pillars. If this is refactored, ensure the condition `last_event_tick > 0` is preserved.

4. **The `_assign_grade` boundary is `>` (strictly greater than), not `>=`.** A score of exactly 0.5 receives grade B, not A. Any test that sets `normalized_score = 0.5` and expects A will fail.

5. **WORLD pillar may still show B after the fix** (last_event_tick=400, normalized=0.440 < 0.5). This is correct and should not be further adjusted by raising the threshold — the correct fix for a low WORLD grade is more world activity, not threshold manipulation.
