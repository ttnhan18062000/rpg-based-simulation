---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE
phase: open
date: 2026-08-21
tags: [architecture, performance]
---

# TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE

## Title
Chunked terrain caching + two-bucket layered entity rendering for the live map, at real scale — gated on M1

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1 of `docs/plans/live_map_scaling_roadmap.md`) reconnects the
existing live-map renderer to the real backend but explicitly keeps `GameCanvas.tsx`/`useCanvas.ts`
untouched. Its own plan doc (§B, "Layered, Cache-First Rendering Architecture") already designed the
rendering-side fix for scaling to a huge map and thousands of entities — chunked terrain caching (real
browser canvas/memory limits researched, 512×512 chunks, viewport-radius eviction) and layered entity
rendering using a corrected two-bucket model (currently-animating entities redrawn every frame,
genuinely-idle ones skipped — corrected after an external design review found the original justification
conflated server-tick sparsity with render-frame sparsity, and independently verified via research into
real 2D-engine sprite architecture that the corrected model is sound). This epic exists to track that
already-designed work as its own milestone (M2), separate from M1, since it touches files M1 deliberately
does not.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M1 ships
(see Assumptions / Open Questions). Prospective scope, already designed in `docs/plans/live_map_reconnection_epic.md` §B:
- Chunk terrain into cached off-screen bitmaps (512×512 world-tile chunks — sized for this project's
  locally-generated terrain rather than the smaller 256×256 convention driven by remote-tile-fetch HTTP
  concerns that don't apply here), extending the exact off-screen-cache pattern already proven on this
  project's minimap to the main viewport. Retain tiles within a fixed buffer radius around the camera,
  evict outside it (Leaflet's `keepBuffer` pattern); invalidate a specific tile only on an actual
  terrain-change event inside it (event-driven, not time-based — this project's terrain is mutable, unlike
  static map tiles).
- Semi-static object layer (buildings, resource nodes, chests): chunk-level cache invalidation (rebuilding
  a whole chunk on any contained object's state change), not object-level.
- Dynamic entity layer: two-bucket dirty-rect rendering — track currently-animating entities (redrawn every
  frame, no saving expected or claimed) separately from genuinely-idle-since-last-frame entities (skipped
  entirely), rather than using the server's `DirtySet` as a proxy for render cost.

## Out of Scope
- Everything in M1's own scope (`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`) — this epic starts only after
  M1 ships.
- Starting any implementation before M1's real performance-validation pass provides measured evidence this
  is actually needed — the hard gate stated in `docs/plans/live_map_scaling_roadmap.md`.
- Migrating to a third-party rendering engine or WebGL — still ruled out per M1's plan doc §B; this epic
  extends the existing Canvas2D code, it does not replace it.
- Interest management / spatial broadcast filtering — that's `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`
  (M3), a separate, independent epic with no dependency on this one.

## Acceptance Criteria
- [ ] Not started until `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1) is DONE and its performance-validation
      pass has produced real measured numbers showing this work is actually needed
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic, `docs/plans/live_map_reconnection_epic.md` §B,
      and `docs/plans/live_map_scaling_roadmap.md`
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` — M1, a hard prerequisite (not a soft reference): this epic
  does not start, and should not even be broken into child tickets, until M1 ships and measures.
- `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` — M3, an independent sibling epic (also gated on M1, no
  dependency between M2 and M3 in either direction).

## Related Docs
- `docs/plans/live_map_scaling_roadmap.md` — the milestone sequencing this epic is M2 of
- `docs/plans/live_map_reconnection_epic.md` — §B is this epic's full design source, already written; §D
  documents the external-review correction to the dirty-rect justification this epic's scope reflects

## Related Stored Artifacts
None.

## Related Code Areas
- `frontend/src/components/GameCanvas.tsx`, `frontend/src/hooks/useCanvas.ts` — the files this epic
  modifies (and that M1 explicitly does not)
- `frontend/src/constants/colors.ts` — likely touched if the manifest-driven rendering fast-follow (noted
  but not scoped in M1) lands around the same time; not assumed here, flagged only

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until M1 is DONE and has produced real performance numbers. Revisit scope-item detail once that evidence
  exists; it may narrow, widen, or reprioritize what's written above.
- Real browser canvas/memory limits (Safari's tighter ~3-5 megapixel / ~384MB ceiling vs. Chrome/Firefox's
  much larger ones) were researched analytically this session, not measured against this project's actual
  target devices — worth a real confirmation pass once this epic is unblocked.
- **Forward connection to M1's phased-loading state machine** (`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`
  Scope item 8): once this epic's chunked terrain cache exists, the loading experience could naturally
  extend from "one binary ready/not-ready state" to genuinely progressive loading — showing a coarse view
  as nearby chunks arrive rather than waiting for the whole visible area. Not scoped here, just flagged so
  the connection isn't lost — M1's phased state machine is deliberately generic enough to accommodate a
  finer-grained "loading progress" state later without redesigning it now.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
