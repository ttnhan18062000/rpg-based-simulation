# Test Plan: Deterministic Scheduler Contract

## Objective
Finalize and pin the deterministic work selection behavior of the `DeterministicScheduler`. Prove that for any given `AuthoritativeState` and `GovernorPolicy`, the resulting work sequence is exact and stable.

## Automated Tests

### 1. Work Hierarchy Stress Test (`test_work_hierarchy_purity`)
- **Input**: A state containing entities (Critical), due periodic tasks, and work debt (Deferred).
- **Assertion**: Verifies that ALL Critical items appear before ANY Periodic items, and ALL Periodic items appear before ANY Deferred items.

### 2. Tie-Break Law Tests
- **Entity Actions**:
  - Test Case: Multiple entities with same readiness must be sorted by ID ASC.
  - Test Case: Entities with different readiness must be sorted by readiness DESC.
- **Periodic Tasks**:
  - Test Case: Multiple tasks due at the same tick must be sorted by subsystem ID ASC.
  - Test Case: Tasks with different due ticks must be sorted by due tick ASC.
- **Deferred Debt**:
  - Test Case: Multiple debts must be sorted by owner ID ASC.

### 3. Governor Policy Gating Tests
- **Input**: `GovernorPolicy(allow_non_authoritative_periodic=False)`.
- **Action**: Register a periodic task marked `is_authoritative=False`.
- **Assertion**: Verify it is NOT selected and is counted as "dropped."

### 4. Placeholder Guard (`test_no_placeholders_scheduler`)
- **Action**: Check if any `EXPECTED_FAIL` or `TODO` branches are reached in any test case.
- **Action**: Assert that `OPPORTUNISTIC` work always returns an empty set in Milestone A.

## Manual Verification
- Code review to ensure sorting keys (`lambda x: (key1, key2)`) exactly match the documents.
