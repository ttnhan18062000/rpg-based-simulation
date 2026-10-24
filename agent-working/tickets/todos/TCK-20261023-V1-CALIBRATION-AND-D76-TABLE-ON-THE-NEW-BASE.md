---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE

## Title
Regenerate the calibration on v1 (`make evaluate-full` plus its run_determinism sidecar) for testing's SimQ re-anchor, and point the D76 cumulative table at the v1 base

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
TCK-20261019-RECORD-BASELINE-V1 closed without its scope item 4. That item regenerates the calibration with `make evaluate-full` and its run_determinism sidecar on v1 (e8df8b96d) so testing can re-anchor SimQ. The record also left the D76 cumulative table pointing at the old base. The record PR says both are "not in this PR". This ticket carries them.

## Scope
1. `make evaluate-full` on v1 (e8df8b96d), with the run_determinism sidecar, on a quiet host (one heavy process).
2. Hand the calibration to testing-planner for the SimQ re-anchor (testing owns the anchors).
3. Re-point the D76 cumulative table at the v1 base (e8df8b96d). Later steps measure against v1.

## Out of Scope
SimQ anchor values (testing). Any simulation change.

## Acceptance Criteria
- Calibration regenerated on e8df8b96d with the sidecar committed; testing notified with the paths.
- The D76 table names v1 (e8df8b96d) as its base.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1.

## Related Docs
docs/plans/systemic_world/v1_disclosure.md; docs/plans/rpg_design_roadmap/ (12.3).

## Related Stored Artifacts

## Related Code Areas
Makefile (evaluate-full); src/observability/reporting/run_determinism.py.

## Assumptions / Open Questions
- The location of the D76 table is to be confirmed (owner memo D76 row / roadmap).
- DUE 2026-10-30 (lead, #725 review): testing's SimQ re-anchor on the v1 sha needs this calibration before 2026-10-31.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
