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
Thin HUD foundation — two-tier tokens, minimal layout wrapper, durable selection state, baseline
measurement — before the M2 vertical slice (M1 of `docs/plans/hud_delivery_roadmap.md`, revised)

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
JSX in `App.tsx`; theming is a single flat 11-token CSS layer with no semantic indirection; and there is no
durable selection/navigation state, so `Sidebar.tsx`'s automatic mode-switching
(`isBuildingView`/`isLootView`/`isSpectating`) silently drops scroll position, active tab, and prior entity
context.

**Revision (2026-08-22):** the originally-scoped version of this epic planned a *full* chassis — complete
navigation-map redesign, a formal scoring-rubric doc, a full named-slot layout engine, and a mandatory
three-tier token system — all gating every downstream HUD milestone. An external design review
(`tmp/hud_review.md`) made a well-grounded case that this over-commits to abstractions before any real HUD
content proves they're the right ones, and that it echoes this project's own CLAUDE.md instinct against
premature abstraction better to build a thin foundation, validate it against one real workflow
(`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`, M2), then extract the rest from what that slice actually
needs (`TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING`, M3). This epic's scope below is the user-approved
hybrid: ship only what's justified immediately regardless of sequencing.

## Scope
1. **Two-tier semantic tokens** — add a semantic layer on top of `index.css`'s existing primitive
   `@theme` block (e.g. `surface-panel`, `text-critical`, `border-interactive` mapping onto the existing
   raw color values). Component-level (third-tier) tokens are explicitly deferred to M3, added only where a
   real independent contract emerges from the M2 slice — not declared as a mandatory tier here. Resolve
   whether the existing unused `@custom-variant dark` declaration is a real planned feature or dead
   scaffold.
2. **Minimal layout wrapper** — a small wrapper component around the current
   `Header → [GameCanvas, Sidebar]` arrangement, cleaning up the inline JSX in `App.tsx` — not a full
   named-slot/config-driven skeleton engine. A named-slot engine is deferred to M3, built only if M2's
   slice demonstrates a real need to rearrange top-level regions.
3. **Durable selection/navigation state model** — explicit, separated state for: active workspace, camera
   position, selected entity/location/event, open inspector/tab, active filter/search query. Fixes the
   concrete failure mode the external review identified in the *current* code: `Sidebar.tsx`'s
   `isBuildingView`/`isLootView`/`isSpectating` auto-switch silently destroys the previous panel's scroll
   position, active tab, and entity context when it fires.
4. **`EntityList.tsx` basic search/filter, with a re-ranked default view** — add text search/filter
   (necessary regardless of sequencing). Replace the current hardcoded hero-first/ID sort with a default
   ranking driven by information volatility/attention-worthiness (recently-changed, currently-visible,
   anomalous entities first) rather than static/alphabetical order — per direct user instruction that the
   HUD should prioritize by what actually changes and what a player watches, not by static ordering. The
   fuller entity-exploration system (facets, grouping, saved views, aggregate-to-detail at the ~10,000-entity
   target scale) is deferred to M3, informed by what M2's slice actually needs.
5. **Baseline measurement** — pick 3-5 representative observer tasks (e.g. "find a specific entity by
   name," "notice a recent anomalous event," "trace why an entity changed state") and measure them against
   the *current*, unmodified HUD before any further change lands. This is the evidence M4 compares against
   — without it, M4 would have a rubric but nothing real to score improvement against.

## Out of Scope
- The full named-slot layout engine, the third (component-level) token tier, and any formal scoring-rubric
  document — all deferred to `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3), built only from what
  `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2)'s real vertical slice demonstrates is actually needed, not
  built speculatively here.
- The full entity-exploration system (faceted filters, grouping, saved queries, aggregate-to-detail views)
  — item 4 above ships only basic text search/filter and default re-ranking; the rest is M3's scope,
  informed by M2.
- Any HUD content wiring beyond the four thin-foundation pieces above (the M2 vertical slice does the real
  content work) — that is `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`, gated on this epic.
- Wiring the mode-triggered panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`) — that is
  `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3), gated on M2.
- Measuring the finished HUD against the baseline, or a systematic progressive-disclosure polish pass —
  that is `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4), gated on M3.
- The live-map renderer (`GameCanvas.tsx`, `useCanvas.ts`) and its own reconnection/scaling roadmap
  (`docs/plans/live_map_scaling_roadmap.md`) — a fully separate effort, no file overlap.

## Acceptance Criteria
- [ ] `index.css` has a real semantic token layer (Layer 2) on top of the existing primitives; at least one
      existing consuming component is migrated from a Layer-1-shaped class name to a Layer-2 semantic one
- [ ] `App.tsx`'s inline layout JSX is wrapped in a small, named layout component (not necessarily
      slot/config-driven yet — that's M3's call if M2 proves it's needed)
- [ ] A durable selection/navigation state model exists and is verified against the specific
      `isBuildingView`/`isLootView`/`isSpectating` context-loss failure mode this epic was scoped to fix
- [ ] `EntityList.tsx` has working text search/filter, and its default (no-filter) view is ranked by
      recency/change/anomaly rather than the old hardcoded hero-first/ID sort
- [ ] A baseline measurement result exists for 3-5 representative observer tasks, recorded and dated,
      before M2 begins
- [ ] No HUD panel content wiring happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2, gated on this epic (hard prerequisite)
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3, gated on this epic (hard prerequisite), independent
  of M2
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4, gated on M2 + M3, not directly on this epic
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1 of the separate live-map roadmap) — independent effort, no
  file overlap; noted only because both are player-facing frontend work landing around the same time
- `TCK-20260822-SEMANTIC-TOKEN-LAYER` — child ticket, scope item 1 (two-tier semantic token layer)
- `TCK-20260822-APP-LAYOUT-WRAPPER` — child ticket, scope item 2 (minimal layout wrapper)
- `TCK-20260822-DURABLE-SELECTION-STATE` — child ticket, scope item 3 (durable selection/navigation state)
- `TCK-20260822-ENTITY-LIST-SEARCH-RANK` — child ticket, scope item 4 (EntityList search/filter + ranking)
- `TCK-20260822-HUD-BASELINE-MEASUREMENT` — child ticket, scope item 5 (baseline usability measurement)

## Related Docs
- `docs/plans/hud_design_system_foundation_epic.md` — this epic's original full plan doc (problem
  statement, five-part idea, open questions, references) — scope has since narrowed per the revision above
- `docs/plans/hud_delivery_roadmap.md` — the revised milestone sequencing this epic is M1 of
- `tmp/hud_review.md` — the external design review that prompted this epic's scope revision

## Related Stored Artifacts
None.

## Related Code Areas
- `frontend/src/App.tsx` — target of scope item 2 (minimal layout wrapper)
- `frontend/src/index.css` — target of scope item 1 (semantic tokens)
- `frontend/src/components/Sidebar.tsx` — target of scope item 3 (durable selection state, fixing the
  auto-switch context-loss failure mode)
- `frontend/src/components/EntityList.tsx` — target of scope item 4 (search/filter, re-ranked default view)

## Assumptions / Open Questions
- **Revision note:** the navigation-map redesign and formal scoring-rubric doc originally planned as scope
  items 1-2 are dropped from this epic's scope, not silently lost — a full navigation-map decision only
  matters once M2/M3 reveal whether page-level views are actually needed, and the rubric is replaced here
  by a concrete baseline measurement (scope item 5), which is more load-bearing at this stage than a
  rubric with nothing yet to score. Revisit both if M2's slice surfaces a real need.
- `@custom-variant dark` status (real planned feature vs. dead scaffold) — still open, resolve during
  scope item 1.
- The exact 3-5 representative baseline tasks are not chosen here — pick them from what this project's own
  simulation actually surfaces as meaningful (factions, quests, calamities, economy, entity anomalies),
  not invented in the abstract.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
