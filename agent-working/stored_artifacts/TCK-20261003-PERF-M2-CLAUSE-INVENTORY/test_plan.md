---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-M2-CLAUSE-INVENTORY
date: 2026-10-03
tags: [performance, documentation]
---

# Test Plan: TCK-20261003-PERF-M2-CLAUSE-INVENTORY

## Helper
`tests/tools/test_perf_threshold_inventory.py`: synthetic sources for every `hard` form (absent, literal True/False,
pass-through expression), `op`, limit text, markers from function / class / module, totals, helper-module and
unparsable-file skip, pipe escaping, and a real-tree determinism check plus CLI byte-identity (two runs).

## Completeness of the inventory (how it was checked)
For each of the seven documents: every number with a unit and every must / MUST / shall / required / forbidden /
prohibited is a row in §3 or named non-normative in §2. Re-run with `grep -nE 'must|MUST|shall|required|forbidden|prohibited|[0-9] ?(ms|%|GB|MB)'`
per document and compare with the row line ranges.

## Scoped runs
`pytest tests/tools/test_perf_threshold_inventory.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_hash_callsite_inventory.py`;
`python3 tools/validate_frontmatter.py` on the new document and artifacts.

## Proof Plan

- Level: unit (helper) plus document evidence.
- Proof kind: synthetic-source tests and a determinism check.
- Oracle source: hand-written synthetic sources with known `hard`, `op`, limit and marker values; two-run byte equality on the real tree.
- Expected effect: the helper reports each call form correctly and is reproducible; the document is validated by frontmatter and by the completeness check above.
- Selected commands: `pytest tests/tools/test_perf_threshold_inventory.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_hash_callsite_inventory.py -p no:cacheprovider`.
