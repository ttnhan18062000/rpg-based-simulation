---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN
phase: open
date: 2026-10-04
tags: [architecture, testing, live-map]
---

# TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

## Title
Rerun M5 against the adopted terrain-v1 set (whole map, forest variants mixed), record the results, close the batch

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Originally the last child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS` (rerun only the M5 checks the
forest variants affect). DEFERRED by the user on 2026-10-04 until a full draft set is reviewed and adopted with
`adopt-set`, so one review covers a whole map. Moved on 2026-10-05 into `visual-asset-terrain-set-review` as its last
child and re-scoped against the adopted `terrain-v1` set. Starts only after the user has run `adopt-set` (see
`SEQUENCE.md`); re-check this ticket against what landed before starting.

## Scope
- Release: decide against what landed whether the rerun needs a release holding the adopted set (proposed
  `pilot/rc-0004`). If yes, ask the user before assembling it; rc-0001..rc-0003 stay as history.
- `W03` crowded scene: the whole-map layout predeclared by `TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE`,
  image and flat-control canvases at device pixel ratio 1 and 2; the user's review by blocking question, answers recorded
  verbatim.
- `W05` colour vision: the committed set rule on the adopted set (result as measured), and the pilot's forest rule rerun
  unchanged on plain/bush/tree. Still INCONCLUSIVE or FAIL if that is what it measures, never reworded.
- Fallback: each missing forest variant falls back to `plain`, a missing `plain` to the role fallback, and each new
  terrain key missing falls back to its flat fill (harness run).
- Rollback drill against the previous release (old release with new client and the reverse).
- Record in `docs/assets/pilot_terrain_m5_results.md` (new dated section) with the overall verdict line; a note in the
  charter draft only if a gate's status changes. Gates are never reworded to pass.
- Unaffected checks listed as not rerun, with the reason.
- Close the batch: refresh `docs/assets/session_handoff/` from both asset handover notes; tickets to `done/`, the folder
  moved with `SEQUENCE.md`.

## Out of Scope
- Charter signing, AM-M6 authorization (the user's). Adoption (the user did it before this ticket).
- Redrawing (child 2); changing any rule or criterion.

## Acceptance Criteria
- [ ] Each affected check rerun on the adopted set and recorded with its result; unaffected checks listed with the reason.
- [ ] User review of the whole-map scene recorded (their own answers).
- [ ] Overall M5 verdict stated as measured (it may stay INCONCLUSIVE).
- [ ] Handoff snapshots refreshed; batch folder in `done/`.

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE,
  TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW, TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (former
  parent, done), TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md, docs/assets/pilot_terrain_m5_results.md, docs/assets/pilot_charter_am6.md,
  docs/assets/session_handoff/

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER/

## Related Code Areas
- frontend/src/visualAssets/ (harness only), visual_assets/catalog/ (release, only if the user approves one)

## Assumptions / Open Questions
- Whether a new release is needed (asked of the user if yes).

## Implementation Notes
DEFERRED by the user, 2026-10-04 (blocking question): rerun M5 once a full draft set has been reviewed and adopted
(`adopt-set`), so one review covers a whole map. Moved out of the detail-variants batch.
Re-scoped 2026-10-05 by asset-planner after the user chose "fix the set, then rerun" (blocking question): moved into
`visual-asset-terrain-set-review`, scope widened from forest variants to the adopted whole set.

## Test Summary

## Files Changed

## Completion Summary
