---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
phase: open
date: 2026-09-02
tags: [content, determinism]
---

# TCK-20260902-PLACE-MIGRATION-RECALIBRATION

## Title
state_hash-first recalibration and grade triage across all 21 worlds

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Child 5/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, runs alongside/after
`TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT` on a per-world basis. Every `world_compile_report.json`
already carries a `state_hash` field — recompile each world under the new schema and diff `state_hash`
against the committed one first. An unchanged hash proves a lossless migration for that world with no
SimQ grade run needed at all. Only for worlds whose hash *does* change does a full `grade_anchors.json`
re-run and manual grade-shift triage apply (real regression vs. compile-shape noise). Per the plan doc's
own budget note: `grade_anchors.json`'s tolerance (±1 letter-grade band, `max(0.05, 0.20×score)`) across
all 84 committed `run_keys` will very likely trip on a structural compile-shape change at this scale even
with zero real gameplay regression — this is budgeted as a genuine per-world triage pass, not a single
batch diff.

## Scope
- For each of the 21 worlds (as they land via the rollout ticket): diff recompiled `state_hash` against
  the committed baseline.
- For any world whose hash changed: run `grade_anchors.json` and manually triage each grade shift as
  real regression vs. compile-shape noise, recording the triage note per this ticket's Implementation
  Notes.
- Record a final summary: how many of 21 worlds had unchanged hashes (lossless migration), how many
  changed and were triaged as noise, how many (if any) surfaced a real regression requiring its own
  follow-up hotfix ticket.

## Out of Scope
- Fixing any real regression surfaced during triage — that gets its own hotfix ticket, referencing this
  one as the source of the finding.

## Acceptance Criteria
- [ ] All 21 worlds have gone through the `state_hash`-first recalibration procedure.
- [ ] Every world whose hash changed has a recorded triage note (real regression vs. compile-shape
      noise) — none deferred to a future audit.
- [ ] Any real regression found is filed as its own ticket, not silently absorbed into this one's scope.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT (runs alongside this ticket)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/simulation_quality/` (grade_anchors.json tolerance mechanics)

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-PLACE-MIGRATION-RECALIBRATION/`)

## Related Code Areas
- `world_compile_report.json` fixtures (per world)
- `grade_anchors.json`

## Assumptions / Open Questions
None beyond what the parent epic already tracks.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
