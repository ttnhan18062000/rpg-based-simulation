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
One real end-to-end entity-investigation workflow through Sidebar/InspectPanel/EntityList/EventLog, using
only M1's thin foundation — gated on M1 (M2 of `docs/plans/hud_delivery_roadmap.md`, revised)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1) ships a thin foundation only — two-tier tokens, a
minimal layout wrapper, durable selection state, `EntityList` basic search. This epic exists to ship the
first real HUD content: not a batch of independently-wired panels, but **one complete, real, end-to-end
observer workflow**, built through the always-available core panels (`Sidebar.tsx`, `InspectPanel.tsx`,
`EntityList.tsx`, `EventLog.tsx`).

**Revision (2026-08-22):** originally scoped as "wire all of Sidebar's core tabs independently." An
external design review (`tmp/hud_review.md`) argued this risks validating each panel in isolation without
ever proving whether the actual cross-panel *workflow* an observer needs (notice something → find it →
understand it → follow it → return) actually works end-to-end. Revised to a single vertical slice instead:
this epic now produces the real evidence `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3) extracts its
chassis pieces from, rather than each panel being wired ad hoc.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M1 ships
(see Assumptions / Open Questions). Prospective scope — implement this one workflow, real and complete, not
simulated or stubbed:

1. **Notice** — an event or anomaly appears in `EventLog.tsx` (or the map).
2. **Locate** — find the entities involved, via `EntityList.tsx`'s search/filter and its
   volatility-ranked default view (both from M1) — not a flat alphabetical scan.
3. **Inspect** — open the entity in `InspectPanel.tsx`, see current and recent state (Stats/Events/Effects
   tabs at minimum).
4. **Follow** — navigate from that entity to a related entity, event, or location (a real relationship or
   causal link, not a placeholder), using M1's durable selection/navigation state.
5. **Return** — get back to the prior context (map position, selection, filters) with nothing silently
   lost — this step is the direct test of M1's durable-state fix for the `isBuildingView`/`isLootView`/
   `isSpectating` context-destruction failure mode.

Data-path note: verify each step's underlying data path against whatever the live-map reconnection effort
(`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`) has shipped by the time this epic starts — `/api/v1/state`
already returns full entity/event data today (unfiltered, full-snapshot), so this is a real-data-source
verification pass, not a from-scratch backend integration.

## Out of Scope
- Everything in M1's own scope (`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`) — this epic starts only
  after M1 ships.
- Wiring every remaining tab/sub-tab independently of the slice (e.g. `InspectPanel`'s Class/Quests/AI/
  Narrative tabs not touched by the workflow above) — those get wired in
  `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3), informed by what this slice proves, not duplicated
  here speculatively.
- The mode-triggered contextual panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`,
  `ControlPanel.tsx`, `Legend.tsx`) and any chassis extraction (named-slot engine, component tokens) — both
  `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3), which now starts *after* this epic, not in
  parallel with it.
- Measuring the finished result against M1's baseline, or a systematic progressive-disclosure polish pass —
  that's `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4), gated on M3.
- Building any new backend endpoint beyond what the live-map reconnection effort already ships; if this
  epic's data-path verification finds a genuine gap, that becomes its own future ticket, not silently
  absorbed here.

## Acceptance Criteria
- [ ] Not started until `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1) is DONE
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic and `docs/plans/hud_delivery_roadmap.md`
- [ ] The five-step workflow (notice/locate/inspect/follow/return) is implemented as one real, connected
      path — not five independently-testable panels with no proof they compose
- [ ] The "return" step is explicitly verified against M1's baseline: no lost scroll position, active tab,
      or entity context
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1, a hard prerequisite (not a soft reference): this
  epic does not start, and should not even be broken into child tickets, until M1 ships.
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3, now a downstream dependent, not an independent
  sibling (revised from the original parallel M2/M3 shape): M3 extracts its chassis pieces from what this
  epic's slice proves.
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4, gated on M3, which is itself gated on this epic.
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` — separate effort; its real-time entity broadcast (once
  shipped) benefits this epic's data-path quality but is not a hard dependency.

## Related Docs
- `docs/plans/hud_delivery_roadmap.md` — the revised milestone sequencing this epic is M2 of
- `docs/plans/hud_design_system_foundation_epic.md` — M1's original design source; scope has since
  narrowed per the revision above
- `tmp/hud_review.md` — the external design review that prompted this epic's revision to a single vertical
  slice

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
