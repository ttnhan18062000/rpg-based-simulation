---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
date: 2026-10-10
tags: [performance, observability, testing]
---

# Plan: TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE

Read `cost_accounting_version` from the raw baseline JSON in `BaselineComparator` (BaselineConfig is outside the lift). Absent or different from `COST_ACCOUNTING_VERSION` makes the tick-cost verdict INCONCLUSIVE with a named reason; FAIL/WARNING stay. Carry the reason on the comparison results, the CI gate result and sweep_report.json. Gate stays non-blocking (exit 0). Extract status helpers so the code-health ratchet holds.
