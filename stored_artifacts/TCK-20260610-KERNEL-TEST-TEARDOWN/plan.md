# Plan — TCK-20260610-KERNEL-TEST-TEARDOWN

## Approach

Add `kernel.shutdown()` to test teardown for every test file that creates a real `Kernel` (or `EventRecorder`) without calling shutdown. Use `yield` fixtures where the kernel is already fixture-managed; use `try/finally` inline where the kernel is created directly in the test body.

No changes to production code. No changes to `conftest.py` (that is TCK-20260610-THREAD-LEAK-CONFTEST scope).

## Ordered Steps

### Step 1 — `tests/unit/resource/test_resource_intelligence_contract.py`
The `kernel` fixture uses a plain `return`. Convert to a `yield` fixture and add `kernel.shutdown()` in the cleanup block. All three test functions share this fixture; one change covers all three.

### Step 2 — `tests/perf/test_dirty_set_integrity.py`
The `kernel_with_audit` fixture uses a plain `return`. Convert to a `yield` fixture and add `kernel.shutdown()` in the cleanup block.

### Step 3 — `tests/unit/kernel/test_worker_equivalence.py`
The `dual_kernel_setup` fixture creates two kernels (`k_local`, `k_concurrent`). Convert to a `yield` fixture and add shutdown for both kernels. `test_zero_worker_fallback_equivalence` creates `k1` and `k2` inline; wrap the body in `try/finally` to shut down both.

### Step 4 — `tests/unit/kernel/test_replay_determinism.py`
`test_transaction_trace_determinism` creates `kernel` and `kernel2` inside a `with tempfile.TemporaryDirectory()` block. Add `try/finally` wrapping the assertion block to shut down both kernels before the temp dir is removed.

### Step 5 — `tests/perf/test_profiler_integrity.py`
`test_recorded_tick_compute_includes_all_phases` creates a `Kernel` inline. Add `try/finally: kernel.shutdown()` after the assertions (placed so assertions still run before shutdown).

### Step 6 — `tests/perf/test_dirty_parity.py`
`test_dirty_set_vs_full_scan_parity` creates `kernel_opt` and `kernel_ref` inline. Add `try/finally` to shut down both after the comparison assertions.

### Step 7 — `tests/unit/core/test_operational_flags.py`
- `test_safe_operational_flags_accepted`: creates `kernel` inline — add `try/finally: kernel.shutdown()`.
- `test_flags_cannot_alter_authoritative_semantics`: creates `k1` and `k2` inline — add `try/finally` to shut down both.

### Step 8 — `tests/unit/core/test_engine_integrity.py`
- `test_bit_identical_determinism`: creates `kernel1` and `kernel2` — add `try/finally` to shut down both.
- `test_isolation_guard_trigger`: creates `kernel` — add `try/finally: kernel.shutdown()`.

### Step 9 — `tests/unit/core/test_signal_truth.py`
Four test functions each create `kernel` inline. Add `try/finally: kernel.shutdown()` to each.

### Step 10 — `tests/unit/core/test_catalog_smoke_simulation.py`
`test_catalog_mode_smoke_simulation` creates `kernel` inline. Add `try/finally: kernel.shutdown()`.

### Step 11 — `tests/arena/test_arena_tactics.py`
`baseline_kernel` is created inside the `if not result.conformance_passed:` block. Add `try/finally: baseline_kernel.shutdown()` inside that branch.

## Out-of-scope decisions recorded
- `BenchHarness.run_benchmark()` creates a kernel internally but does not call shutdown. Fixing this requires touching production code and is explicitly out of scope. The three `BenchHarness`-based tests in `test_profiler_integrity.py` are exempt from this ticket.
- No blanket autouse fixture is added to `conftest.py` — that is TCK-20260610-THREAD-LEAK-CONFTEST.
