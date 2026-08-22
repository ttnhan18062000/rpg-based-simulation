---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION
phase: open
date: 2026-08-22
tags: [architecture, hud, design-system]
---

# TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION

## Title
Bootstrap the HUD design-system chassis — navigation map, UX metrics/scoring rubric, composable layout
skeleton, tiered theme tokens, component-slot architecture — before any HUD content work (M1 of
`docs/plans/hud_delivery_roadmap.md`)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Prior investigation this session found the HUD's actual content components (`Sidebar.tsx`,
`InspectPanel.tsx`, `EntityList.tsx`, and siblings) already built and architecturally sound — mode-driven
tabs, progressive disclosure, color-coded scanning, tooltips. What's missing is the chassis underneath
them: navigation is a flat 2-button page switch with everything else at panel level; layout is hardcoded
JSX in `App.tsx` with no swappable-arrangement primitive; theming is a single flat 11-token CSS layer with
no semantic indirection; and there is no explicit, measurable rubric to compare design candidates against.
The user's direct instruction: decide the navigation map, define how design quality is measured, build the
skeleton and theme as swappable systems, and make HUD components pluggable into that chassis, before
resuming HUD content design — "think about crafting part by part, component by component."

## Scope
1. **Navigation map** — define the full set of top-level views vs. panel-level navigation. Resolve whether
   deeper information (faction/economy/calamity aggregate state, cross-entity comparison) warrants new
   top-level pages beyond the current `simulation` / `api-docs` pair, or stays panel-level within
   `simulation`. Update `Header.tsx`'s `PageView` type and nav if new pages are warranted.
2. **Metrics & scoring rubric** — a short scoring doc (mirroring `docs/simulation_quality/quality_scoring_contract.md`'s
   shape) defining Task Success Rate, click/interaction-depth budget, screen real-estate allocation, and
   navigation/search success rate, plus the 3-5 representative tasks ("find the lowest-HP hero," etc.)
   candidates get measured against. Resolve the open question of composite grade vs. separate metrics
   explicitly rather than defaulting silently.
3. **Composable layout skeleton** — replace `App.tsx`'s hardcoded `Header → [GameCanvas, Sidebar]` JSX with
   a named-slot layout primitive that the navigation map (item 1) and HUD panels (item 5) compose into, so
   a different top-level arrangement is a slot/config change, not an `App.tsx` rewrite.
4. **Tiered theme tokens** — upgrade `index.css`'s existing flat `@theme` block (11 CSS custom properties)
   into a three-tier system: Layer 1 primitives (kept as-is), Layer 2 semantic tokens (intent-based names
   components consume instead of near-primitive ones), Layer 3 component tokens for fine-grained overrides.
   Resolve whether the existing unused `@custom-variant dark` declaration is a real planned feature or dead
   scaffold, and scope Layer 2 accordingly (one preset vs. two from day one).
5. **Component-slot wiring convention** — define the convention M2/M3 (`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`,
   `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING`) will use to plug the already-decoupled, props-driven HUD
   components into the skeleton's slots. Not full content wiring — that is explicitly M2/M3's scope, gated
   on this epic.

## Out of Scope
- Wiring any HUD panel to real backend data, or fixing `EntityList.tsx`'s missing search/filter — that is
  `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2), gated on this epic.
- Wiring the mode-triggered panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`) — that is
  `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3), gated on this epic.
- Measuring the finished HUD against this epic's own rubric, or a systematic progressive-disclosure polish
  pass — that is `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4), gated on M2 + M3.
- The live-map renderer (`GameCanvas.tsx`, `useCanvas.ts`) and its own reconnection/scaling roadmap
  (`docs/plans/live_map_scaling_roadmap.md`) — a fully separate effort, no file overlap.
- Building a light theme preset, unless item 4's investigation into `@custom-variant dark` finds it's
  already a committed, planned feature rather than dead scaffold.

## Acceptance Criteria
- [ ] Navigation map decision documented: either the existing 2-page/panel-level shape is confirmed
      sufficient, or new top-level `PageView` variants are added to `Header.tsx` with a stated rationale
- [ ] A scoring-rubric doc exists, modeled on `quality_scoring_contract.md`'s shape, naming concrete metrics
      and 3-5 representative tasks
- [ ] `App.tsx`'s layout is expressed through a named-slot skeleton component, not inline hardcoded JSX —
      verified by an actual second slot arrangement being possible without editing `App.tsx` itself
- [ ] `index.css`'s theme is expressed as a real three-tier system (primitives / semantic / component
      tokens); at least one existing consuming component is migrated from a Layer-1-shaped class name to a
      Layer-2 semantic one, proving the remap-not-rewrite claim
- [ ] A documented component-slot wiring convention exists for M2/M3 to consume
- [ ] No HUD panel content wiring happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2, gated on this epic (hard prerequisite)
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3, gated on this epic (hard prerequisite), independent
  of M2
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4, gated on M2 + M3, not directly on this epic
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1 of the separate live-map roadmap) — independent effort, no
  file overlap; noted only because both are player-facing frontend work landing around the same time

## Related Docs
- `docs/plans/hud_design_system_foundation_epic.md` — this epic's full plan doc (problem statement,
  five-part idea, open questions, references)
- `docs/plans/hud_delivery_roadmap.md` — the milestone sequencing this epic is M1 of
- `docs/simulation_quality/quality_scoring_contract.md` — the internal precedent scope item 2's rubric is
  modeled on
- `docs/plans/live_map_scaling_roadmap.md` — the sibling roadmap this doc's own structure was deliberately
  mirrored from

## Related Stored Artifacts
None.

## Related Code Areas
- `frontend/src/App.tsx` — target of scope item 3 (skeleton)
- `frontend/src/components/Header.tsx` — target of scope item 1 (navigation)
- `frontend/src/index.css` — target of scope item 4 (theme tokens)
- `frontend/src/components/Sidebar.tsx`, `EntityList.tsx`, `InspectPanel.tsx`, `EventLog.tsx`,
  `ControlPanel.tsx`, `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `Legend.tsx` — consumers
  of scope item 5's wiring convention, not modified directly by this epic

## Assumptions / Open Questions
See `docs/plans/hud_design_system_foundation_epic.md`'s own Open Questions section (navigation-map scope,
composite-vs-separate scoring, `@custom-variant dark` status, representative-task list) — carried here by
reference rather than duplicated, since that doc is the living source for this epic's design questions.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
