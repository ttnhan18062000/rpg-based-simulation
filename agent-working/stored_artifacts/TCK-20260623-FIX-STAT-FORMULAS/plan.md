# Plan: TCK-20260623-FIX-STAT-FORMULAS

**Date:** 2026-06-24  
**Scope:** Fix 8 actual test failures (not stat formula changes — the D10 audit patterns already pass)

---

## Root Causes and Fixes

| # | File | Change | Type |
|---|---|---|---|
| 1 | `tests/unit/core/test_p1_semantic_hardening.py:257-258` | Replace `TaskUpdate` injection with `TaskComponent` | Test bug |
| 2 | `tests/unit/core/test_hardcoded_regression_guard.py:48` | Add `mode=RuntimeContentMode.LEGACY_FALLBACK` to `seed_phase1_content` call | Test bug |
| 3 | `src/engine/replay_manager.py` `pressure_report()` | Honor `budget` parameter when `budget.max_inflight_chunks` is not None | Production bug |
| 4 | `src/engine/kernel.py` `_phase_advancement` | Snapshot `self._rng.get_state()` into `StateUpdate.rng_checkpoint` | Production bug |
| 5 | `tests/unit/core/test_graceful_shutdown.py:44-48` | Configure `mock_replay.replay_metrics.return_value` with numeric dict | Test bug |

## Sequence

1. Fix production bugs first (replay_manager.py, kernel.py) — these affect multiple tests
2. Fix test bugs (3 files)
3. Run scoped tests to verify all 8 pass

## Architecture Notes

- `pressure_report(budget)` change: use `budget.max_inflight_chunks` only when provided and > 0; fall back to `self._max_pending_flushes` otherwise. Zero risk to existing behavior.
- `rng_checkpoint` change: `replace(update, rng_checkpoint=self._rng.get_state())` before `apply_generation`. The field already exists on `StateUpdate` (src/core/updates.py:899). This is an additive fix — no existing paths depended on it being None.
- No parity ledger changes required: these are all test-infrastructure bugs or missing wiring, not behavioral formula changes.
