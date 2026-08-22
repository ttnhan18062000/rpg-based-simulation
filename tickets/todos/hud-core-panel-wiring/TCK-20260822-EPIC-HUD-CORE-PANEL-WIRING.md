---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING
phase: open
date: 2026-08-22
tags: [architecture, hud]
---

# TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING

## Title
Wire Sidebar's always-available core tabs (info/inspect/events) into the M1 skeleton and theme, fix
EntityList's missing search/filter — gated on M1

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1 of `docs/plans/hud_delivery_roadmap.md`) builds the
navigation map, layout skeleton, theme-token system, and component-slot wiring convention. This epic exists
to track re-plugging `Sidebar.tsx`'s core, always-available tabs — `info`, `inspect` (backed by
`InspectPanel.tsx`'s 7 sub-tabs: Stats/Class/Events/Quests/Effects/AI/Narrative), and `events` (backed by
`EventLog.tsx`) — into that chassis once it exists, as its own milestone (M2), separate from M1 since it
touches content these panels render, not the chassis itself.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M1 ships
(see Assumptions / Open Questions). Prospective scope:
- Re-plug `Sidebar.tsx`'s tab system into M1's named-slot skeleton, replacing whatever ad-hoc positioning
  it currently has inside `App.tsx`'s hardcoded row.
- Migrate `Sidebar.tsx`, `InspectPanel.tsx`, `EntityList.tsx`, `EventLog.tsx` from M1's Layer-1-shaped
  Tailwind classes (`bg-bg-secondary`, `text-accent-blue`, etc.) to M1's new Layer-2 semantic tokens.
- Fix the concrete gap already identified: `EntityList.tsx` (`frontend/src/components/EntityList.tsx`) has
  zero search or filter state — `EntityListProps` carries only `entities`, `selectedEntityId`, `onSelect`,
  with a hardcoded hero-first/ID sort over a flat scrolling list. Add search/filter, sized for this
  project's ~10,000-entity target scale, and measured against M1's own navigation-search-success metric
  once that rubric exists.
- Verify each tab's underlying data path against whatever the live-map reconnection effort
  (`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`) has shipped by the time this epic starts — `/api/v1/state`
  already returns full entity/event data today (unfiltered, full-snapshot), so this is a real-data-source
  verification pass, not a from-scratch backend integration.

## Out of Scope
- Everything in M1's own scope (`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`) — this epic starts only
  after M1 ships.
- The mode-triggered contextual panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`,
  `ControlPanel.tsx`, `Legend.tsx`) — that's `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3), a
  separate, independent epic with no dependency on this one.
- Measuring the finished result against M1's rubric, or a systematic progressive-disclosure polish pass —
  that's `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4), gated on this epic plus M3.
- Building any new backend endpoint beyond what the live-map reconnection effort already ships; if this
  epic's data-path verification finds a genuine gap, that becomes its own future ticket, not silently
  absorbed here.

## Acceptance Criteria
- [ ] Not started until `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1) is DONE
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic and `docs/plans/hud_delivery_roadmap.md`
- [ ] `EntityList.tsx` search/filter is explicitly one of the child tickets, not silently dropped
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1, a hard prerequisite (not a soft reference): this
  epic does not start, and should not even be broken into child tickets, until M1 ships.
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3, an independent sibling epic (also gated on M1, no
  dependency between M2 and M3 in either direction).
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4, gated on this epic plus M3.
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` — separate effort; its real-time entity broadcast (once
  shipped) benefits this epic's data-path quality but is not a hard dependency.

## Related Docs
- `docs/plans/hud_delivery_roadmap.md` — the milestone sequencing this epic is M2 of
- `docs/plans/hud_design_system_foundation_epic.md` — M1's design source (skeleton slots, semantic tokens,
  component-slot convention) this epic's wiring depends on

## Related Stored Artifacts
None.

## Related Code Areas
- `frontend/src/components/Sidebar.tsx`, `EntityList.tsx`, `InspectPanel.tsx`, `EventLog.tsx` — the files
  this epic modifies

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until M1 is DONE and its skeleton/token/wiring conventions exist. Revisit scope-item detail once M1's
  actual shape is known; it may narrow, widen, or reprioritize what's written above.
- Whether `EntityList.tsx`'s search/filter needs client-side or server-side filtering at the ~10,000-entity
  target scale is not resolved here — worth a real measurement once M1's metrics rubric exists to test
  against, rather than assumed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
