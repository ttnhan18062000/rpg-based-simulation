---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260718-STATUS-FACET-CANONICAL
phase: open
date: 2026-07-18
tags: []
---

# Test Plan — TCK-20260718-STATUS-FACET-CANONICAL

## Regression Surface (existing tests that must pass)

- `tests/tools/test_agent_ops_dashboard_ingest.py` — full file, including
  the three pre-existing AND/OR filter tests and the pagination tests
  added by `TCK-20260717-TICKETS-TABLE-PAGINATION`.
- `tests/tools/test_agent_ops_dashboard_api.py`,
  `test_agent_ops_dashboard_api_boundary.py`,
  `test_agent_ops_dashboard_concurrency.py`,
  `test_agent_ops_dashboard_frontend_api_surface.py`,
  `test_agent_ops_dashboard_serve.py` — full dashboard backend surface.
- `tests/tools/test_status_drift_check.py` — full file, including all
  tests unrelated to `EPIC_TIER_VALUES`.
- `dashboard-frontend`'s full vitest suite — regression guard only, no
  frontend file expected to change.

## New Tests Required (per AC)

- `test_statuses_facet_is_canonical_full_set_regardless_of_corpus_content` —
  a fixture with only `OPEN`/`DONE` tickets, zero `INPROGRESS`/`BLOCKED`/
  `EPIC_SCOPED` anywhere; asserts `facets["statuses"]` still lists all 5.
- `test_statuses_facet_unaffected_by_status_query_param` — filtering by
  `status=DONE` (narrowing `items` to one ticket) must not narrow
  `facets["statuses"]`.
- `test_bare_scoped_no_longer_exempt_after_tightening` — a ticket with
  body `## Status` = bare `SCOPED` (no parenthetical) must now be flagged
  `FAIL` by `check_ticket_status_drift`, not silently exempted.

## Updated Tests

- `test_facets_source_reflects_full_filtered_corpus_not_just_current_page` —
  `statuses` assertion updated from the 4-value fixture-derived list to the
  5-value canonical list (`BLOCKED`, `DONE`, `EPIC_SCOPED`, `INPROGRESS`,
  `OPEN`).
- `test_epic_tier_exception_ignored_by_value` — narrowed to assert only
  `EPIC_SCOPED`'s exemption (the bare-`SCOPED` half moved to the new test
  above, now asserting the opposite outcome).

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py \
  tests/tools/test_agent_ops_dashboard_api.py \
  tests/tools/test_agent_ops_dashboard_api_boundary.py \
  tests/tools/test_agent_ops_dashboard_concurrency.py \
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py \
  tests/tools/test_agent_ops_dashboard_serve.py \
  tests/tools/test_status_drift_check.py -q
```

```
cd dashboard-frontend && npm run test -- --run
```

## Anti-Drift Test Guards

- The new `test_statuses_facet_is_canonical_full_set_regardless_of_corpus_content`
  test is itself the anti-drift guard for the core behavior: if a future
  change reverts `facets["statuses"]` back to corpus-derived, this test
  fails immediately because its fixture deliberately contains zero
  `BLOCKED`/`INPROGRESS`/`EPIC_SCOPED` tickets.
- `test_bare_scoped_no_longer_exempt_after_tightening` guards against
  `EPIC_TIER_VALUES` silently drifting back to the looser two-value set.
