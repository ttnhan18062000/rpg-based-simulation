# Implementation Sequence — perf-closeout-benchmark-identity

Owner-approved 2026-10-03. The RPG-core entry gate and the `src/` freeze both stay in force: no
ticket in this batch edits `src/` or produces a performance measurement.

## Order

1. TCK-20261003-PERF-M0-EPIC-CLOSURE  (no deps in this batch)
2. TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING  (no deps in this batch)
3. TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA  (no deps in this batch)
4. TCK-20261003-IMPLEMENT-TICKET-PERF-REMINDER-CITATION  (follows 2; added by perf-planner at review of 2)

## Why This Order Matters

1 and 2 are small, independent hotfixes and clear the backlog first. 3 is a standard-tier design
draft and may cite the closed M0 epic. One PR for the whole batch, including the planning commit.
