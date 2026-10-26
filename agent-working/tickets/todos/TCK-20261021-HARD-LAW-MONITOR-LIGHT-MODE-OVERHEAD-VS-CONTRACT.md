---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261021-HARD-LAW-MONITOR-LIGHT-MODE-OVERHEAD-VS-CONTRACT
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-HARD-LAW-MONITOR-LIGHT-MODE-OVERHEAD-VS-CONTRACT

## Title
The hard-law monitor's LIGHT mode costs about 27-36% overhead against the <1% target in performance_contract.md §4.2, and its test threshold was relaxed to a 60% soft warning

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Lead-planner-u24's read-only pass on origin/main (2026-10-21): tests/perf/test_hard_law_monitor_overhead.py measures about 27-36% LIGHT-mode overhead (500 entities, about 13 ms tick). performance_contract.md §4.2 targets under 1%, and the test threshold was relaxed to 60% as a soft warning. Either the contract or the monitor is wrong. After v1.

## Scope
- Measure on the quiet host per performance_contract.md (tripwire rules: max(5 ms, 1.40×)).
- Then either reduce the monitor's LIGHT-mode cost, or have the owner restate the §4.2 target with a reason.
- Never just raise the test threshold.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The measured overhead and the contract agree, either by a fix or by a ruled contract change.
- The test asserts the real target, not a soft warning.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- tests/perf/test_hard_law_monitor_overhead.py, docs/engine/performance_contract.md §4.2, the hard-law monitor in src

## Assumptions / Open Questions
- Lead-planner-u24 reported this; it has not been re-verified here yet.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
