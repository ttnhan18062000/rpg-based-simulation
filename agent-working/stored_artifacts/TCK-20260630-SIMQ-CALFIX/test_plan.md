---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-CALFIX
artifact_type: test_plan
tags: [simq, calibration, test-plan]
---

# Test Plan: TCK-20260630-SIMQ-CALFIX

## Existing Tests to Run (Scoped)

Run: `pytest tests/simulation_quality/ -v --timeout=120 -m "not slow"`

Key tests that exercise the changed module dependencies:
- `test_kernel_simq_integration.py` — kernel wiring, verify no regressions from state changes
- `test_quality_hub_integration.py` — hub event processing
- `test_grade_regression.py` — regression anchors (may need updates if calibration data changes)
- `test_weights.py` — profile loading (validates `ScoringWeights.load(profile=...)` path)

## New Verification (Calibration Runs)

Run calibration for at least two worlds after implementation:
```bash
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 200
python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks 200
```

### Acceptance Checks

| Check | How to verify |
|---|---|
| No `LAW-OCCUPANCY-COLLISION` | Grep run logs / no error output from calibration run |
| Non-identical pillar scores | Compare `quality_report.json` from dungeon_crawl vs urban_political |
| WORLD or ECONOMY events > 0 | Check `event_count` fields in quality_report.json |
| Profile loaded correctly | `dungeon_crawl` uses COMBAT weight 2.0 per `dungeon_crawl.yaml` |

## Goblin Spawn Position Fix

Generic fallback: `(20.0 + (i % 5) * 8, 20.0 + (i // 5) * 8)` for i in 0..8
produces positions: (20,20), (28,20), (36,20), (44,20), (52,20), (20,28), (28,28)...
All at least 12 tiles from hero at (64,64). No collision possible.

## Regression Concern

`test_grade_regression.py` anchors may have been built on generic sim runs. If those
anchors are stale, they may need updating after world-specific runs. Monitor for
unexpected failures in that test and update anchors if necessary.
