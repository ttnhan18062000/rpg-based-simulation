---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-M2-CLAUSE-INVENTORY
date: 2026-10-03
tags: [performance, documentation]
---

# Plan: TCK-20261003-PERF-M2-CLAUSE-INVENTORY

## Summary
Write `docs/performance/performance_clause_inventory.md` (clause matrix, reverse table, disagreement list,
PERF-D4 mapping, call-site table) and a read-only `ast` helper `tools/perf/perf_threshold_inventory.py`
for the `assert_perf_threshold` / `perf_check` table. Documents, code and CI are only read.

## Steps
1. Read the seven documents with line numbers; read gate code, harnesses, certification code, test helper, CI.
2. Add the helper (deterministic JSON/markdown, no timestamps) with `tests/tools/test_perf_threshold_inventory.py`
   and one line in `_TOOLS_PERF_BASENAME_MAP` (`tools/gate_checks/test_scope_coverage_static.py`).
3. Write the inventory; embed the helper's markdown table verbatim.
4. Verify cited paths and test files exist; record misses as findings, never fix them here.
5. perf-planner reviews before close.

## Scope guards
No edit to any listed document, threshold, `hard` flag, baseline, CI job or `src/`. Nothing is measured.
