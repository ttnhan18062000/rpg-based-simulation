---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-SEMANTIC-TOKEN-LAYER
phase: open
date: 2026-08-22
tags: [hud, design-system, architecture]
---

# TCK-20260822-SEMANTIC-TOKEN-LAYER

## Title
Add two-tier semantic token layer to index.css

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Add a semantic token layer (e.g. surface-panel, text-critical, border-interactive) on top of index.css's existing flat primitive @theme block, mapping semantic names onto the existing raw color values. Migrate at least one existing consuming component from a Layer-1 primitive class name to the new Layer-2 semantic one. Also resolve whether the existing unused @custom-variant dark declaration is a real planned feature or dead scaffold.

## Scope
- Add a Layer 2 semantic token block to frontend/src/index.css that maps semantic names (surface-panel, text-critical, border-interactive, etc.) onto the existing 11 Layer-1 primitive values, without duplicating raw hex.
- Migrate InspectPanel.tsx (best target, ~230 raw-class occurrences) from Layer-1 primitive class names to the new Layer-2 semantic equivalents, preserving identical rendering.
- Investigate and record a written, evidence-backed determination of whether the existing @custom-variant dark declaration in index.css is a real planned feature or dead scaffold.

## Out of Scope
- Migrating the other 11 components (ClassHallPanel.tsx, BuildingPanel.tsx, ApiDocsPage.tsx, Sidebar.tsx, EntityList.tsx, EventLog.tsx, ControlPanel.tsx, LootPanel.tsx, Legend.tsx, Header.tsx, GameCanvas.tsx) — deferred to M3, stated as deferred not incomplete.
- Introducing a Layer 3 (component-level) token tier — explicitly excluded by the epic's Out-of-Scope.
- Building automated visual-regression test infrastructure (none exists today; package.json has no test script for styling).
- Deleting @custom-variant dark outright without recording rationale — decision must be documented, not silently applied.

## Acceptance Criteria
- [ ] index.css defines a Layer 2 semantic token block whose values reference the existing 11 Layer-1 primitives rather than duplicating raw hex; Layer-1 primitives remain unmodified.
- [ ] At least one consuming component (InspectPanel.tsx) has utility classes migrated from Layer-1-shaped names to Layer-2 semantic equivalents, and the component renders identically to before migration.
- [ ] A written, evidence-backed determination is recorded for whether @custom-variant dark is real or dead scaffold, referencing the grep evidence (zero .dark toggles, zero dark: prefixed classes, no theme-switch hook anywhere).
- [ ] No Layer 3 tokens are introduced anywhere in the change.
- [ ] New Layer-2 token names do not collide with existing Tailwind-generated utility names during @theme resolution.

## Related Tickets
- TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION

## Related Docs
- docs/plans/hud_design_system_foundation_epic.md
- docs/plans/hud_delivery_roadmap.md

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/index.css — Layer 2 semantic token block added here
- frontend/src/components/InspectPanel.tsx — migration target for this ticket

Not touched by this ticket (found during investigation, explicitly deferred to M3 per Out of Scope):
ClassHallPanel.tsx, BuildingPanel.tsx, ApiDocsPage.tsx, Sidebar.tsx, EntityList.tsx, EventLog.tsx,
ControlPanel.tsx, LootPanel.tsx, Legend.tsx, Header.tsx, GameCanvas.tsx — all under
frontend/src/components/.

## Assumptions / Open Questions
- Whether @custom-variant dark is dead scaffold vs a planned feature is treated as a product decision requiring explicit recorded rationale, not assumed deletable without sign-off.
- Migrating only "at least one" component to Layer 2 leaves the remaining 11 intentionally mixed until M3; accepted as deferred-not-incomplete per roadmap.
- No automated visual-regression check exists, so "renders identically" must be verified by manual/visual comparison, not a script.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
