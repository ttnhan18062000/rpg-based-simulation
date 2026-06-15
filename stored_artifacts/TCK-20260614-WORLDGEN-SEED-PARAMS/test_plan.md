# Test Plan — TCK-20260614-WORLDGEN-SEED-PARAMS

## Test File

`tests/unit/worldgeneration/test_seed_params.py`

## Test Cases

1. **Same seed determinism** — two calls with seed=42, same modules → identical parameters dict on each ModuleRefSpec
2. **Different seeds differ** — seed=42 vs seed=99 with bounded params → different values
3. **Integer bounds respected** — sampled int in [min_value, max_value] inclusive
4. **Float bounds respected** — sampled float in [min_value, max_value]
5. **No bounds uses default** — param with no min/max and no allowed_values → default unchanged, no rng consumed
6. **allowed_values sampling** — result is always one of declared values
7. **Mixed params** — module with both bounded and unbounded params; bounded sampled, unbounded use default

## Coverage Targets

- Normal flow: bounded int, bounded float, allowed_values, no-bounds default
- Edge: empty parameters list (no sampling, no crash)
- Regression: existing composition tests still pass
