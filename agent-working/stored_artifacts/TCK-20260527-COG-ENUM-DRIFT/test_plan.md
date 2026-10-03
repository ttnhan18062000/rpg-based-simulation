---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-ENUM-DRIFT
artifact_type: test_plan
tags: [cog, enum, drift]
---

# Test Plan: TCK-20260527-COG-ENUM-DRIFT

We will add a new unit test suite: `tests/unit/strategic/test_enum_drift.py` covering:
- Every registered goal in `GoalRegistry` is an instance of `GoalKind`.
- Invalid string or type rejection in `GoalRegistry.register`.
- Strategic event creation validates kind values correctly.
- Test that loading state with invalid kinds raises validation errors.
