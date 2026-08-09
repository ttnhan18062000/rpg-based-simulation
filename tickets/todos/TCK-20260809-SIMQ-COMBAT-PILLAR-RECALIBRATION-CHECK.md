---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK
phase: open
date: 2026-08-09
tags: [simulation-quality, combat]
---

# TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK

## Title
Re-run real SimQ COMBAT pillar calibration against `dungeon_crawl`/`urban_political` now that
identity-resolution, pursuit-tracking, and 2 scorer-emission gaps have all been fixed this
session, and check whether `grade_anchors.json` needs recalibrating

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
This session shipped 4 real fixes affecting COMBAT-pillar-scored behavior:
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (identity resolution — real hostile pairs now
detected), `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (live target tracking — pursuit
converges), `TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX` (`combat_resolved`, +3, now emits),
`TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX` (`tactical_variety`, +1/modifier, now
emits). The COMBAT pillar previously graded C on both worlds (documented earlier this session,
before any of these fixes), when combat was effectively inert. A real, fresh calibration run
using `tools/calibrate_simq.py` (the same real tool this session used throughout for verification)
would show whether the grade has genuinely moved, and whether `config/simulation_quality/
grade_anchors.json`'s own existing anchor bands still reflect a meaningful comparison baseline
or need recalibrating against the new, real post-fix behavior.

This is a status-check/verification ticket, not presumed to require a code change — the real
question is whether the grade moved and whether the anchors are stale, not "make the grade
higher."

## Scope
1. Run `tools/calibrate_simq.py` against `dungeon_crawl`/`urban_political` (matching this
   session's own established real-corpus methodology — real seeds, real tick counts, corpus-
   default feature flags) and record the real, current COMBAT pillar grade/score for each.
2. Compare against the pre-session baseline (C grade, documented in this session's own earlier
   turns) and against `grade_anchors.json`'s own existing bands for these 2 worlds.
3. If the real score has moved meaningfully outside the existing anchor band: determine whether
   this reflects genuine, durable improvement (recalibrate the anchor) or run-to-run noise (the
   corpus's own real combat volume is still low and timing-variable, confirmed repeatedly this
   session — a single run may not be representative).
4. Document the real, current state — no forced conclusion either way.

## Out of Scope
- Any further code fix to combat mechanics — this ticket is a verification/status check only.
- Recalibrating any other pillar's anchors — COMBAT only, scoped to this session's own real
  changes.

## Acceptance Criteria
- [ ] A real, fresh SimQ calibration run's COMBAT pillar grade/score is recorded for both worlds
- [ ] The result is compared honestly against the pre-session baseline and `grade_anchors.json`
- [ ] A concrete recommendation is produced (recalibrate anchors, or leave as-is with reasoning
      — e.g. run-to-run noise, insufficient sample size)

## Related Tickets
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE, TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE,
  TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX, TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
  (DONE, same session — the 4 fixes this ticket checks the aggregate real-world effect of)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT
- `config/simulation_quality/grade_anchors.json`

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tools/calibrate_simq.py` (the real calibration tool)
- `config/simulation_quality/grade_anchors.json` (potentially updated if recalibration is
  warranted)

## Assumptions / Open Questions
- Whether a single fresh run is a sufficient sample given this session's own repeated
  observations of real run-to-run combat-volume variance — left to Investigate/Scope judgment;
  multiple runs may be warranted before drawing a conclusion.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
