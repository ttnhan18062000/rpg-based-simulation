---
ticket_id: TCK-20260614-REPLAY-BACKPRESSURE
date: 2026-06-14
---

# Test Plan: TCK-20260614-REPLAY-BACKPRESSURE

File: `tests/unit/engine/test_replay_backpressure.py`

| # | Test | Coverage |
|---|------|----------|
| 1 | `test_inflight_count_starts_at_zero` | Initial state |
| 2 | `test_inflight_count_increments_on_submit` | Increment on async submit |
| 3 | `test_inflight_count_decrements_on_completion` | Decrement via callback |
| 4 | `test_on_persist_done_decrements` | Direct callback decrement |
| 5 | `test_on_persist_done_clamps_at_zero` | Underflow protection |
| 6 | `test_pressure_ok_below_80pct` | OK state threshold |
| 7 | `test_pressure_warn_above_80pct` | WARN state threshold |
| 8 | `test_pressure_degraded_at_limit` | DEGRADED at 100% |
| 9 | `test_pressure_degraded_over_limit` | DEGRADED above 100% |
| 10 | `test_pressure_zero_max_returns_ok_unlimited` | Unlimited mode (max=0) |
| 11 | `test_replay_metrics_initial_state` | Initial metrics shape |
| 12 | `test_replay_metrics_reflects_inflight` | bytes_pending_estimate calc |
| 13 | `test_chunks_always_submitted_regardless_of_inflight_count` | No-drop invariant |

Run: `pytest tests/unit/engine/test_replay_backpressure.py -v`
