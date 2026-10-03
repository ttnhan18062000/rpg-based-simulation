---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT
date: 2026-10-03
tags: [performance, architecture, engine]
---

# Plan: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT

## Summary
Add `tools/perf/phase_inventory.py` (stdlib `ast`, no engine import) plus tests, and commit one
generated report (`docs/performance/phase_inventory.{json,md}`). Evidence only (PA-05A).

## Steps
1. Read the pipeline's `refine()`, `run_phase` helper and the four documented sources.
2. Write the script: run_phase calls, direct `update` assignments, direct class-method calls,
   four documented sources compared by named phase, dependency-graph and domain-permission names.
3. Tests in `tests/tools/test_phase_inventory.py`; synthetic pipeline source; no fixed real count.
4. Add `phase_inventory.py` to the test-scope map (`tools/gate_checks/test_scope_coverage_static.py`).
5. Generate the report, send it to perf-planner for review, close.

## Scope guards
No `src/` edit; no edit to authoritative_pipeline.md, AGENTS.md, CLAUDE.md, the generator note or any P1 doc.
Does not decide which count is right (PERF-D6). `--check` is not wired into CI.

## Acceptance-criteria map
AC1 -> determinism test and cmp; AC2 -> report sections 1.1-1.3; AC3 -> section 2; AC4 -> section 3;
AC5 -> `--check` tests; AC6 -> committed report; AC7 -> test run; AC8 -> diff scope check.
