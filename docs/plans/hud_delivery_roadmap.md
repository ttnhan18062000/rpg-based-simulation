---
status: active
layer: frontend
authority: P1
audience: agent
tags: [architecture, hud, design-system]
---

# Roadmap — HUD: Design-System Foundation, Then Content Delivery

**Purpose**: this player-facing HUD effort spans more work than one epic can hold cleanly. This doc ties
the milestones together and states the sequencing/gating rule once, instead of repeating it in each epic —
the same structure `docs/plans/live_map_scaling_roadmap.md` established for the live-map effort, applied
here. Per direct user instruction, the chassis (navigation map, UX metrics/scoring rubric, layout skeleton,
theme tokens, component-slot architecture) ships first and gates all HUD content work — content is not
designed or built speculatively against a chassis that doesn't exist yet.

## Milestones

### M1 — Design-System Foundation (the chassis)

**Tracking epic**: `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (already fully scoped — 5 scope items,
full plan doc at `docs/plans/hud_design_system_foundation_epic.md`).

Ships: the navigation map (page-level vs. panel-level navigation decided explicitly), the UX
metrics/scoring rubric (Task Success Rate, click-depth budget, real-estate allocation, navigation-search
success — modeled on this project's own SimQ grade-band convention), the composable layout skeleton
(replacing `App.tsx`'s hardcoded `Header → [GameCanvas, Sidebar]` JSX with named slots), the three-tier
theme-token system (primitives → semantic → component tokens, replacing `index.css`'s current flat
11-token layer), and the component-slot wiring convention the later milestones plug into.

**M1 is the milestone that produces the rubric and the slots M2/M3/M4 are built and measured against** —
without it, every panel wired in M2/M3 would need its own layout and theming decisions, and M4 would have
no objective way to score the result.

### M2 — Core Panel Content Wiring (gated on M1)

**Tracking epic**: `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (new, scope-only — see its own ticket).

Ships: `Sidebar.tsx`'s always-available tabs (`info` / `inspect` / `events`, backed by `InspectPanel.tsx`'s
7 sub-tabs and `EventLog.tsx`) plugged into M1's skeleton slots and consuming M1's semantic theme tokens
instead of near-primitive class names, plus the one already-identified concrete content gap:
`EntityList.tsx` has zero search/filter today, a hardcoded hero-first/ID sort over a flat list — a real
failure against M1's own navigation-search-success metric at this project's ~10,000-entity scale target.

**Gate**: does not start — not even scoped into child tickets — until M1 ships (skeleton slots and
semantic tokens must exist for these panels to be re-plugged into rather than re-hardcoded).

**Touches**: `frontend/src/components/Sidebar.tsx`, `EntityList.tsx`, `InspectPanel.tsx`, `EventLog.tsx`.

### M3 — Contextual Panel Content Wiring (gated on M1, independent of M2)

**Tracking epic**: `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (new, scope-only — see its own ticket).

Ships: the mode-triggered panels — `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`,
`ControlPanel.tsx`, `Legend.tsx` — plugged into M1's skeleton slots the same way M2's core panels are.
These consume different, more specialized backend data (buildings, loot, class-hall state) than M2's
always-on entity/event feed, so there is no data-layer dependency between M2 and M3.

**Gate**: does not start until M1 ships, same as M2. **Soft coordination note (not a hard gate):** M2 and
M3 both re-plug existing components into the same M1 skeleton/token system — whichever milestone starts
first should surface any real gaps found in M1's slot/token conventions (missing slot shape, a token that
doesn't generalize) back into M1 rather than each milestone quietly working around it differently.

**Touches**: `frontend/src/components/BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`,
`ControlPanel.tsx`, `Legend.tsx`.

### M4 — Content Polish & Rubric Measurement (gated on M2 + M3)

**Tracking epic**: `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (new, scope-only — see its own
ticket).

Ships: the actual application of the RimWorld/Crusader-Kings-style "structured complexity" content-design
direction researched alongside M1 (progressive disclosure via `CollapsibleSection`, consistent
color/tooltip layering, a stated click-depth budget) as a systematic pass across every panel M2 and M3
wired, plus the first real measurement of the finished HUD against M1's own rubric (Task Success Rate,
navigation-search success, etc.) — the earlier milestones ship working panels, this milestone proves they
meet the bar M1 set.

**Gate**: does not start until both M2 and M3 have shipped real, wired content to measure and polish —
measuring or polishing against panels that don't exist yet would be speculative, the same reasoning
`live_map_scaling_roadmap.md` applies to its own M2/M3 gating on M1.

**Touches**: cross-cutting — every component M2 and M3 touched, plus a new scored-result doc (shape
decided by M1's rubric-format open question — composite grade vs. separate metrics).

## Sequencing rules

- **M1 is a hard prerequisite for M2, M3, and M4.** None may start — not even be scoped into child
  tickets — before M1 ships.
- **M2 and M3 are independent of each other.** No dependency in either direction; either can be picked up
  first once M1's gate clears, or both can proceed in parallel — same shape as `live_map_scaling_roadmap.md`'s
  M2/M3 relationship.
- **M4 is a hard prerequisite gated on both M2 and M3**, not just one of them — it measures and polishes
  the full wired HUD, not a partial one.
- **Detailed child-ticket breakdown for M2, M3, and M4 is deliberately not done yet.** All three are
  scope-only at the epic tier for now — this roadmap and the three epic tickets exist to capture milestone
  structure and design intent, not to fully plan implementation before M1's chassis exists to build against.
- **Cross-roadmap note, not a gate:** this HUD roadmap is independent of `docs/plans/live_map_scaling_roadmap.md`
  (the live-map renderer effort) — different components (`GameCanvas.tsx`/`useCanvas.ts` vs.
  `Sidebar.tsx`/HUD panels), no file overlap. The one soft connection: M2's entity/event-focused panels
  benefit from live-map M1's real-time entity broadcast once it ships, rather than relying on full-snapshot
  polling — worth checking that effort's status before M2 starts, but not a hard dependency, since
  `/api/v1/state` already returns full entity/event data today, just without incremental push updates.

## References

- `docs/plans/hud_design_system_foundation_epic.md` — M1's full plan doc.
- `docs/plans/live_map_scaling_roadmap.md` — the sibling roadmap this doc's structure is deliberately
  mirrored from.
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1's ticket.
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2's ticket.
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3's ticket.
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4's ticket.
