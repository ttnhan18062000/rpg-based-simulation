---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-ENTITY-LIST-SEARCH-RANK
phase: open
date: 2026-08-22
tags: [hud]
---

# TCK-20260822-ENTITY-LIST-SEARCH-RANK

## Title
Add search/filter and attention-driven ranking to EntityList

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add basic text search/filter to EntityList.tsx, and replace the hardcoded hero-first/ID-sort default with a ranking driven by information volatility/attention-worthiness (recently-changed, currently-visible, anomalous entities first).

## Scope
- Add text search/filter to EntityList.tsx: typing a query filters rendered entities by case-insensitive substring match on id or kind, with an empty-state message shown when zero results match.
- Replace the current hardcoded hero-first/ID-sort default order with a volatility/attention-driven ranking (entities whose hp, state, or position changed since the previous poll rank ahead of static id order) when no search query is active.
- Extend EntityListProps with the new search/ranking surface without breaking the existing entities/selectedEntityId/onSelect contract, so Sidebar.tsx's usage still type-checks unchanged.

## Out of Scope
- A "currently-visible" ranking signal — no visibility field exists on EntitySlim today and no prop threads a visible-set concept into EntityList.tsx/useSimulation.ts (the only related concept, fog-of-war, lives in useCanvas.ts/GameCanvas.tsx); omitting/deferring this is acceptable if explicitly documented.
- Any backend/API change to EntitySlim (id, kind, x, y, hp, max_hp, state, level, tier, faction, weapon_range, combat_target_id, loot_progress, loot_duration) — ranking is computed client-side via diffing against the previous poll.
- Faceting, grouping, or saved-views — explicitly deferred to M3.
- Any HUD panel content wiring beyond EntityList itself, per the epic's statement that no HUD panel content wiring happens directly on the epic ticket.

## Acceptance Criteria
- [ ] Typing a query filters the rendered list to entities whose id or kind substring-matches case-insensitively; an empty-state message is shown when zero entities match.
- [ ] With no search query, default render order ranks entities by a volatility/attention score (hp changed, state changed, or position changed since the previous poll) ahead of static id order, verified by a non-hero entity that just took damage rendering above an untouched hero.
- [ ] EntityListProps gains the new search/ranking surface without breaking the existing entities/selectedEntityId/onSelect contract; Sidebar.tsx's usage still type-checks unchanged.
- [ ] If a "currently-visible" signal is included, it comes from an explicit new prop, not invented ad hoc; omitting/deferring it is an acceptable, explicitly documented outcome.

## Related Tickets
- TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION
- TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING
- TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/components/EntityList.tsx
- frontend/src/types/api.ts
- frontend/src/hooks/useSimulation.ts
- frontend/src/hooks/useCanvas.ts
- frontend/src/components/Sidebar.tsx
- frontend/src/test/useSimulation.test.tsx

## Assumptions / Open Questions
- Ranking needs client-side diffing against the previous poll (via useRef in EntityList/useSimulation), since EntitySlim has no last-updated-tick, delta, or anomaly-flag field; no backend change is required.
- Wiring a "currently-visible" signal is real cross-component plumbing (the fog-of-war concept lives in useCanvas.ts/GameCanvas.tsx, not threaded into EntityList today) and may be scoped out of this ticket.
- No EntityList-specific test file exists yet; one must be added, not assumed to already exist.
- Soft sequencing note: TCK-20260822-DURABLE-SELECTION-STATE (a sibling child ticket of the same parent epic) introduces a durable state slot for filter/search query. If that ticket is implemented first, this ticket's search-query state should plug into it directly instead of using local component state; not a hard blocking dependency, just a recommended order if both are picked up close together.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
