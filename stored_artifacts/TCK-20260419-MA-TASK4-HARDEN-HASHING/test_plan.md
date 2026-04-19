# Test Plan: Canonical Hashing Audit

## Objective
Finalize the `CanonicalStateHasher` and prove it is the absolute source of truth for simulation identity. Verify that non-authoritative state is isolated and that hashing is deterministic regardless of transients.

## Automated Tests

### 1. Truth Isolation Test (`test_hash_isolation`)
- **Action**: 
    1. Capture the hash of the current `AuthoritativeState`.
    2. Change a non-authoritative field (e.g., `kernel._status.signal_history` or `kernel._final_compute_ms`).
    3. Capture the hash again.
- **Assertion**: The hashes must be IDENTICAL.

### 2. Deep Sorting Test (`test_deep_property_sorting`)
- **Input**: An entity with nested properties: `{"meta": {"b": 2, "a": 1}}` vs `{"meta": {"a": 1, "b": 2}}`.
- **Action**: Compare the resulting canonical hashes.
- **Assertion**: The hashes must be IDENTICAL.

### 3. RNG State Load/Save Test (`test_rng_hash_reproducibility`)
- **Action**:
    1. Capture state with an RNG checkpoint.
    2. Reset the `DeterministicRNG` with the captured state.
    3. Capture and compare the hashes.
- **Assertion**: The hashes must be IDENTICAL.

### 4. Deterministic JSON Baseline (`test_json_canonical_format`)
- **Action**: Check `to_canonical_json` for `separators=(",", ":")` and `sort_keys=True`.
- **Assertion**: Verify it produces a compact string with no extra whitespace.

## Manual Verification
- Review `to_canonical_data` to ensure no new fields added to `AuthoritativeState` are missing from the hasher.
