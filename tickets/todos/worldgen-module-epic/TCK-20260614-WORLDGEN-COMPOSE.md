---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-COMPOSE
phase: open
date: 2026-06-14
tags: [worldgen, procedural, composition, generator]
---

# TCK-20260614-WORLDGEN-COMPOSE

## Title
Procedural composition generator — intent to WorldCompositionSpec YAML

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
There is no code path from `GenerationIntentSpec` to a `WorldCompositionSpec`. The procedural generator (`WorldProceduralGenerator`) builds a `WorldSpec` directly, bypassing the module/composition pipeline entirely. This ticket implements `ProceduralCompositionGenerator` that selects modules via scores from `ModuleScorer`, resolves their dependency graph, and emits a valid `WorldCompositionSpec` YAML to disk. The output is a first-class file — inspectable, editable, and passable to the existing assembly pipeline unchanged.

## Scope
- Implement `ProceduralCompositionGenerator` in `src/worldgeneration/generator.py`:
  - `generate(intent: GenerationIntentSpec, module_repo: WorldModuleRepository) -> Path`
  - Calls `ModuleScorer.score(intent, all_modules)` to get ranked candidates
  - Selection rules:
    - Always include at least one `terrain`-type module (highest scorer)
    - Include one `settlement`-type module if `intent.settlement_style != "none"`
    - Fill remaining slots (up to `budget` — default 6 modules) with highest-scoring remaining candidates
    - Add dependency modules automatically: for each selected module's `requires` list, ensure the required module is also selected
  - Build `WorldCompositionSpec` with selected modules as `module_refs` (structured form), `order` set by selection rank
  - Set `generation_seed = intent.seed` on the composition
  - Derive `world_id` as `f"generated_{intent.settlement_style}_{int(intent.danger_level)}_{intent.seed}"`
  - Write YAML to `data/content/world_compositions/generated/{world_id}.yaml` (create dir if needed)
  - Return the output path
- Expose via `src/worldbuilding/cli.py` as new subcommand `generate`:
  - `python3 -m src.worldbuilding.cli generate --danger-level 3 --settlement-style frontier --seed 42 [--terrain-style temperate] [--resource-density 1.0] [--population-scale 1.0]`
  - Prints the output path on success

## Out of Scope
- Seed-based parameter value randomization (TCK-20260614-WORLDGEN-SEED-PARAMS)
- Assembling or compiling the generated composition (caller's responsibility)
- Conflict resolution between modules (strict collision policy unchanged)

## Acceptance Criteria
- `generate(intent, repo)` with `danger_level=3, settlement_style=frontier, seed=42` produces a YAML file at `data/content/world_compositions/generated/generated_frontier_3_42.yaml`
- The output YAML is a valid `WorldCompositionSpec` that assembles without errors via `WorldAssemblyResolver.assemble()`
- Calling twice with the same intent and seed produces identical YAML (deterministic)
- Dependency modules are automatically included: if `goblin_camp_conflict` requires `frontier_village_core`, both appear even if only the conflict module scored high enough alone
- `make world-compile WORLD=generated_frontier_3_42` works end-to-end after generation
- `python3 -m src.worldbuilding.cli generate --danger-level 3 --settlement-style frontier --seed 42` prints the output path

## Related Tickets
- TCK-20260614-WORLDGEN-SCORING (prerequisite)
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260614-WORLDGEN-SEED-PARAMS (follows this)

## Related Docs
- `docs/world/generator_contract.md`
- `docs/observability/how_to_run_simulation.md`

## Related Code Areas
- `src/worldgeneration/generator.py` — WorldProceduralGenerator, new ProceduralCompositionGenerator
- `src/worldgeneration/scorer.py` — ModuleScorer (from TCK-20260614-WORLDGEN-SCORING)
- `src/worldassembly/schema.py` — WorldCompositionSpec, ModuleRefSpec
- `src/worldmodules/repository.py` — WorldModuleRepository
- `src/worldbuilding/cli.py` — add `generate` subcommand
- `data/content/world_compositions/generated/` — output directory (create)

## Assumptions / Open Questions
- `budget` (max module count) defaults to 6; can be a `GenerationIntentSpec` field later
- If fewer than `budget` eligible modules exist after dependency resolution, use all available

## Test Summary
- Unit: `tests/unit/worldgeneration/test_composition_generator.py` — determinism, dependency auto-inclusion, output path, settlement_style=none skips settlement module
- Integration: generated composition assembles via `WorldAssemblyResolver` without errors

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
