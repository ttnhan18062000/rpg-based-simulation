---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-PROGRESS-TIMELINE-VIEW-BARE-ECHARTS-IMPORT
phase: done
date: 2026-08-17
tags: [dashboard, bug]
---

# TCK-20260817-HOTFIX-PROGRESS-TIMELINE-VIEW-BARE-ECHARTS-IMPORT

## Title
Fix `ProgressTimelineView.tsx`'s stray bare `'echarts'` type import (tree-shaking rule violation)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Real CI failure on the "API / tools / logging" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_no_source_file_imports_full_echarts_bundle`
failed: `dashboard-frontend/src/views/ProgressTimelineView.tsx` imports the full `echarts` bundle,
violating the repo's tree-shaking rule (only `echarts/core` + tree-shaken submodule imports are
allowed).

Root cause (confirmed via investigation): `ProgressTimelineView.tsx:2` had
`import type { ECharts } from 'echarts'` — a type-only import from the bare package specifier. The
test's regex has no carve-out for `import type`, matching the repo's stated intent ("only
echarts/core plus tree-shaken submodule imports are allowed"). The file's runtime imports were
already fully compliant (`import * as echarts from 'echarts/core'` + explicit
`echarts.use([...])` registration); only the type import was non-compliant. The established
compliant sibling pattern in this repo (`dashboard-frontend/src/test/liveTickMerge.test.ts`) never
imports from bare `'echarts'` at all — it references the type via the already-imported namespace
(`echarts.ECharts`), which `echarts/core`'s own type declarations re-export.

## Scope
- `dashboard-frontend/src/views/ProgressTimelineView.tsx`: remove
  `import type { ECharts } from 'echarts'`; use `echarts.ECharts` (the namespace already imported
  from `echarts/core`) at both use sites instead.

## Out of Scope
- Any other ticket in this batch.
- Any change to the file's already-compliant runtime submodule imports/registration.

## Acceptance Criteria
- [ ] No bare `'echarts'` import remains in `ProgressTimelineView.tsx`.
- [ ] `test_no_source_file_imports_full_echarts_bundle` passes.
- [ ] TypeScript compiles clean (`tsc -b --noEmit`).

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `dashboard-frontend/src/views/ProgressTimelineView.tsx`

## Implementation Notes
Removed `import type { ECharts } from 'echarts'`. Replaced both use sites
(`useRef<ECharts | null>(null)` and `onChartReady={(instance: ECharts) => {`) with
`echarts.ECharts`, using the already-imported `* as echarts from 'echarts/core'` namespace —
matching `liveTickMerge.test.ts`'s established pattern exactly.

## Test Summary
- `pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q`: 4 passed.
- `npx tsc -b --noEmit` (dashboard-frontend): clean, no errors.

## Files Changed
- `dashboard-frontend/src/views/ProgressTimelineView.tsx` — removed bare `echarts` type import,
  replaced 2 use sites with `echarts.ECharts`.

## Completion Summary
Fixed the one stray bare-package import in the frontend source tree. No new submodule imports were
needed — `echarts/core`'s own re-exported types cover the case, matching an already-established
in-repo pattern.
