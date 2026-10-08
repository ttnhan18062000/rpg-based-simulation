---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP
phase: open
date: 2026-10-08
tags: [architecture, planning, documentation]
---

# TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP

## Title
Record the activation roadmap for adopted art (the gate chain to icons in the live app) and park it; refresh the planner handoff snapshot

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
After PR #418 (36 adopted icons, nothing wired) the owner asked to plan the activation path, read the planner's
gate map, and chose (blocking question, 2026-10-08) **"Record the map, park it"**: write the chain into the plan as the
activation roadmap, move no gate, and resume when the RPG core lands. The planner's investigation is in this ticket's
staging folder (`gate_map_2026-10-08.md`, with file:line citations to re-verify).

## Scope
- In `docs/plans/visual-asset-management-runtime-integration/README.md`, a dated "Status update 2026-10-08
  (activation roadmap, parked)" section: the current status of M0-M7 and C01-C10 (as a table), the shortest chain to icons
  in the live panels (7 steps, each marked owner decision / engineering / evidence run), what the owner MAY narrow and
  what the plan forbids, and the icon/HUD-specific gaps. State plainly: parked by the owner until the RPG core lands; no
  gate moved; nothing authorized.
- Record as a known gap (not fixed here): the 36 adopted icon keys have no declared fallback-safety class although
  `fallback_safety.md` rules 1-3 require one before adoption (register row W02.7 is the field). Say so in
  `fallback_safety.md` or the register, wherever the existing gaps live.
- Refresh `docs/assets/session_handoff/asset-planner.md` from `.claude/handover/asset-planner.md` (stale in #418) and the
  implementer snapshot.
- `make knowledge-index-update` after docs change.

## Out of Scope
- Moving any gate or result; any code (the W02.7/W03.1/W06.3 tickets are not filed); any owner decision on M0, narrowing, the charter or authorization.

## Acceptance Criteria
- [ ] The roadmap section exists, every claim re-verified against the cited lines (or corrected), parked status explicit.
- [ ] The missing per-icon safety class recorded as a known gap.
- [ ] Planner handoff snapshot refreshed.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (done, PR #418)

## Related Docs
- docs/plans/visual-asset-management-runtime-integration/ (README, 06, 07), docs/assets/m0_discovery_result.md, m1_contract_register.md, m2_evidence_charter.md, pilot_charter_am6.md, surface_rehearsal_result.md, fallback_safety.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP/gate_map_2026-10-08.md

## Related Code Areas
- docs only

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

