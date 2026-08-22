---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-APP-LAYOUT-WRAPPER
phase: open
date: 2026-08-22
tags: [hud, design-system, architecture]
---

# TCK-20260822-APP-LAYOUT-WRAPPER

## Title
Extract minimal AppLayout wrapper from App.tsx

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Introduce a small, named wrapper component around the current Header -> [GameCanvas, Sidebar] arrangement, cleaning up the inline layout JSX currently hardcoded in App.tsx. This is explicitly not a full named-slot/config-driven layout engine.

## Scope
- Extract a new named layout component (e.g. AppLayout/HudLayout) from App.tsx's current lines 35-81, preserving the outer h-screen flex flex-col overflow-hidden wrapper, the Header render, and the currentPage === 'simulation' ? [GameCanvas, Sidebar] : ApiDocsPage conditional exactly as-is, both branches.
- Shrink App.tsx to state/handler ownership plus a single render call into the new wrapper, with unchanged prop names/types.
- Add a new component-render test (e.g. AppLayout.test.tsx, vitest + @testing-library/react pattern) asserting Header always renders and GameCanvas+Sidebar vs ApiDocsPage render conditionally on currentPage.

## Out of Scope
- Any generic named-slot map or layout config object — explicitly a non-goal per epic AC #2 and roadmap M1, deferred to M3's full named-slot/config-driven layout engine.
- Changing what regions exist or what's docked in them today (epic Part 3 constraint).
- Any behavior change to Header, GameCanvas, Sidebar, or ApiDocsPage themselves beyond being rendered from the new wrapper.

## Acceptance Criteria
- [ ] A new named layout component is extracted from App.tsx lines 35-81, preserving the outer h-screen flex flex-col overflow-hidden wrapper, Header render, and both branches of the currentPage === 'simulation' ? [GameCanvas, Sidebar] : ApiDocsPage conditional exactly as-is.
- [ ] App.tsx shrinks to state/handler ownership plus a single render call into the new wrapper, with the same props and no prop name/type changes.
- [ ] npm run build (tsc -b && vite build) succeeds with zero new TypeScript errors.
- [ ] The new wrapper takes plain typed props for the fixed arrangement only — no generic named-slot map, no layout config object.
- [ ] A new component-render test asserts Header always renders and GameCanvas+Sidebar vs ApiDocsPage render conditionally on currentPage.

## Related Tickets
- TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION
- TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING
- TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING

## Related Docs
- docs/plans/hud_delivery_roadmap.md
- docs/plans/hud_design_system_foundation_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/App.tsx
- frontend/src/components/Header.tsx
- frontend/src/components/GameCanvas.tsx
- frontend/src/components/Sidebar.tsx
- frontend/src/components/ApiDocsPage.tsx

## Assumptions / Open Questions
- No existing test exercises App.tsx's render output today, so the new test is net-new coverage, not a migration of an existing test.
- "Small wrapper component" is bounded by explicit non-goal checks against named slots/config props, to guard against scope creep toward M3's deferred engine.
- The wrapper must cover both the simulation and ApiDocsPage branches, since App.tsx mounts ApiDocsPage as an alternate top-level page when currentPage !== 'simulation'.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
