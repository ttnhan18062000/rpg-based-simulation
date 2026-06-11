---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260410-PH1-STG-AUDIT
artifact_type: test_plan
tags: [ph1, stg, audit]
---

# Test Plan - Strategic Design Shift Audit

## Existing Tests
Run these to ensure the current implementation is stable:
- `pytest tests/core/test_strategy_models.py`
- `pytest tests/ai/test_strategic_biasing.py`
- `pytest tests/ai/test_strategic_uncertainty.py`

## New Tests
Add a specific safety test to verify that deep-copying an entity preserves the strategic state without sharing mutable references for the nested lists.

### Scenario: Deep Copy Isolation
1. Create an entity with a project in `MindAspect`.
2. Create a deep copy of the entity (e.g. via `entity.copy()` if available, or via Pydantic model copy).
3. Mutate the project list in the copy.
4. Verify the original entity's project list remains unchanged.

## Manual Verification
- Run a simulation tick and inspect an entity via the CLI to confirm they have directives and that updates are applied correctly.
