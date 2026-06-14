---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-SEED-PARAMS
phase: open
date: 2026-06-14
tags: [worldgen, procedural, seed, parameters, determinism]
---

# TCK-20260614-WORLDGEN-SEED-PARAMS

## Title
Seed-based parameter randomization in procedural composition generator

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`ProceduralCompositionGenerator` (TCK-20260614-WORLDGEN-COMPOSE) selects modules and emits a `WorldCompositionSpec`, but all module `parameters` in the output use their declared `default` values. Two runs with different seeds produce the same parameter values. This ticket adds deterministic seed-based parameter sampling: for each selected module, parameters with `min_value`/`max_value` bounds are sampled from a seeded RNG chain, producing different world instances for different seeds while remaining fully reproducible.

## Scope
- In `ProceduralCompositionGenerator.generate()`, after module selection:
  - Initialize `random.Random(intent.seed)` (standard library, not numpy — deterministic across platforms)
  - For each selected module in selection-rank order, for each `ModuleParameterSpec` with `min_value` and `max_value` defined:
    - Sample value within bounds: `int` type → `rng.randint(min_value, max_value)`; `float` → `rng.uniform(min_value, max_value)`
    - Set sampled value in `ModuleRefSpec.parameters` dict for that module ref
  - Parameters with `allowed_values` (enum type): sample from `rng.choice(allowed_values)`
  - Parameters without bounds or allowed_values: use `default` unchanged
  - `required` parameters with no default and no bounds are left to the author — do not sample; leave absent (assembly will raise `AssemblyParameterError` unless the caller supplies them)
- Same `intent.seed` + same module selection order → identical parameter values (deterministic)
- Different seeds → different parameter values within declared bounds

## Out of Scope
- Parameter constraint validation (handled by TCK-20260614-WORLDMOD-PARAMS evaluator at assembly time)
- Sampling from continuous distributions (uniform only)

## Acceptance Criteria
- Two `generate()` calls with `seed=42` produce `ModuleRefSpec.parameters` with identical values
- Two `generate()` calls with `seed=42` and `seed=99` produce different parameter values for modules with bounded params
- Modules with no bounded parameters are unaffected
- Sampled integer values are within `[min_value, max_value]` inclusive
- Sampled float values are within `[min_value, max_value]`
- The output YAML reflects the sampled parameter values in each `module_refs` entry

## Related Tickets
- TCK-20260614-WORLDGEN-COMPOSE (prerequisite)
- TCK-20260614-WORLDMOD-PARAMS (prerequisite — params must work at assembly time)

## Related Code Areas
- `src/worldgeneration/generator.py` — ProceduralCompositionGenerator.generate()
- `src/worldmodules/schema.py` — ModuleParameterSpec (min_value, max_value, allowed_values)
- `src/worldassembly/schema.py` — ModuleRefSpec.parameters

## Test Summary
- Unit: `tests/unit/worldgeneration/test_seed_params.py` — same seed determinism, different seeds differ, bounds respected, no-bounds params use default, float and int type handling

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
