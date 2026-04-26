# Test Plan: Resource-Safe Engine Milestone 4

## Purpose
Verify the deterministic work selection, work classification, and bounded debt handling of the Milestone 4 scheduler.

## Test Areas

### 1. Deterministic Scheduler (`tests/engine/test_scheduler_contract.py`)
- **Goal**: Verify stable work selection.
- **Tests**:
  - `test_readiness_selection`: Periodic/Entity work is only selected if due.
  - `test_tie_break_order`: Multiple entities at same readiness/priority are sorted by ID.
  - `test_repeatable_selection`: Multiple ticks produce identical work chains across runs.

### 2. Work Classes (`tests/engine/test_work_classes.py`)
- **Goal**: Verify priority and subordination.
- **Tests**:
  - `test_priority_enforcement`: Critical work always executes before Opportunistic.
  - `test_periodic_cadence`: Verify a task with cadence=10 executes exactly on ticks 10, 20, 30.
  - `test_opportunistic_bypass`: Verify that optional work doesn't affect authoritative state.

### 3. Bounded Work Debt (`tests/engine/test_deferred_work_debt.py`)
- **Goal**: Verify that postponed work is bounded.
- **Tests**:
  - `test_deferred_accumulation`: Add work while "busy", verify it goes to the deferred queue.
  - `test_deferred_drain`: Next tick, verify deferred work is processed first.
  - `test_debt_limit_reject`: Verify `REJECT` policy if too much work is deferred.

## Success Criteria
- 100% test pass.
- No semantic drift (same seed/input => same outcome).
