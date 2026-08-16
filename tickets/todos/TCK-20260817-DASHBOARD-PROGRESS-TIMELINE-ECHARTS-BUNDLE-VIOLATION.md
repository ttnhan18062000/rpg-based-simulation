---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-DASHBOARD-PROGRESS-TIMELINE-ECHARTS-BUNDLE-VIOLATION
phase: open
date: 2026-08-17
tags: [observability, testing, performance]
---

# TCK-20260817-DASHBOARD-PROGRESS-TIMELINE-ECHARTS-BUNDLE-VIOLATION

## Title
`dashboard-frontend/src/views/ProgressTimelineView.tsx` imports the full `echarts` bundle instead
of `echarts/core` + tree-shaken submodules

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while running `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP`'s full `tests/tools`
regression sweep: `test_agent_ops_dashboard_frontend_api_surface.py::test_no_source_file_imports_full_echarts_bundle`
fails because `dashboard-frontend/src/views/ProgressTimelineView.tsx` imports the full `echarts`
package (`from 'echarts'` or `require('echarts')`) rather than `echarts/core` plus tree-shaken
submodule imports, which every other dashboard-frontend view correctly uses. This is a real
bundle-size regression (the full `echarts` bundle is significantly larger than the tree-shaken
subset actually used), not a stale test.

## Scope
- Identify exactly which `echarts` chart types/components `ProgressTimelineView.tsx` actually uses.
- Rewrite its import to `echarts/core` plus the specific tree-shaken submodules it needs, matching
  the pattern already used by every other dashboard-frontend view file.
- Verify the dashboard still renders and functions correctly after the import change (visual/manual
  check, since this is frontend code this repo's own test suite doesn't fully cover).

## Out of Scope
- Any other dashboard-frontend architecture change.
- Any change to the echarts version itself.

## Acceptance Criteria
- [ ] `ProgressTimelineView.tsx` no longer imports the bare `echarts` package.
- [ ] `test_agent_ops_dashboard_frontend_api_surface.py::test_no_source_file_imports_full_echarts_bundle`
      passes.
- [ ] The Progress Timeline view still renders and functions correctly (manually verified — this
      repo's test suite doesn't cover frontend rendering).

## Related Tickets
- `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP` (found this while sweeping the `tests/tools`
  CI lane)

## Related Docs
None known yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `dashboard-frontend/src/views/ProgressTimelineView.tsx`
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`

## Assumptions / Open Questions
- Whether this is a recently-introduced regression or has existed since the file was authored is
  unconfirmed — `git log` on the file would clarify.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
