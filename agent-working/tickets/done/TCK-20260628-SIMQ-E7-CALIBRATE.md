---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E7-CALIBRATE
phase: done
date: 2026-06-28
tags: [simulation-quality, scoring, calibration, thresholds]
---

# TCK-20260628-SIMQ-E7-CALIBRATE

## Title
Simulation Quality Scoring — Calibration & Grade Threshold Tuning

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Run baseline quality scoring on canonical worlds and scenarios, observe the normalized
scores produced by the complete module, and tune the grade threshold constants to
produce meaningful signal — grades should reflect real simulation health, not be
uniformly A or uniformly F due to miscalibrated scoring deltas or thresholds.

## Scope
- Run `sandbox_world`, `urban_political`, `dungeon_crawl`, `wilderness_survival` at
  seeds 42 and 137, 500 ticks each, with `QUALITY_SCORING_DISABLED=0`
- Record `quality_report.json` from each run
- Analyze per-pillar normalized scores and compare against expected health for each world
- Edit `config/simulation_quality/grade_thresholds.yaml` so that:
  - Known-broken systems (e.g., Economy in pre-fix urban_political) grade F
  - Known-healthy systems (e.g., Combat in dungeon_crawl) grade B or better
  - Grade spread across pillars is meaningful (not all A, not all F)
- Edit `config/simulation_quality/scoring_weights.yaml` if any pillar's raw_score is
  dominated by a single high-weight rule that drowns out other signals — rebalance the
  delta for that rule key only; **no Python code changes required**
- Re-run all 8 scenarios to verify updated config produces correct differentiation
- Commit calibrated `scoring_weights.yaml` and `grade_thresholds.yaml`
- Commit `grade_anchors.json` for E6 regression tests
- Update `quality_scoring_contract.md` §4.5 with calibrated threshold values
- Update `docs/parity_ledger/infrastructure.yaml` with a new entry for the quality
  module (SIMQ-CALIBRATED-001) at status `verified` once thresholds are locked

## Out of Scope
- Fixing simulation bugs discovered during calibration (file separate tickets)
- Tuning world configs to produce better quality scores (not this module's job)
- Historical cross-run comparison (post-MVP)

## Acceptance Criteria
- [ ] Baseline runs completed on all 4 canonical worlds × 2 seeds × 500 ticks = 8 runs
- [ ] `quality_report.json` retained from each run and analyzed (do not clean data/runs/ during this ticket)
- [ ] `GRADE_THRESHOLDS` in `pillars.py` updated from estimates to calibrated values
- [ ] Grade spread across pillars is non-degenerate: at least 3 distinct grades (A/B/C/D/F) observable across the 8 runs
- [ ] `grade_anchors.json` committed with grades from canonical runs
- [ ] `quality_scoring_contract.md` §4.5 updated with final threshold values
- [ ] `docs/parity_ledger/infrastructure.yaml` has SIMQ-CALIBRATED-001 entry at `verified`
- [ ] Any scoring delta that is identified as dominating (>50% of raw_score in a pillar) is reviewed and possibly rebalanced
- [ ] Implementation notes document the calibration methodology for future re-calibration

## Related Tickets
- Parent: TCK-20260628-SIMQ-EPIC
- Requires: TCK-20260628-SIMQ-E6-TESTS (full test suite must pass before calibration)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §4.5 (Grade Thresholds — update here)
- `docs/audits/D04_balance_tuning.md` — existing balance observations for cross-reference
- `docs/audits/D06_longrun_health.md` — long-run baseline data for expected pillar behavior
- `docs/parity_ledger/infrastructure.yaml` — add calibration parity entry

## Implementation Notes
Calibration methodology:
1. Run all 8 baseline scenarios and collect `quality_report.json`
2. For each pillar, compute the percentile distribution of normalized_score across all 8 runs
3. Edit `grade_thresholds.yaml` — set thresholds at natural breaks in the distribution,
   not at round numbers
4. Re-run all 8 scenarios to verify updated config produces meaningful differentiation
5. If any single scoring rule contributes >50% of a pillar's raw_score in a typical run,
   reduce its delta value in `scoring_weights.yaml` — no Python code change needed
6. Document the final values in `quality_scoring_contract.md` §4.5

Do not clean `data/runs/` during this ticket. After calibration is complete and anchors
are committed, run `rm -rf data/runs/*` as the final step per the After Work workflow.

## Implementation Notes
Calibration runner (`tools/calibrate_simq.py`) implemented and verified: runs engine for N ticks, waits for JSONL flush, replays `simulation_events.jsonl` through QualityHub, writes `quality_report.json` to `data/calibration/{name}_seed{seed}_{ticks}t/`.

**Calibration-blocking gap found:** The engine emits event types `quest_event`, `StrategicConcernRaised`, `InvariantViolation`, `StrategicProjectChanged`, `StrategicObjectiveChanged` — none of which are registered in any scorer's `EVENT_TYPES`. The contract §5 event type vocabulary (`action_executed`, `combat_initiated`, `resource_harvested`, etc.) is not yet emitted by the kernel's `EventRecorder`. Zero events scored in 100-tick baseline run.

**Root cause:** The engine's observability layer emits internal diagnostic events, not the normalized domain event types defined in the scoring contract. Event type alignment is a prerequisite for threshold calibration. Filed as gap in parity ledger SIMQ-CALIBRATED-001 (status: missing).

**Grade thresholds:** Remain at initial contract estimates (S=2.0, A=0.5, B=0.0, C=-0.5, D=-1.0). Cannot calibrate until event type alignment is complete.

**data/runs/** NOT cleaned per ticket rule: "do not clean data/runs/ during this ticket." Cleaning deferred until calibration completes in a follow-up ticket.

## Test Summary
No regression tests updated (grade_anchors.json remains UNKNOWN). Calibration script verified working end-to-end for engine execution and JSONL replay; scoring yields zero due to event type mismatch.

## Files Changed
- `tools/calibrate_simq.py` (new — calibration runner)
- `docs/parity_ledger/infrastructure.yaml` (SIMQ-CALIBRATED-001 at status=missing)
- `data/calibration/sandbox_world_seed42_100t/quality_report.json` (calibration artifact)

## Completion Summary
Calibration infrastructure complete. Actual threshold tuning blocked by event type mismatch between engine JSONL output and scorer contract vocabulary. SIMQ-CALIBRATED-001 parity entry documents gap as P1 missing.
