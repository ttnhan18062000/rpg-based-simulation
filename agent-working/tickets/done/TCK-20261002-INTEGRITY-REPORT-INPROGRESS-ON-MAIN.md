---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261002-INTEGRITY-REPORT-INPROGRESS-ON-MAIN
phase: done
date: 2026-10-02
tags: [agent-monitoring]
---

# TCK-20261002-INTEGRITY-REPORT-INPROGRESS-ON-MAIN

## Title
Integrity report flags tickets still under `tickets/inprogress/` on the merged ref

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
PR #276 merged its src change while its four tickets stayed in `tickets/inprogress/` (Finalize never ran). No PR-time
render check can catch that; only a look at the merged ref can. Raised by rpg-feature-planning; draft from
`agent-working-design` (`.claude/handover/drafts/integrity-inprogress-check/`).

## Scope
- `tools/agent-monitoring/main_integrity_report.py`: new `inprogress` check, one finding per ticket file under
  `tickets/inprogress/` at the ref (`.gitkeep` ignored, `--since-date` honoured), report-only. Read from file
  locations, not commit subjects (a squash merge leaves only the PR title).
- One sentence in `docs/agent-monitoring/README.md` and a clause in the direction doc's integrity row.

## Out of Scope
- Closing the four #276 tickets (owned by rpg-implementer) and deciding on
  `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` (its owner says if it is in flight or never finalized).

## Acceptance Criteria
- A ticket left under `tickets/inprogress/` on the ref is reported; a done ticket and `.gitkeep` are not; a clean ref reports nothing.
- The new test fails on the unpatched module.

## Related Tickets
- TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT

## Related Docs
- docs/agent-monitoring/README.md
- docs/plans/agent_infrastructure/agent_working_direction.md

## Related Stored Artifacts
none (hotfix)

## Related Code Areas
- tools/agent-monitoring/main_integrity_report.py
- tests/tools/test_main_integrity_report.py

## Assumptions / Open Questions
- On `origin/main` 78ea7c465 it reports 5 tickets: the four from #276 plus
  `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`; the report total goes 263 to 268.

## Implementation Notes
Applied design's `mir.patch` verbatim (2 files, +34), plus the two doc edits it specified.

## Test Summary
`tests/tools/test_main_integrity_report.py`: 10 passed. Negative control (design, throwaway worktree): the new test fails on the unpatched module.

## Files Changed
- tools/agent-monitoring/main_integrity_report.py
- tests/tools/test_main_integrity_report.py
- docs/agent-monitoring/README.md
- docs/plans/agent_infrastructure/agent_working_direction.md

## Completion Summary
Merged work left in `tickets/inprogress/` now shows up in the post-merge integrity report.
