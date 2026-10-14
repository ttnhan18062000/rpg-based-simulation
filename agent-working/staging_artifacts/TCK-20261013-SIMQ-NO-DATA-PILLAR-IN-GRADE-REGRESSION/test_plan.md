---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION
phase: open
date: 2026-10-14
tags: [testing, regression, simulation-quality]
---

# Test plan

- Helper unit tests: AC1 (missing pillar), AC2 (four cells, min_events change, both malformed shapes), AC3 (overall sets and overall no-data), AC5 (anchor shapes), AC6 (status-less reports).
- Regression-test unit tests on synthetic reports (run without data/calibration).
- Corpus-diversity: `_anchor` reader and `_snap_failure` on synthetic snapshots; one real guard re-run.
- Re-anchor tool: no-data rows written, status changes moved, identity check, refusals, ruling table; plus the byte-identity run over the #531 stored rows.
- AC8: `SCORE_TOLERANCE_OVERRIDES == {}` test untouched and passing.
