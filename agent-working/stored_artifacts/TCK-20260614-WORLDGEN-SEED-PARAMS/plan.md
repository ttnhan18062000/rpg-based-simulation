# Plan — TCK-20260614-WORLDGEN-SEED-PARAMS

## Objective

Add deterministic seed-based parameter sampling to `ProceduralCompositionGenerator.generate()` so that modules with bounded or enum parameters receive varied values per seed, while remaining fully reproducible.

## Implementation Steps

1. In `ProceduralCompositionGenerator.generate()`, after the conflict check (Rule 5) and before building `module_refs`:
   - Initialize `rng = random.Random(intent.seed)`
   - Build `module_refs` with sampled parameters instead of empty dicts

2. Sampling logic per `ModuleParameterSpec`:
   - `allowed_values` non-empty → `rng.choice(param_spec.allowed_values)`
   - `min_value` and `max_value` both set:
     - `type == "integer"` → `rng.randint(int(min_value), int(max_value))`
     - else → `rng.uniform(float(min_value), float(max_value))`
   - Otherwise → use `param_spec.default` (no rng call, preserves determinism)

3. Only write non-None sampled values to the parameters dict. If default is None and no bounds/allowed_values, leave absent (ticket: "leave absent").

## File Changed

- `src/worldgeneration/generator.py` — modify `ProceduralCompositionGenerator.generate()`

## Tests

- `tests/unit/worldgeneration/test_seed_params.py` (new file)
