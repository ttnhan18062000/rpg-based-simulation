---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY
phase: open
date: 2026-07-02
tags: [simulation_quality, combat, world, grade_thresholds, normalization, scoring]
---

# TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY

## Title
Document or fix COMBAT/WORLD grade decay caused by tick-count normalization in longer runs

## Status
OPEN

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
- Data proof that supports D2 as the "correct" fix: the quality scoring contract literally states the purpose of normalization is comparability across run lengths. A->B decay for identical events at 200 vs 500 ticks violates that stated purpose.
- If D1 is chosen instead, the grade_anchors.json entries for 500t, 1000t, 2000t dungeon_crawl (where COMBAT and WORLD are already anchored at B) would be confirmed correct.
- WORLD raw grows 164→176 (+12 in 300 ticks), but the grade still drops A→B because the denominator grows 200→500. Even with event growth, the normalization dilutes faster than events accumulate in dungeon_crawl.

## Test Summary
- Read `data/calibration/dungeon_crawl_seed42_{200,500}t/quality_scores.jsonl`, confirm event_type distribution and confirm no new negative COMBAT events in 200–500t window
- If D2: add regression test asserting that normalized_score for same raw_score at different tick counts remains within ±10% when no new events fire (tests the fix)
- Run `make evaluate --dry-run` after any anchor changes; must exit 0

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on completion)
