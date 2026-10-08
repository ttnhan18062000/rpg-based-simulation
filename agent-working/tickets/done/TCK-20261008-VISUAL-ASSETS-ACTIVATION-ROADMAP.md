---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP
phase: done
date: 2026-10-08
tags: [architecture, planning, documentation]
---

# TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP

## Title
Record the activation roadmap for adopted art (the gate chain to icons in the live app) and park it; refresh the planner handoff snapshot

## Status
DONE

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
- [x] The roadmap section exists, every claim re-verified against the cited lines (or corrected), parked status explicit.
- [x] The missing per-icon safety class recorded as a known gap.
- [x] Planner handoff snapshot refreshed.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (done, PR #418)

## Related Docs
- docs/plans/visual-asset-management-runtime-integration/ (README, 06, 07), docs/assets/m0_discovery_result.md, m1_contract_register.md, m2_evidence_charter.md, pilot_charter_am6.md, surface_rehearsal_result.md, fallback_safety.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP/ (gate_map_2026-10-08.md, investigation.md with the citation corrections)

## Related Code Areas
- docs only

## Assumptions / Open Questions
- Parked by the owner until the RPG core lands; resuming, narrowing and any authorization are owner decisions not taken here.
- The planner's gate map had errors, corrected in `investigation.md`: wrong line citations and one false claim (icon keys without a class: they state class and text fallback as prose, only the registry field and a check are missing).

## Implementation Notes
- Section 'Status update 2026-10-08 (activation roadmap, parked)' added to the plan README before 'Status and authorization boundary': status table of M0-M7 and C01-C10, the 7-step chain with owner/engineering/evidence marks, what may be narrowed and what is forbidden, icon and HUD gaps. Every citation re-read at 4a2141df9.
- Known gap recorded in `docs/assets/fallback_safety.md` (class only as prose in the 36 icon key descriptions).
- Both handoff snapshots refreshed from the current handovers.

## Test Summary
- Docs only; `pytest tests/docs tests/static` run (see the commit report); knowledge index and registry regenerated.

## Files Changed
- docs/plans/visual-asset-management-runtime-integration/README.md, docs/assets/fallback_safety.md, docs/assets/session_handoff/{asset-planner,asset-implementer}.md, ticket and stored artifacts.

## Completion Summary
The parked activation roadmap is recorded in the plan with every citation re-verified (two line errors and one false claim corrected), the icon class gap is a recorded known gap, and the handoff snapshots are current. No gate moved; nothing is authorized.
