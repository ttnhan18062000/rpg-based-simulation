---
status: open
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-STAT-FORMULAS
phase: open
date: 2026-06-23
tags: [test-repair, stats, progression, optimization, parity, P1]
---

# TCK-20260623-FIX-STAT-FORMULAS

## Title
Reconcile stat recalculation + optimization parity divergence (~7 failures)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Stat recalculation formulas or attribute injection changed, producing values that diverge
from test expectations. The same numeric mismatch appears across unit and integration
optimization tests, confirming a shared root cause.

**Confirmed error patterns:**
```
test_rpg_math.py:              assert 8 == 23       (stat recalculation — large delta)
test_rpg_advancement.py:       assert 9.5 == 11.9   (equipment stat injection into move cost)
test_apply_plan_parity.py:     assert (10.0, 10.0) == (10.0, 11.0)  (optimization plan parity)
test_component_patch_apply_parity.py: assert (10.0, 10.0) == (10.0, 11.0)  (component patch)
test_lifecycle.py:             assert None is not None  (near-death hardening — value missing)
test_cache_memory_bounds.py:   assert None is not None  (cache sweep returns None)
test_profile_specific_behavior.py: assert None is not None (profile behavior returns None)
```

The `(10.0, 10.0) == (10.0, 11.0)` pattern in optimization tests suggests one stat component
is off by exactly 1.0 — likely the same stat whose formula changed in `test_rpg_math`
(`assert 8 == 23` is a large delta, suggesting a multiplier or additive term changed).

Related to D17 finding: `docs/mechanics/01_entity_anatomy.md` biological thresholds are
documented incorrectly vs. source. Stat formula divergence may stem from the same code-doc
gap where the code was updated but tests still expect old values.

## Scope
- Identify which stat formula changed (start with `src/entities/` stat recalculation logic)
- Determine if the formula change was intentional (balance decision) or an accidental regression
- If intentional: update test assertions to match new formula AND update `docs/mechanics/01_entity_anatomy.md`
  AND add/update parity ledger entries in `docs/parity_ledger/progression.yaml`
- If regression: restore the formula and verify it matches the Mechanics Bible
- Fix the `assert None is not None` failures — identify what object is unexpectedly None
  (likely a stat component or cache result that is now returning None after formula change)

## Out of Scope
- Balance tuning decisions (this ticket fixes the test-code divergence, not the balance)
- Progression system logic changes beyond the formula alignment

## Acceptance Criteria
- `tests/unit/core/test_rpg_math.py::test_stat_recalculation` passes
- `tests/unit/progression/test_rpg_advancement.py::test_equipment_stat_injection_move_cost` passes
- `tests/unit/progression/test_lifecycle.py::test_near_death_hardening_logic` passes
- `tests/integration/optimization/test_apply_plan_parity.py` passes
- `tests/integration/optimization/test_component_patch_apply_parity.py` passes
- `tests/integration/optimization/test_cache_memory_bounds.py` passes
- `tests/integration/optimization/test_profile_specific_behavior.py` — both tests pass
- `docs/mechanics/01_entity_anatomy.md` updated if formula change is intentional
- Parity ledger entry added/updated in `docs/parity_ledger/progression.yaml`

## Related Tickets
- D17 doc currency — `docs/mechanics/01_entity_anatomy.md` (biological thresholds wrong)
- TCK-20260623-FIX-KERNEL-PHASES — phase skip parity may resolve as cascade of kernel fix

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` (stat definitions, should be authoritative)
- `docs/parity_ledger/progression.yaml`
- `docs/audits/D10_test_coverage.md` (D17 connection)

## Related Code Areas
- `src/entities/` (stat recalculation logic)
- `src/domains/adventure/scoring.py` or `src/engine/` (stat injection into move cost)
- `src/engine/optimization/` (apply plan, component patch, cache, profile)
- `tests/unit/core/test_rpg_math.py`
- `tests/unit/progression/`
- `tests/integration/optimization/`

## Assumptions / Open Questions
- Was the stat formula intentionally changed (e.g. as part of E12A balance measurement)?
- What is the `assert 8 == 23` test actually checking? (8 is old, 23 is current — very large delta suggests a different formula branch, not just a constant change)
- Are `cache_memory_bounds` and `profile_specific_behavior` returning None because of the stat
  formula change, or a separate initialization failure?

## Implementation Notes
Investigation order:
1. `graphify query "stat recalculation entity attributes"` to find the stat engine
2. Read `test_rpg_math.py` to see exactly what formula it tests
3. Compare with `docs/mechanics/01_entity_anatomy.md` formula
4. Trace the `(10.0, 11.0)` stat delta to find which component changed
5. Check if None returns in optimization tests are the same root (stat init failure)

## Test Summary
Run: `pytest tests/unit/core/test_rpg_math.py tests/unit/progression/ tests/integration/optimization/ -m "not slow" --tb=short`

## Files Changed
- `src/engine/replay_manager.py` — `pressure_report()`: honor `budget` param; `budget=None` uses DEFAULT_REPLAY_BUDGET; `budget.max_inflight_chunks=None` means unlimited
- `src/engine/kernel.py` — `_phase_advancement()`: snapshot `self._rng.get_state()` into `StateUpdate.rng_checkpoint` before `apply_generation`
- `tests/unit/core/test_p1_semantic_hardening.py` — `test_stamina_drain`: replace `TaskUpdate` injection with `TaskComponent`
- `tests/unit/core/test_hardcoded_regression_guard.py` — add `mode=RuntimeContentMode.LEGACY_FALLBACK` to `seed_phase1_content` call
- `tests/unit/core/test_graceful_shutdown.py` — configure `mock_replay.replay_metrics.return_value` with numeric dict
- `tests/unit/engine/test_replay_backpressure.py` — 3 `TestPressureReport` tests updated to pass explicit `SubsystemBudget` to `pressure_report()`

## Completion Summary
Fixed 8 test failures (actual D10 failures; the stat formula assertions cited in the ticket already passed). Root causes: 1 missing TaskComponent injection, 1 LEGACY_FALLBACK mode guard, 3 ignored budget param in pressure_report(), 2 missing rng_checkpoint writes in kernel, 1 MagicMock vs int comparison. 3 production bugs + 4 test bugs fixed. All 28 targeted tests pass; no regressions introduced.
