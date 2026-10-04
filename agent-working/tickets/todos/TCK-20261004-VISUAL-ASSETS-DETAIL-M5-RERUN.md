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
Rerun the M5 checks the detail variants affect, record the results, close the epic

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Last child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`. With `plain` / `bush` / `tree` released
(`pilot/rc-0002`), rerun only the M5 checks that variants can change, against the predeclared criteria in
`docs/assets/pilot_terrain_m5_criteria.md`, and record them.

## Scope
- Crowded scene with mixed variants (`W03`-style): the user's recorded review, by blocking question.
- Colour-vision check (`W05`) on all three tiles and on the mixed scene: forest still reads as forest next to its
  neighbours; still INCONCLUSIVE if the criteria cannot be met, never reworded.
- Fallback per variant: each missing slot falls back to `plain`, a missing `plain` to the role fallback (harness run).
- Rollback drill against rc-0001 (old release, new client and the reverse).
- Record in `docs/assets/pilot_terrain_m5_results.md` (dated section) and the overall verdict line; a note in the
  charter draft only if a gate's status changes. Gates are never reworded to pass.
- Close the epic: tickets to `done/`, `SEQUENCE.md` kept, folder moved when all are done.

## Out of Scope
- Charter signing, AM-M6 authorization (the user's). Checks variants cannot affect (not rerun; say so).

## Acceptance Criteria
- [ ] Each affected check rerun and recorded with its result; unaffected checks listed as not rerun with the reason.
- [ ] User review of the mixed scene recorded (their own answer).
- [ ] Overall M5 verdict stated as measured (it may stay INCONCLUSIVE).

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md, docs/assets/pilot_terrain_m5_results.md, docs/assets/pilot_charter_am6.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER/

## Related Code Areas
- frontend/src/visualAssets/ (harness only)

## Assumptions / Open Questions
- None.

## Implementation Notes
DEFERRED by the user, 2026-10-04 (blocking question): rerun M5 once a full draft set has been reviewed and adopted
(`adopt-set`), so one review covers a whole map. Moved out of the detail-variants batch; re-scope against the adopted set
before starting.

## Test Summary

## Files Changed

## Completion Summary
