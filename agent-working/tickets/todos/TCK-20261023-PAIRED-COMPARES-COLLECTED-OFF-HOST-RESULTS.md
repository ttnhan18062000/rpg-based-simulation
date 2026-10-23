---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS

## Title
paired.py can compare arm results collected from the off-host workflow instead of running them (rpg child of T2)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
rpg child of testing's T2 TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (0ed157004). Testing owns the workflow_dispatch matrix over (world, seed) that runs BOTH arms per job through the unchanged arm_child.py (PYTHONHASHSEED=0) and records runner identity. rpg writes the paired.py option that feeds the aggregate job; testing reviews.

## Scope
1. A `--collected DIR` (name to settle in review) mode: read the per-(world, seed) arm results from the workflow artifacts instead of running arm_child.
2. Unchanged: require_host_independent_runs, --legacy-base, the STOP rule and the report.
3. Refuse arms whose runner-identity records differ in Python version or OS; refuse a (world, seed) whose base and new did not come from the same job.

## Out of Scope
The workflow itself (testing). Any change to arm_child.py.

## Acceptance Criteria
- AC1 equality proof on a real, already-measured step: the (a1) step e6a6a3e10 -> 3b0722bdb (seeds 42-46, 3 worlds; local result: 0 of 15 pairs differ in any field, PR #720). Off-host collected results must reproduce the local report byte for byte (same final hashes, fates, counters).
- Refusal tests for mixed runner identity and split jobs.

## Related Tickets
TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (T1, testing); TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (T2, testing).

## Related Docs
docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
tools/rpg_measure/paired.py

## Assumptions / Open Questions
Depends on T2's workflow. Testing reviews.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
