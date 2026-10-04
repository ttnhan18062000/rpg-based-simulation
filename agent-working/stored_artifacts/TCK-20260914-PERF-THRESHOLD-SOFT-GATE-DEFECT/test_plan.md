---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT
date: 2026-10-04
tags: [performance, testing]
---

# Test plan: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT

Docs-only change, so no new tests.
- `tests/tools/test_perf_inventories_committed_in_sync.py`: the committed inventories still match the tool.
- `python3 tools/validate_frontmatter.py` on the ticket and the three artifacts.
- `make docs-registry` then `done_checker_static.py`.

## Proof Plan

| Criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| AC1 disposition (superseded) | docs | regenerated inventory plus cited gate rule | `tools/perf/perf_threshold_inventory.py`, roadmap gate item 2 | 55 call sites, 0 literal `hard=True` | `python3 tools/perf/perf_threshold_inventory.py --format json` |
| Inventory stays in sync | unit | committed-vs-generated comparison | `tests/tools/test_perf_inventories_committed_in_sync.py` | 4 passed | `uv run pytest tests/tools/test_perf_inventories_committed_in_sync.py` |
| AC3 gap row updated | docs | frontmatter and registry validity | `tools/validate_frontmatter.py`, `make docs-registry` | no violations | `python3 tools/validate_frontmatter.py --content-type ticket <ticket>` |
