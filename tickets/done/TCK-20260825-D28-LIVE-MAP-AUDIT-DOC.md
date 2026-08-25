---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260825-D28-LIVE-MAP-AUDIT-DOC
phase: open
date: 2026-08-25
tags: [audit, live-map, websocket, documentation]
---

# TCK-20260825-D28-LIVE-MAP-AUDIT-DOC

## Title
Add `docs/audits/D28_live_map_functional_correctness.md` -- the live map's first-ever audit pass

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Direct user instruction. Confirmed via direct inspection that neither `D26_visual_quality_integration.md`
(server-side batch/QA renderer only) nor `D27_frontend_hud_visual_design_quality.md` (HUD chrome
design quality only, explicitly disclaiming the live canvas in its own "the live-canvas gap"
section) covers whether the live map's real-time data + render pipeline actually *functions*. This
session found and fixed three independent, severe, real bugs
(`TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX`,
`TCK-20260825-METADATA-PROVIDER-NONBLOCKING-FALLBACK`,
`TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN`) that made the live map non-functional through its
own documented golden path -- none of them caught by any pre-existing test, because none of them
are unit-testable in isolation. This is exactly the kind of finding a dedicated audit dimension
exists to capture and prevent from silently regressing.

## Scope
- New `docs/audits/D28_live_map_functional_correctness.md`, mirroring `D26`'s format (Summary,
  Dimension Profile, Related dimensions, Findings Summary table, Related Documents) since this is a
  completed audit pass with real findings, not a not-yet-run placeholder like `D27`.
- Register a new `live-map` tag (subsystem-topic) -- confirmed via registry check that no existing
  tag covers this: `rendering` is explicitly server-side-only, `hud` is explicitly chrome-only,
  `websocket` is narrower (transport layer only).
- Document all 7 findings (F1-F7): the 3 bugs fixed this session (F1-F3 from
  `LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX`), the root-cause terrain bug (F4), the new verification
  tooling (F5), and the two disclosed-open items (F6 TPS throughput inconclusive, F7
  rendering-performance/interest-management epics not started).
- A "Why None of This Was Caught by Existing Tests" section -- the generalizable lesson, not just a
  bug list, since that is this dimension's real Interest-rating justification.

## Out of Scope
- Fixing F6 or F7 -- both explicitly disclosed as open, out of this documentation ticket's own
  scope (F6 already has its own re-check ticket; F7's epics already exist, not started).
- Registering `D28` in `docs/audits/audit_dimensions.md`'s master index -- matching the precedent
  D19-D27 already set (that index is stale and out of scope to repair here, per D26's own F3).

## Acceptance Criteria
- [x] `D28_live_map_functional_correctness.md` created, mirroring `D26`'s completed-audit format
- [x] `live-map` tag registered before use
- [x] All 7 findings documented with real, cited evidence (ticket IDs, real numbers), not vague
      claims
- [x] Frontmatter validates

## Related Tickets
- TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX (F1, F2, F3)
- TCK-20260825-METADATA-PROVIDER-NONBLOCKING-FALLBACK (F3)
- TCK-20260825-METADATA-API-BACKEND-MISSING (the still-open real fix behind F3)
- TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN (F4)
- TCK-20260825-LIVE-VERIFICATION-TOOLING (F5)
- TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK (F6)
- TCK-20260825-D26-VISUAL-QUALITY-AUDIT-REFRESH (sibling ticket, same session, the visual-quality
  counterpart)

## Related Docs
- docs/audits/D28_live_map_functional_correctness.md (new)
- docs/audits/D26_visual_quality_integration.md, D27_frontend_hud_visual_design_quality.md (cited
  as siblings, explicitly not overlapping)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
None -- documentation only.

## Assumptions / Open Questions
None.

## Implementation Notes
Modeled on `D26`'s structure rather than `D27`'s, since this is a completed audit pass with real
findings (matching `D26`'s `status: historical`), not a not-yet-scheduled placeholder (`D27`'s
`status: active`, `State: none`).

## Test Summary
Documentation-only change. `tools/validate_frontmatter.py docs/audits/D28_live_map_functional_correctness.md`
passes. Every finding's underlying evidence (bug fixes, real numbers, tooling) was independently
verified live by the cited tickets in the same session, not re-derived here.

## Files Changed
- docs/audits/D28_live_map_functional_correctness.md (new)
- registries/tag_registry.jsonl (`live-map` tag added)

## Completion Summary
The live map now has its own audit dimension distinct from D26 (server rendering QA) and D27 (HUD
design), documenting that its real-time functional pipeline genuinely works end-to-end for the
first time in this feature's history, plus the two remaining disclosed-open items.
