---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING
phase: open
date: 2026-08-22
tags: [architecture, hud]
---

# TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING

## Title
Wire the mode-triggered contextual panels (Building/Loot/ClassHall/Control/Legend) into the M1 skeleton and
theme — gated on M1, independent of M2

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
navigation map, layout skeleton, theme-token system, and component-slot wiring convention.
`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2) re-plugs `Sidebar.tsx`'s always-available tabs into that
chassis. This epic exists to track the other half of the HUD panel inventory — the mode-triggered,
specialized panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`,
`Legend.tsx`) that `Sidebar.tsx`'s own `useEffect` already auto-switches to based on `isBuildingView` /
`isLootView` / `isSpectating` state — as its own milestone (M3), independent of M2 since these panels
consume different, more specialized backend data (buildings, loot, class-hall state) than M2's always-on
entity/event feed.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M1 ships
(see Assumptions / Open Questions). Prospective scope:
- Re-plug `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`, `Legend.tsx` into
  M1's named-slot skeleton, replacing whatever ad-hoc positioning they currently have inside `Sidebar.tsx`'s
  mode-switch logic.
- Migrate each from M1's Layer-1-shaped Tailwind classes to M1's new Layer-2 semantic tokens, matching
  M2's own migration so the two milestones don't diverge on token usage.
- Verify each panel's underlying data path against the real V2 backend (buildings, resource nodes, chests,
  ground_items, class-hall state) — these fields already exist on `AuthoritativeState`
  (`src/core/state.py`), so this is a real-data-source verification pass per panel, not a from-scratch
  backend integration; any genuine gap found becomes its own future ticket.

## Out of Scope
- Everything in M1's own scope (`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`) — this epic starts only
  after M1 ships.
- The always-available core tabs (`Sidebar.tsx` info/inspect/events, `EntityList.tsx`, `InspectPanel.tsx`,
  `EventLog.tsx`) — that's `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2), a separate, independent epic
  with no dependency on this one.
- Measuring the finished result against M1's rubric, or a systematic progressive-disclosure polish pass —
  that's `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4), gated on this epic plus M2.
- Building any new backend endpoint beyond what already exists on `AuthoritativeState`; if this epic's
  data-path verification finds a genuine serialization gap (a field that exists in state but has no
  presenter path to the API), that becomes its own future ticket, not silently absorbed here.

## Acceptance Criteria
- [ ] Not started until `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1) is DONE
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic and `docs/plans/hud_delivery_roadmap.md`
- [ ] Token usage stays consistent with `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`'s (M2) own migration —
      any real divergence in slot/token conventions gets surfaced back to M1, not resolved independently
      by each milestone
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1, a hard prerequisite (not a soft reference): this
  epic does not start, and should not even be broken into child tickets, until M1 ships.
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2, an independent sibling epic (also gated on M1, no
  dependency between M2 and M3 in either direction; soft coordination note on shared token conventions
  only).
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4, gated on this epic plus M2.

## Related Docs
- `docs/plans/hud_delivery_roadmap.md` — the milestone sequencing this epic is M3 of
- `docs/plans/hud_design_system_foundation_epic.md` — M1's design source (skeleton slots, semantic tokens,
  component-slot convention) this epic's wiring depends on

## Related Stored Artifacts
None.

## Related Code Areas
- `frontend/src/components/BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`,
  `Legend.tsx` — the files this epic modifies
- `frontend/src/components/Sidebar.tsx` — the mode-switch (`isBuildingView`/`isLootView`/`isSpectating`)
  this epic's panels are triggered by, read but not modified here (modified by M2 instead)

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until M1 is DONE and its skeleton/token/wiring conventions exist. Revisit scope-item detail once M1's
  actual shape is known; it may narrow, widen, or reprioritize what's written above.
- Whether M2 or M3 starts first once M1's gate clears is not decided here — both are independent and
  either order (or parallel execution) is valid per `docs/plans/hud_delivery_roadmap.md`'s sequencing
  rules.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
