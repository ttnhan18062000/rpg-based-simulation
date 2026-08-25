---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260825-METADATA-PROVIDER-NONBLOCKING-FALLBACK
phase: open
date: 2026-08-25
tags: [hud, content]
---

# TCK-20260825-METADATA-PROVIDER-NONBLOCKING-FALLBACK

## Title
`MetadataProvider` hard-blocks the entire app (live map included) on a metadata-fetch failure --
make it degrade gracefully

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while broadly auditing "anything else related to" the live-map-reconnection and
world-rendering-core epics (`TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX`'s own audit turned up
a third, more severe issue than its own two). `frontend/src/main.tsx` wraps the entire app in
`<MetadataProvider>` (`frontend/src/contexts/MetadataContext.tsx`), which fetches 8
`/api/v1/metadata/*` sub-paths and, on any failure, rendered a full-screen "Failed to load game
metadata" error and never rendered `<App/>` at all -- the live map, sidebar, everything. Confirmed
live: none of the 8 `/api/v1/metadata/*` routes exist on the backend (404, not an auth issue) --
`TCK-20260825-METADATA-API-BACKEND-MISSING` is the real, substantive fix for that gap, filed
separately and routed to the HUD epic track (the real consumer of this data), since it is
substantial new backend work outside both epics being audited. This ticket is the narrow,
self-evident unblock: don't let an unrelated, optional detail-lookup data source hard-block the
whole app.

## Scope
- `frontend/src/contexts/MetadataContext.tsx`: on fetch failure, `console.error` for visibility and
  fall back to a correctly-shaped, all-empty `GameMetadata` object instead of setting a blocking
  `error` state. `useMetadata()`'s null-context guard must still never fire in this path -- the
  fallback object satisfies the type contract.
- Remove the now-dead blocking error-div render branch.
- Add a regression test confirming both paths: real metadata loads correctly on success, and a
  fetch failure still renders (not blocks) with an empty-but-valid `GameMetadata`.

## Out of Scope
- Building the real `/api/v1/metadata/*` backend routes -- `TCK-20260825-METADATA-API-BACKEND-MISSING`,
  filed separately, standard tier, routed to the HUD epic track.
- Any change to the 4 consuming panels (`BuildingPanel`/`LootPanel`/`ClassHallPanel`/`InspectPanel`)
  -- they already handle empty lookup maps correctly (no crash), just show no name/description,
  which is the expected degraded state until the backend ticket lands.

## Acceptance Criteria
- [x] A metadata-fetch failure no longer blocks `<App/>` from rendering
- [x] `useMetadata()` never throws in the failure path -- falls back to a valid, correctly-shaped
      empty `GameMetadata`
- [x] New test covers both the success and failure-fallback paths
- [x] Existing frontend test suite and build still pass

## Related Tickets
- TCK-20260825-METADATA-API-BACKEND-MISSING (the real fix -- building the actual backend routes;
  filed separately, not implemented here)
- TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX (this ticket was found during that one's own
  broader audit; consolidated into the same PR per direct user instruction)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- frontend/src/contexts/MetadataContext.tsx
- frontend/src/main.tsx (read-only reference -- confirms `MetadataProvider` wraps the whole app;
  not modified)

## Assumptions / Open Questions
None.

## Implementation Notes
Added `EMPTY_METADATA: GameMetadata` (all-empty arrays/objects/maps, matching every field
`buildMetadata()` would otherwise populate) as the fallback value. The `.catch()` handler now
`console.error`s the real failure reason (for developer visibility -- this is not meant to hide a
real bug once the backend exists) and calls `setMetadata(EMPTY_METADATA)` instead of `setError(...)`.
Removed the `if (error)` render branch entirely -- there is no longer any error state to render, only
the pre-existing `if (!metadata)` loading branch and the success branch.

## Test Summary
New `frontend/src/test/MetadataContext.test.tsx` (2 tests): confirms real metadata loads correctly
via `useMetadata()` on 8/8 successful fetches, and confirms `useMetadata()` still resolves (never
throws) with an empty-but-valid `GameMetadata` when all 8 fetches 404. Full frontend suite:
`npx vitest run` -- 30/30 passing (28 pre-existing + 2 new). `npm run build` -- clean.

## Files Changed
- `frontend/src/contexts/MetadataContext.tsx`
- `frontend/src/test/MetadataContext.test.tsx` (new)

## Completion Summary
The live map (and the rest of the app) can no longer be hard-blocked by an unrelated, currently-missing
optional metadata backend. The real backend gap is tracked and scoped correctly in its own ticket,
routed to the epic that actually owns the consuming HUD panels.
