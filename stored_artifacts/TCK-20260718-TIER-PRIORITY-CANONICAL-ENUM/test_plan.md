---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
date: 2026-07-18
tags: [frontmatter, data-quality]
---

# Test Plan — TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM

## Regression Surface (existing tests that must pass)

- `tests/tools/test_validate_frontmatter.py` — must remain fully green;
  `LAYER_VALUES` behavior is unchanged, only its import path may gain a
  re-export consumer, not a behavior change.
- `tests/tools/test_status_drift_check.py` — must remain fully green;
  `EPIC_TIER_VALUES` stays as-is (see investigation.md's risk note).
- `tests/tools/test_done_checker_static.py` — existing
  `test_run_static_precheck_all_pass_eligible` /
  `test_run_static_precheck_surfaces_fail_not_masked` must still pass with
  the new 6th condition added — a valid ticket's `## Tier`/`## Priority`
  must not spuriously fail the new check.
- `tests/tools/test_agent_ops_dashboard_ingest.py` — must remain fully
  green after `WORKFLOW_STATUS_VALUES`'s import source changes.

## New Tests Required (per AC)

1. `tools/ticket_field_values.py` module-level test: `TIER_VALUES ==
   {"hotfix", "standard", "epic"}`, `PRIORITY_VALUES == {"P0", "P1", "P2",
   "P3"}`, `WORKFLOW_STATUS_VALUES` unchanged from its current 5-value set,
   `LAYER_VALUES is validate_frontmatter.LAYER_VALUES` (same object, not a
   copy — proves no duplication).
2. New body-section check function: fixture ticket with `## Priority\nP1:
   High` — assert FAIL/non-canonical result, with evidence text naming the
   offending value.
3. Same function: fixture ticket with `## Tier\nstandard\n\n##
   Priority\nP1` — assert PASS.
4. `run_static_precheck` integration test: a ticket fixture with a bad
   `## Priority` produces a checklist entry with `status: "FAIL"` for the
   new condition name, and the overall `DONE_SCHEMA` verdict this would feed
   into (via `classify_checklist_failure`) is not silently masked by the
   other 5 conditions passing.
5. **Genuine-catch proof** (mirrors `TCK-20260718-FILTER-SELECT-DROPOUT`'s
   verification discipline): after writing test 2, temporarily revert only
   the new check-function file (via `git stash` on that one file, or by
   testing against a stub that always returns PASS) and confirm test 2
   fails with the expected assertion error — proving the test would have
   caught the bug pre-fix, not just that it passes post-fix by coincidence.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_ticket_field_values.py tests/tools/test_done_checker_static.py tests/tools/test_validate_frontmatter.py tests/tools/test_status_drift_check.py tests/tools/test_agent_ops_dashboard_ingest.py -q
```

## Anti-Drift Test Guards

- A test asserting `LAYER_VALUES` is imported, not redefined, in the new
  module (e.g. `tools.ticket_field_values.LAYER_VALUES is
  tools.validate_frontmatter.LAYER_VALUES`) — prevents a future edit from
  silently forking the two.
- A test confirming the new check function's extraction calls
  `parse_body_section` (source-text guard, mirroring
  `GanttBar.test.tsx`/`TicketsView.test.tsx`'s own anti-drift source-scan
  pattern from earlier today) rather than a bespoke regex.
