---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-SEED-PARAMS
phase: done
date: 2026-06-14
tags: [worldgen, procedural, seed, parameters, determinism]
---

# TCK-20260614-WORLDGEN-SEED-PARAMS

## Title
Seed-based parameter randomization in procedural composition generator

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`ProceduralCompositionGenerator` selects modules and emits a `WorldCompositionSpec`, but all module `parameters` in the output use their declared `default` values. Two runs with different seeds produce the same parameter values. This ticket adds deterministic seed-based parameter sampling: for each selected module, parameters with `min_value`/`max_value` bounds are sampled from a seeded RNG chain, producing different world instances for different seeds while remaining fully reproducible.

## Scope
- In `ProceduralCompositionGenerator.generate()`, after module selection:
  - Initialize `random.Random(intent.seed)` (standard library, not numpy)
  - For each selected module in selection-rank order, for each `ModuleParameterSpec`:
    - `allowed_values` non-empty → sample with `rng.choice()`
    - `min_value` + `max_value` both set → int or float sampling
    - No bounds/allowed_values → use `default` unchanged
  - `required` params with no default and no bounds → leave absent
- Same `intent.seed` + same module selection order → identical parameter values

## Out of Scope
- Parameter constraint validation (assembly time)
- Sampling from continuous distributions (uniform only)

## Acceptance Criteria
- Two `generate()` calls with `seed=42` produce identical `ModuleRefSpec.parameters`
- `seed=42` vs `seed=99` produce different parameter values for bounded params
- Modules with no bounded parameters are unaffected
- Sampled integer values are within `[min_value, max_value]` inclusive
- Sampled float values are within `[min_value, max_value]`
- Output YAML reflects sampled parameter values in each `module_refs` entry

## Related Tickets
- TCK-20260614-WORLDGEN-COMPOSE (prerequisite)
- TCK-20260614-WORLDMOD-PARAMS (prerequisite)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md
- docs/world/generator_contract.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260614-WORLDGEN-SEED-PARAMS/

## Related Code Areas
- `src/worldgeneration/generator.py` — ProceduralCompositionGenerator.generate()
- `src/worldmodules/schema.py` — ModuleParameterSpec
- `src/worldassembly/schema.py` — ModuleRefSpec.parameters

## Assumptions / Open Questions
- `random.Random(intent.seed)` is initialized fresh per generate() call — no shared state
- RNG call order: module rank order × parameter declaration order

## Implementation Notes
- Added `param_rng = random.Random(intent.seed)` after the conflict check (Rule 5) in `ProceduralCompositionGenerator.generate()`.
- Replaced the single-line `module_refs` list comprehension with an explicit loop that samples parameters per module.
- Sampling priority: `allowed_values` > bounded numeric (int/float by type) > default unchanged.
- Required params with no default and no bounds are left absent from the dict (assembly raises `AssemblyParameterError` if caller doesn't supply them).
- `mod_by_id` dict (already built for BFS deps) reused for parameter lookups — no extra data structure needed.

## Test Summary
- Unit: `tests/unit/worldgeneration/test_seed_params.py`

## Files Changed
- `src/worldgeneration/generator.py` — ProceduralCompositionGenerator.generate(): replaced module_refs list comprehension with param_rng sampling loop
- `tests/unit/worldgeneration/test_seed_params.py` — new: 10 unit tests covering all acceptance criteria
- `docs/parity_ledger/substrate.yaml` — added SUBSTRATE-NEW-011 entry for seed-based parameter sampling

## Completion Summary
Implemented seed-based parameter sampling in ProceduralCompositionGenerator.generate(). A fresh random.Random(intent.seed) is initialized after module selection and consumed in fixed rank × declaration order. Sampling priorities: allowed_values → bounded int/float → default unchanged. 10 new unit tests all pass; 28/28 worldgeneration tests pass. Parity ledger updated with SUBSTRATE-NEW-011.
