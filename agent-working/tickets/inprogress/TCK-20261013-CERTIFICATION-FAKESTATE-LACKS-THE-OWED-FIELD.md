---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261013-CERTIFICATION-FAKESTATE-LACKS-THE-OWED-FIELD
phase: implement
date: 2026-10-13
tags: []
---

# TCK-20261013-CERTIFICATION-FAKESTATE-LACKS-THE-OWED-FIELD

## Title
The certification FakeState mirrors the new AuthoritativeState.owed field.

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Batch 3 (EXCH-02, ruling 61) added AuthoritativeState.owed and the canonical hasher reads it (conditionally, only when non-empty, through one helper). tests/certification/test_evidence_levels.py::FakeState mirrors the state for the hasher and lacked it: 4 test_evidence_levels tests and test_resilience_recovery::test_harness_catches_failed_recovery failed with "'FakeState' object has no attribute 'owed'" (found by Lane C on rpg-fold-next).

## Scope
Add owed: dict = {} to the FakeState (the fake mirrors the state; production code is not made to tolerate a missing field).

## Out of Scope
Production code.

## Acceptance Criteria
tests/certification/test_evidence_levels.py and test_resilience_recovery.py pass.

## Related Tickets
EXCH-02 batch 3 treasury tickets (closed).

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
tests/certification/test_evidence_levels.py

## Assumptions / Open Questions
None.

## Implementation Notes
One line in the fake.

## Test Summary
tests/certification/test_evidence_levels.py + test_resilience_recovery.py: 15 passed.

## Files Changed
tests/certification/test_evidence_levels.py

## Completion Summary
Pending PR.
