---
ticket_id: TCK-20260614-CONTENT-HOTPATH-GUARD
date: 2026-06-14
---

# Test Plan: TCK-20260614-CONTENT-HOTPATH-GUARD

File: `tests/unit/engine/test_content_hotpath_guard.py`

| # | Test | AC |
|---|------|-----|
| 1 | `test_warmup_populates_faction_singleton` | warmup() sets cache to non-None |
| 2 | `test_is_warm_false_before_warmup` | is_warm() False before call |
| 3 | `test_is_warm_true_after_warmup` | is_warm() True after call |
| 4 | `test_reset_clears_singletons` | reset() clears back to None |
| 5 | `test_reset_blocked_outside_pytest` | AssertionError if sys.modules lacks pytest |
| 6 | `test_load_all_raises_inside_tick_context` | ContentHotPathViolation raised when flag=True |
| 7 | `test_load_all_ok_outside_tick_context` | No exception when flag=False |
| 8 | `test_tick_context_flag_is_thread_local` | Two threads have independent flag values |
| 9 | `test_tick_context_cleared_on_exception` | Flag cleared in finally even when body raises |
| 10 | `test_load_all_not_called_during_warm_kernel_tick` | Architecture: warm singleton → load_all not called during tick context |

Run: `pytest tests/unit/engine/test_content_hotpath_guard.py -v`
Regression: `pytest tests/unit/engine/ tests/unit/content/ -v`
