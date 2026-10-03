---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-DASHBOARD-PROGRESS-TIMELINE-ECHARTS-BUNDLE-VIOLATION
phase: done
date: 2026-08-17
tags: [observability, testing, performance]
---

# TCK-20260817-DASHBOARD-PROGRESS-TIMELINE-ECHARTS-BUNDLE-VIOLATION

## Title
`dashboard-frontend/src/views/ProgressTimelineView.tsx` imports the full `echarts` bundle instead
of `echarts/core` + tree-shaken submodules

## Status
DONE

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
None remaining.

## Implementation Notes
**Already fixed this same session** as `TCK-20260817-HOTFIX-PROGRESS-TIMELINE-VIEW-BARE-ECHARTS-IMPORT`
(`tickets/done/`), found independently via the real "API / tools / logging" CI job log rather than
this ticket. Root cause: a single stray `import type { ECharts } from 'echarts'` (type-only, not a
runtime import) — every runtime submodule import in the file was already correctly tree-shaken
(`echarts/core` + specific chart/component/renderer imports). Fixed by referencing the type via the
already-imported `echarts` namespace (`echarts.ECharts`) instead, matching an established
in-repo pattern (`dashboard-frontend/src/test/liveTickMerge.test.ts`).

Re-verified for this ticket's own closure (the original fix only confirmed `tsc --noEmit`):
production build (`npm run build`) succeeds; dev server (`npm run dev`) serves the view at HTTP
200 with the transformed module resolving to `echarts_core.js` (the tree-shaken core), no bare
`echarts` import present anywhere in the transformed output.

## Test Summary
- `pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_no_source_file_imports_full_echarts_bundle -q`:
  1 passed.
- `npm run build` (dashboard-frontend): succeeds, no errors.
- `npm run dev` + `curl http://127.0.0.1:5199/`: HTTP 200; `curl .../src/views/ProgressTimelineView.tsx`
  shows the transformed module importing `echarts_core.js`, not the full `echarts` package.

## Files Changed
None by this ticket directly — resolved by `TCK-20260817-HOTFIX-PROGRESS-TIMELINE-VIEW-BARE-ECHARTS-IMPORT`'s
change to `dashboard-frontend/src/views/ProgressTimelineView.tsx`.

## Completion Summary
Confirmed already resolved by a sibling ticket from this same session's CI-fix batch, found
independently via the real CI log. Closing with the additional dev-server/build verification this
ticket's own acceptance criteria called for (beyond the original fix's typecheck-only check).
