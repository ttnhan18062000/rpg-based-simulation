---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-TICKET-CORPUS-REPORT
artifact_type: test_plan
tags: []
---

# Test Plan — TCK-20260718-TICKET-CORPUS-REPORT

## Regression Surface (existing tests that must pass)

- `tests/tools/test_tag_report.py` (if it exists) — unaffected, this ticket doesn't touch
  `tag_report.py`.
- `tests/tools/test_agent_ops_dashboard_*.py` — unaffected except the new endpoint's own tests.

## New Tests Required (per AC)

1. `tests/tools/test_ticket_stats_report.py` — dedicated test file mirroring
   `tag_report.py`'s own test conventions (fixture tickets in `tmp_path`, real
   `collect_completed_tickets`-style walk): velocity computation correctness against a small
   `working_log.csv` fixture, tier/type/priority/layer distribution correctness against fixture
   tickets, artifact-completeness detection (present vs. missing `stored_artifacts/` files,
   hotfix-exemption).
2. New route test(s) for `/api/stats/tickets` mirroring the sibling
   `test_agent_ops_dashboard_stats.py`'s pattern: happy path, empty-corpus edge case.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_ticket_stats_report.py tests/tools/test_agent_ops_dashboard_stats.py -q
```

## Anti-Drift Test Guards

- Assert the new tool imports `TIER_VALUES`/`PRIORITY_VALUES`/`layer_values()` rather than
  redefining them (source-text guard).
- Assert the new tool's computation function is pure (no writes) except when explicitly asked
  via `--json`, mirroring `tag_report.py`'s own contract.
