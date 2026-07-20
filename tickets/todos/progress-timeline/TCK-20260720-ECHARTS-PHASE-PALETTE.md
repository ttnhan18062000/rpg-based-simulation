---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260720-ECHARTS-PHASE-PALETTE
phase: open
date: 2026-07-20
tags: [dashboard, observability]
---

# TCK-20260720-ECHARTS-PHASE-PALETTE

## Title
Add ECharts dependency and phase-to-color palette module

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Add the echarts and echarts-for-react packages to the frontend (tree-shaken imports only — echarts/core plus CustomChart, TooltipComponent, DataZoomComponent, GridComponent, CanvasRenderer). Define a deterministic phase-to-color mapping covering all 21 WORKFLOW_PHASES strings from tools/agent-monitoring/vocabulary.py; must be an explicitly-authored deterministic assignment, not reliant on Python set iteration order. This work is a stated prerequisite for the new ProgressTimelineView work, which will render each phase as a distinctly colored chart segment.

## Scope
- Add echarts and echarts-for-react to dashboard-frontend/package.json as dependencies; regenerate and commit package-lock.json
- Use only tree-shaken imports: echarts/core plus CustomChart, TooltipComponent, DataZoomComponent, GridComponent, CanvasRenderer — no source file imports the full 'echarts' bundle
- Create a new phase→color palette module (alongside dashboard-frontend/src/lib/chartPalette.ts) exporting a mapping whose key set exactly equals the 21 distinct WORKFLOW_PHASES strings
- Follow chartPalette.ts's existing pattern/convention: validate every color via the dataviz skill's contrast/lightness-band check against --color-bg-tertiary: #242835, documented in the module's header comment mirroring chartPalette.ts's existing comment convention
- Add a unit test asserting the literal 21-key list (not derived from iterating any Set) and asserting the mapping function/lookup is pure and deterministic (same phase string returns the same color across two calls)

## Out of Scope
- No visible UI change or chart rendering — acceptance stays scoped to completeness/contrast/build checks; end-to-end rendering is the ProgressTimelineView ticket's job
- No change to tools/agent-monitoring/vocabulary.py or WORKFLOW_PHASES itself
- No new automated cross-language sync guard between vocabulary.py and the TS palette — a hand-copied 21-item list with a completeness test is the accepted approach for this ticket
- C5 docs update (docs/guides/agent_ops_dashboard.md, docs/observability/agent_ops_dashboard_contract.md) is deferred to a separate follow-up ticket, not covered here

## Acceptance Criteria
- [ ] package.json declares echarts and echarts-for-react as dependencies with package-lock.json regenerated and committed; no source file imports the full 'echarts' bundle (only 'echarts/core' plus the five named tree-shaken imports/registrations appear anywhere in dashboard-frontend/src)
- [ ] the new phase→color palette module exports a mapping whose key set exactly equals the 21 distinct WORKFLOW_PHASES strings (Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize, Comprehend, Structure, Write, Link, Recalibrate, "Classify Drift", "Update Anchors", "Sync Docs", "Parity Check", Report), verified by a test asserting the literal key list — not derived from iterating any Set
- [ ] every color in the new palette passes the same contrast/lightness check chartPalette.ts already uses against --color-bg-tertiary: #242835, documented in the module's header comment mirroring chartPalette.ts's existing comment convention
- [ ] the mapping function/lookup is pure and deterministic (same phase string always returns the same color), unit-tested by calling it twice and asserting identical output

## Related Tickets
- TCK-20260718-STATS-TAB-FRONTEND
- TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT
- TCK-20260717-GANTT-TIME-AXIS
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/package.json
- dashboard-frontend/src/lib/chartPalette.ts
- dashboard-frontend/src/components/GroupedBarChart.tsx
- dashboard-frontend/src/components/BarChart.tsx
- dashboard-frontend/src/components/GanttBar.tsx
- dashboard-frontend/src/api.ts
- tools/agent-monitoring/vocabulary.py
- dashboard-frontend/package-lock.json

## Assumptions / Open Questions
- The dataviz skill must be loaded before authoring the palette; it was not discoverable by the investigating subagent's own local file search but is available in the orchestrating session's own skill listing
- WORKFLOW_PHASES lives only in Python with no automated sync to any TS mirror; a hand-copied 21-item TS list risks silent drift if vocabulary.py's phase sets change — this ticket hardcodes the list with a completeness test rather than adding a new backend round-trip, per the investigation's recommendation
- A 21-entry categorical palette is a much larger color budget than chartPalette.ts's existing 2-series palette, which already found --color-accent-* tokens fail the lightness-band check on this dark surface; distinguishability across 21 hues at required contrast may be difficult and could force fallback to non-color-only encoding (label/pattern) for some phases
- This ticket is a hard prerequisite for the ProgressTimelineView ticket, which consumes both the echarts dependency and this palette module
- `layer: observability` chosen (registered in docs/guidelines/layer_registry.jsonl) since this is dashboard-frontend/agent-monitoring visualization tooling, not a gameplay/simulation layer

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
