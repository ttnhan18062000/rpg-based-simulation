# Investigation: TCK-20260624-FIX-MOCK-SERIAL

## Root Cause Confirmed

`src/engine/kernel.py` line 646:
```python
update = _dc_replace(update, rng_checkpoint=self._rng.get_state())
```

`src/engine/checkpoint.py` line 105 (`to_canonical_data`):
```python
data["rng_checkpoint"] = state.rng_checkpoint
```
This is passed directly to `json.dumps`. When `self._rng` is a `MagicMock(spec=DeterministicRNG)`, `get_state()` returns another `MagicMock`, which is not JSON-serializable → `TypeError`.

`None` is valid JSON (`null`) and checkpoint.py does not assert `rng_checkpoint is not None`.
Fix: `rng.get_state.return_value = None` on each mock.

## shutdown() Signature
`kernel.shutdown(timeout_s: float = 5.0)` — use `kernel.shutdown(timeout_s=1.0)` in tests.

## Per-File Analysis

### tests/unit/core/test_operational_flags.py
- `test_flags_cannot_alter_authoritative_semantics` (line 71): `rng = MagicMock(spec=DeterministicRNG)`, no `get_state` stub.
  - Already has `try/finally: k1.shutdown(); k2.shutdown()`.
  - Fix: add `rng.get_state.return_value = None` after line 71.
- `test_safe_operational_flags_accepted` (line 33): `rng=MagicMock()` (no spec), already has `try/finally`. Not in the 7 failing tests list, but has same pattern — no fix needed (no spec means `get_state()` returns a MagicMock too, but that test doesn't call `tick_once()`).

### tests/unit/core/test_signal_truth.py
- Multiple tests use `rng = MagicMock(spec=DeterministicRNG)` with no `get_state` stub.
- `test_signal_truth_dropped_work` (line 114): only this is in the 7 failing tests. All 4 rng-using tests call `kernel.tick_once()` so all need the stub.
- All 4 tests already have `try/finally: kernel.shutdown()`.
- Fix: add `rng.get_state.return_value = None` to each of the 4 test functions.

### tests/unit/kernel/test_replay_contract.py
- `test_replay_is_non_authoritative` (line 39): `rng=MagicMock()` (no spec), calls `tick_once()` 5 times.
  - Already has `try/finally: kernel.shutdown()`.
  - `rng=MagicMock()` (no spec): `get_state()` still returns MagicMock, not JSON-serializable.
  - Fix: add `rng = MagicMock()` then `rng.get_state.return_value = None`.

### tests/integration/kernel/test_authoritative_outcome_truth.py
- `mock_deps` fixture has `"rng": MagicMock()` (no spec), no `get_state` stub.
- `test_replay_sources_from_refined_update`: calls only `_phase_init()`, `_phase_scheduling()`, `_phase_collection()`, `_phase_resolution()` — NOT `_phase_advancement()`, so `get_state()` is never called. No TypeError expected.
- However: no kernel shutdown is called. Need to add shutdown.
- Fix: add `rng.get_state.return_value = None` in fixture + add `kernel.shutdown(timeout_s=1.0)` after test body.

### tests/integration/kernel/test_kernel_boundaries.py
- `mock_rng` fixture (line 25): `rng = MagicMock(spec=DeterministicRNG)`, no `get_state` stub.
- Both tests (`test_hook_isolation_from_authoritative_state`, `test_authoritative_hash_purity`) call `tick_once()` → trigger the TypeError.
- Neither test has `try/finally` or shutdown.
- Fix: add `rng.get_state.return_value = None` to `mock_rng` fixture + add shutdown to both tests.

### tests/integration/kernel/test_simulation_kernel_contract.py
- `test_kernel_tick_execution_order` (line 46): `rng = MagicMock(spec=DeterministicRNG)`, no `get_state` stub.
- Calls `kernel.tick_once()`, no shutdown.
- Fix: add `rng.get_state.return_value = None` + wrap in `try/finally`.

## None vs dict
`checkpoint.py` line 105 just assigns `data["rng_checkpoint"] = state.rng_checkpoint` — `None` becomes `null` in JSON, which is valid. No assertion or non-null check found. Using `None` is safe.
