---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT

## Title
Four tests fail only inside a wide scoped run and pass alone, on the v1 tree too (order-dependent state leak)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by rpg-implementer (Lane A) during HUNGER step B's local scoped run (2026-10-23): 9030 passed, 7 failed. Four of the failures (the authoritative_outcome_truth, envelope_violations, harness_contract and resilience_recovery tests) pass when run alone, on both the step B tree and the v1 base tree 341f700d0. So they are order-dependent in a wide run, not caused by step B. CI shards evidently don't hit the order.

## Scope
1. Reproduce: the same scoped command on 341f700d0; bisect the collection order (pytest -p no:randomly, then --lf with a growing prefix) to find the test that leaks state.
2. Fix the leak (fixture teardown, a monkeypatch left in place, a module-level cache) at its source. Never by reordering or skipping.

## Out of Scope
The step B changes themselves.

## Acceptance Criteria
- The four tests pass in the wide scoped run on main; the leaking test is named and fixed; a guard test exists if the leak class allows one.

## Related Tickets
TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (where it was seen).

## Related Docs
docs/testing/test_taxonomy.md

## Related Stored Artifacts

## Related Code Areas
tests/ (the four named tests and their fixtures)

## Assumptions / Open Questions
- Ownership: if the leak is in tests/architecture/**, route to testing-planner.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
