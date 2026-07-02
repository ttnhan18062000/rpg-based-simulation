---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY
phase: done
date: 2026-07-02
tags: [simulation_quality, combat, world, grade_thresholds, normalization, scoring]
---

# TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY

## Title
Document or fix COMBAT/WORLD grade decay caused by tick-count normalization in longer runs

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
COMBAT and WORLD pillar grades decay A→B between 200t and 500t dungeon_crawl runs — consistently across all 3 seeds (42, 123, 456). Investigation from `make evaluate` reveals:

```
dungeon_crawl_seed42_200t  COMBAT: raw=127.0  tick=200  normalized=0.6350  grade=A
dungeon_crawl_seed42_500t  COMBAT: raw=127.0  tick=500  normalized=0.2540  grade=B
dungeon_crawl_seed42_200t  WORLD:  raw=164.0  tick=200  normalized=0.8200  grade=A
dungeon_crawl_seed42_500t  WORLD:  raw=176.0  tick=500  normalized=0.3520  grade=B
```

The raw COMBAT score is **identical** at 200t and 500t (127.0). WORLD gains only 12 raw points in 300 additional ticks. The grade drops because `normalized_score = raw_score / max(1, tick_count)` dilutes the same events as the run grows longer.

This is **not H1** (accumulated negative events) — no new negative COMBAT events fire between 200–500t. It is **H2**: the normalization formula treats longer quiet runs as lower-quality runs, even if the activity that occurred was identical.

This raises a design question: is grade decay over idle ticks **intended** (the metric rewards sustained per-tick activity) or **a calibration artifact** (the same quality of simulation should score the same regardless of how long you watch it)? The current behavior makes the same dungeon_crawl scenario score differently depending solely on tick count, which undermines the stated purpose of normalized_score: "Makes short and long runs comparable."

## Scope
1. Read `config/simulation_quality/grade_thresholds.yaml` to identify the exact A/B boundary (observed to lie between normalized 0.254 and 0.635).
2. Compare COMBAT event distribution at dungeon_crawl_seed42_200t vs 500t using quality_scores.jsonl — confirm no new negative events in 200–500t window.
3. Make an explicit design decision (with rationale), one of:
   - **D1 — Intended**: Sustained activity per tick is the correct metric. Grade decay is expected. Document this explicitly in `docs/simulation_quality/quality_scoring_contract.md` §4.4 and `docs/simulation_quality/eval_matrix_results.md`. No formula change.
   - **D2 — Artifact**: Fix the normalization so that grades reflect quality of active periods rather than dilution over idle ticks. Options include: capping the tick divisor at last-event-tick, using event-density over active windows, or computing normalized_score per event rather than per tick.
4. Update `docs/simulation_quality/eval_matrix_results.md` with the confirmed explanation for the A→B decay pattern.
5. If D1: verify grade_anchors.json already reflects correct (lower) grades for 500t and 1000t runs — update any anchors that don't.
6. If D2: implement formula change, re-run calibration for affected scenarios, update anchors.

## Out of Scope
- Changing COMBAT or WORLD scoring weights
- Addressing why raw COMBAT score doesn't grow beyond 200t (a dungeon archetype question, related to TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG)
- FACTION/SOCIAL/INFORMATION zero-activation (separate ticket)

## Acceptance Criteria
- [ ] `config/simulation_quality/grade_thresholds.yaml` read and exact A/B boundary documented in investigation.md
- [ ] quality_scores.jsonl diff (200t vs 500t) confirms zero new negative COMBAT events in 200–500t window
- [ ] Design decision (D1 or D2) documented with rationale
- [ ] If D1: `docs/simulation_quality/quality_scoring_contract.md` §4.4 updated with explicit statement about tick-dilution behavior; `docs/simulation_quality/eval_matrix_results.md` updated with grade decay explanation
- [ ] If D2: formula changed, calibration re-run for dungeon_crawl multi-tick anchors, grade_anchors.json updated, parity ledger entry for combat_movement.yaml updated
- [ ] `make evaluate --dry-run` exits 0 (no regressions) after any anchor updates

## Related Tickets
- TCK-20260630-SIMQ-TIMEGATE — added time-gate penalties; established `normalized_score = raw_score / max(1, tick_count)` as canonical formula
- TCK-20260702-SIMQ-EVAL-MATRIX — produced the multi-tick calibration corpus that surfaced this pattern
- TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG — sibling: investigates why dungeon_crawl has no economy/cognition activity

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §4.4 — normalized score formula definition
- `docs/simulation_quality/eval_matrix_results.md` — grade distribution matrix (currently shows A→B decay without explanation)
- `docs/parity_ledger/combat_movement.yaml` — COMBAT parity entries
- `docs/parity_ledger/world_dynamics.yaml` — WORLD parity entries

## Related Stored Artifacts
- (none yet)

## Related Code Areas
- `src/simulation_quality/accumulator.py` — PillarAccumulator, normalized_score computation
- `src/simulation_quality/scorers/combat.py` — CombatScorer
- `src/simulation_quality/scorers/world_dynamics.py` — WorldDynamicsScorer
- `config/simulation_quality/grade_thresholds.yaml` — A/B boundary values
- `data/calibration/dungeon_crawl_seed42_200t/quality_scores.jsonl`
- `data/calibration/dungeon_crawl_seed42_500t/quality_scores.jsonl`

## Assumptions / Open Questions
- **AQ1**: Is the intent of normalized_score "sustained quality per tick" (D1) or "quality regardless of run length" (D2)? The contract says "makes short and long runs comparable" — but the observed behavior does the opposite for same-scenario runs.
- **AQ2**: If D2 is chosen, the simplest fix is to divide by the tick of the last scored event rather than total tick count. Would this break any existing calibration anchors for scenarios where events DO continue throughout the run?
- **AQ3**: The parity ledger `combat_movement.yaml` may need a new entry for this behavior if D1 is the decision.

## Implementation Notes
Decision D2 (Fix) was confirmed by plan.md and implemented as follows:

**Formula change (quality_report.py):** Replaced `raw_score / effective_tick` with:
```python
last_event_tick = snap.get("last_event_tick", 0)
floor_tick = max(1, effective_tick // 4)
effective_denominator = max(floor_tick, last_event_tick) if last_event_tick > 0 else effective_tick
normalized_score = snap["raw_score"] / effective_denominator
```
The floor (`current_tick // 4`) prevents S-grade inflation for initialization-burst pillars
(AGENCY fires all events at tick 1; without floor: 40/1=40.0 >> S threshold).

**PillarAccumulator change:** Added `last_event_tick: int = 0` field, updated in `add()` as
`self.last_event_tick = max(self.last_event_tick, record.tick)` inside the duplicate-event guard.
Exposed via `snapshot()`.

**Calibration result:** All 25 anchored scenarios re-calibrated. 24 pillar grades changed.
Key changes: COMBAT+PROGRESSION hold A at 500t and 1000t in dungeon_crawl (was B). SOCIAL=S
in urban_political (ENABLE_SOCIAL_COOPERATION=ON with high event density). AGENCY=A for
simq_routing_test seeds 123/456 (higher event counts than seed42).

**simq_routing_test note:** Engine crashes with STONE registry bug (pre-existing, unrelated);
calibration data regenerated by replaying existing quality_scores.jsonl through updated formula.

**Parity ledger:** INFRA-255 (primary, infrastructure.yaml), COMB-293 (secondary,
combat_movement.yaml), WORLD-110 (secondary, world_dynamics.yaml).

## Test Summary
- 12 new unit tests: T-ACC-01 through T-ACC-05 in test_accumulator.py, T-REP-01 through T-REP-07
  in test_report.py.
- 387 tests pass in tests/simulation_quality/ (not slow).
- evaluate_simq --dry-run: 250 pillars checked, 0 regressions.
- Updated existing test_normalized_score_formula to reflect new floor-based denominator.

## Files Changed
- src/simulation_quality/pillar_accumulator.py (last_event_tick field + snapshot)
- src/simulation_quality/quality_report.py (corrected normalization formula)
- tests/simulation_quality/test_accumulator.py (T-ACC-01 through T-ACC-05)
- tests/simulation_quality/test_report.py (T-REP-01 through T-REP-07 + updated formula test)
- tests/simulation_quality/fixtures/grade_anchors.json (24 grade changes across 25 scenarios)
- data/calibration/*/quality_report.json (all 25 scenarios re-calibrated)
- docs/simulation_quality/quality_scoring_contract.md (§4.3 last_event_tick, §4.4 corrected formula + rationale)
- docs/simulation_quality/eval_matrix_results.md (D2 fix header note + updated grade tables)
- docs/parity_ledger/infrastructure.yaml (INFRA-255 primary entry)
- docs/parity_ledger/combat_movement.yaml (COMB-293 secondary reference)
- docs/parity_ledger/world_dynamics.yaml (WORLD-110 secondary reference)

## Completion Summary
D2 fix implemented: normalized_score now uses max(floor_tick, last_event_tick) as divisor,
where floor_tick = current_tick // 4. COMBAT/PROGRESSION hold A at 500t and 1000t in
dungeon_crawl (was B — tick-dilution artifact resolved). Floor prevents S-grade inflation
from initialization-burst pillars. All 25 calibration anchors updated from actual output.
387 tests pass, 0 regressions.
