---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION
phase: done
date: 2026-10-14
tags: [testing, regression, simulation-quality]
---

# Plan

1. `tools/test_architecture/simq_pillar_compare.py`: typed parse (ok / no-data / contract error), four-way `compare_pillar`, `no_data_sets_equal`, `compare_report`, label helpers. One module for the tests, the guards, `simq_reanchor` and `evaluate_simq` (testing-planner, 2026-10-14).
2. `test_grade_regression.py`: every default removed; `_pillar_failures` / `_assert_pillars` call the helper; schema guard uses `parse_anchor`.
3. `test_corpus_diversity.py`: `_anchor` strict, `_snap_failure` / `_score_applies` at the 14 guard sites.
4. `simq_reanchor.py`: no-data anchor shape, status columns, status transitions as moved rows, ruling table.
5. `evaluate_simq.py`: minimum change (read through the helper, print `no-data`).
6. Docs: quality_scoring_contract.md 11.3 and the re-anchor how-to.

Scope guard: no tolerance, band or override changes (AC8); no scorer change; no re-anchor of the held rows.
