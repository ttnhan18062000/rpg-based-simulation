---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION

## Title
paired.py writes one run-ledger/v1 row per invocation (incl. STOP, REFUSED, KILLED), with per-arm wall_seconds and peak RSS (rpg child of T1)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
rpg child of testing's T1 TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (testing-planner-v1-followups 0ed157004). Testing owns tools/test_architecture/run_ledger.py; rpg owns tools/rpg_measure/** and writes the hook; testing reviews. Also closes the lead's finding (via architecture-planner): no wall time is kept per paired arm, so a feature-test cycle's cost cannot be answered from data (v1's 1b: refused base, then a 2.5 h re-run).

## Scope
Write through `tools/test_architecture/run_ledger.append_row` (after T1 lands), schema `run-ledger/v1`, all fields required (nullable marked):
- schema, invocation_id (uuid4), tool "paired", step (--step), base_sha, new_sha, worlds, seeds, ticks, started_at, ended_at (ISO tz-aware)
- outcome PASS | STOP | REFUSED | KILLED | ERROR; outcome_detail (nullable: STOP/refusal text, e.g. the NonAuditRunError message)
- rerun_of (nullable; from a new `--rerun-of` flag, never guessed)
- runs: [{arm: base|new|self, world, seed, wall_seconds, peak_rss_mb (nullable), cached: bool}]
- host: {name, nproc, mem_total_mb, python, platform}
KILLED: write a `started` row first (same invocation_id, outcome null, ended_at null); a started row with no end row reads as KILLED. A ledger write failure warns on stderr and never changes paired.py's exit code.

## Out of Scope
The ledger module and its summary command (testing). The gate harness hook (testing).

## Acceptance Criteria
- Every paired.py exit path writes exactly one end row (unit tests for PASS, STOP, REFUSED, ERROR; KILLED shown by a started row without end).
- wall_seconds per executed arm; cached arms marked cached with no wall time claimed.
- A ledger failure never changes the exit code (test).
- No change to measurement results (paired --neutral IDENTICAL on one step).

## Related Tickets
TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (T1, testing); TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (T2, testing).

## Related Docs
docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
tools/rpg_measure/paired.py; tools/rpg_measure/arm_child.py; tools/test_architecture/run_ledger.py (reader)

## Assumptions / Open Questions
Depends on T1 landing. Testing reviews.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
