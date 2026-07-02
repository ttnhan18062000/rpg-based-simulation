---
ticket_id: TCK-20260623-FIX-KERNEL-PHASES
date: 2026-06-23
status: draft
---

# Test Plan: TCK-20260623-FIX-KERNEL-PHASES

## Scope

Tests covering the two root causes:
1. Kernel phase-contract source inspection (RC1)
2. `GroundItemState` / `ItemStack` type mismatch in race-condition tests (RC2)

## Pre-fix Baseline (Expected Failures)

Run before applying fixes to confirm test state:

```bash
python3 -m pytest \
  tests/integration/kernel/test_milestone_a_closure.py::test_final_kernel_law_compliance \
  tests/integration/kernel/test_race_conditions_v2.py \
  -q --tb=line
```

Expected: 1 failure (RC1) + 4 failures (RC2 cascade).

## Post-fix Verification

### RC1 — Kernel phase contract test

```bash
python3 -m pytest tests/integration/kernel/test_milestone_a_closure.py -q --tb=short
```

Expected after fix: all tests in the file pass.

### RC2 — Ground item index / ItemStack race condition tests

```bash
python3 -m pytest tests/integration/kernel/test_race_conditions_v2.py -q --tb=short
```

Expected after fix: all 4 tests pass (or fail only on unrelated assertions, not `AttributeError: 'ItemStack' object has no attribute 'position'`).

### Full kernel integration suite

```bash
python3 -m pytest tests/integration/kernel/ -q --tb=line -m "not slow"
```

### Event replay and authoritative outcome

```bash
python3 -m pytest \
  tests/integration/kernel/test_event_replay.py \
  tests/integration/kernel/test_authoritative_outcome_truth.py \
  -q --tb=short
```

### World index unit tests (if they exist)

```bash
python3 -m pytest tests/unit/ -k "world_index or ground_item" -q --tb=short 2>/dev/null || echo "No dedicated world_index unit tests found"
```

## Regression Guard

Ensure no previously-passing kernel tests regress:

```bash
python3 -m pytest tests/integration/kernel/test_determinism_suite.py tests/integration/kernel/test_seed_stability.py tests/integration/kernel/test_minimal_kernel.py tests/integration/kernel/test_substrate_freeze_m1.py -q --tb=short
```

## Out-of-Scope Test Commands (for tracking, not part of this ticket's pass criteria)

These tests are failing for independent reasons and should be tracked separately:

```bash
# Pipeline mutation boundary (independent bug)
python3 -m pytest tests/integration/pipeline/test_mutation_boundary.py -q --tb=line

# Movement pipeline (independent bug)
python3 -m pytest \
  tests/integration/pipeline/test_movement_micro_arena_position_swap.py \
  tests/unit/movement/test_position_swap.py \
  tests/unit/movement/test_tactical_movement.py \
  -q --tb=line

# Milestone B/C/D (independent bugs)
python3 -m pytest \
  tests/integration/kernel/test_milestone_b_closure.py \
  tests/integration/kernel/test_milestone_c_desimulation.py \
  tests/integration/kernel/test_milestone_d_closure.py \
  -q --tb=line
```
