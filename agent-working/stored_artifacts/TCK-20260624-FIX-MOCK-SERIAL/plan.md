# Plan: TCK-20260624-FIX-MOCK-SERIAL

## Ordered Steps

1. **test_operational_flags.py** — add `rng.get_state.return_value = None` after line 71.
   (shutdown already in try/finally)

2. **test_signal_truth.py** — add `rng.get_state.return_value = None` to all 4 test functions
   that use `MagicMock(spec=DeterministicRNG)`.
   (shutdown already in try/finally for all)

3. **test_replay_contract.py** — add `rng.get_state.return_value = None` after `rng=MagicMock()` on line 39.
   (shutdown already in try/finally)

4. **test_authoritative_outcome_truth.py** — add `rng.get_state.return_value = None` to `mock_deps` fixture.
   Add `kernel.shutdown(timeout_s=1.0)` after test body (no shutdown exists).

5. **test_kernel_boundaries.py** — add `rng.get_state.return_value = None` to `mock_rng` fixture.
   Add `try/finally: kernel.shutdown(timeout_s=1.0)` to `test_hook_isolation_from_authoritative_state`
   and `test_authoritative_hash_purity`.

6. **test_simulation_kernel_contract.py** — add `rng.get_state.return_value = None` after rng construction.
   Wrap `Kernel(...)` and `tick_once()` in `try/finally: kernel.shutdown(timeout_s=1.0)`.

7. Run primary tests, verify 7/7 pass.
8. Run cascade tests, verify 5/5 pass.
9. Finalize ticket.

## Non-Goals
- Do not modify production source files.
- Do not change serialization logic in checkpoint.py.
- Do not change kernel.py.
