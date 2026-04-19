# Investigation: Canonical Hashing Audit

## Truth Isolation

The `CanonicalStateHasher` only accepts `AuthoritativeState`. This provides a strong structural guarantee that transients in `Kernel`, `RuntimeStatus`, or `WorkerManager` cannot leak into the hash proof. 

Fields included in the hash exactly match the Milestone A contract:
- `tick`, `seed`, `world_time`
- `entities` (ID-sorted)
- `global_resources` (Key-sorted)
- `periodic_due_ticks` (Key-sorted)
- `work_debt` (Key-sorted)
- `rng_checkpoint` (State-sorted)

## Potential Issues

### 1. Shallow Sorting of Properties
The current logic uses `dict(sorted(ent.properties.items()))`. This only sorts the top-level keys. If an entity has:
```python
properties={"meta": {"b": 2, "a": 1}}
```
The `meta` dictionary might not be sorted during `json.dumps` if `sort_keys=True` is not applied recursively or if we rely on the dictionary construction order.
Actually, `json.dumps(..., sort_keys=True)` IS recursive, so this might already be handled. We should verify this with a test.

### 2. RNG State Compatibility
`random.Random.getstate()` returns a large nested tuple. 
Example: `(3, (..., 624), None)`
`json.dumps` will convert this to recursive lists. We need to ensure that the "None" (gauss_next) and other elements are handled consistently across different Python versions if inter-version compatibility is a goal (though likely not for Milestone A).

### 3. Float Precision
Resource values are `float`. Milestone A Law requires total determinism. While JSON serialization of floats is generally stable, we should verify that small precision differences (e.g. from incremental resource updates) are captured accurately.

## Proposed Verification
- **Test 1**: Verify that `Kernel` metrics changes (e.g. `compute_ms`) do NOT change the hash of the state.
- **Test 2**: Verify that deep nested dicts in `properties` are sorted canonically.
- **Test 3**: Verify that RNG state load/restore cycle maintains hash consistency.
