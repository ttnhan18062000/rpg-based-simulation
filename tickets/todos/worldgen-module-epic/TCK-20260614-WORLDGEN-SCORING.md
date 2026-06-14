---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-SCORING
phase: open
date: 2026-06-14
tags: [worldgen, procedural, scoring, intent]
---

# TCK-20260614-WORLDGEN-SCORING

## Title
Module scoring system against GenerationIntentSpec

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`GenerationIntentSpec` (`src/worldgeneration/schema.py`) captures `danger_level`, `terrain_style`, `settlement_style`, `resource_density`, `population_scale`, `required_modules`. `WorldProceduralGenerator` (`src/worldgeneration/generator.py`) uses these values directly to hardcode region hazard levels (e.g. `1.2 * intent.danger_level` at L75) but has no logic to score or select which `WorldModuleSpec` candidates fit the intent. This ticket adds a `ModuleScorer` that produces a ranked score per module against the intent — the foundation for the composition generator.

## Scope
- Implement `ModuleScorer` in `src/worldgeneration/scorer.py` (new file):
  - `score(intent: GenerationIntentSpec, modules: List[WorldModuleSpec]) -> Dict[str, float]` — module_id → normalized score 0.0–1.0
  - Scoring dimensions:
    - `module_type` vs `settlement_style`: `settlement` module type → high score when `settlement_style != "none"`; `terrain` always scores high
    - `danger_level`: modules tagged `["hostile", "conflict", "danger_zone"]` or with type `"conflict"` / `"danger_zone"` score proportionally to `intent.danger_level`
    - `resource_density`: modules with many `resource_recipes` or type `"economy"` score proportionally to `intent.resource_density`
    - `population_scale`: `settlement`/`population` modules score proportionally to `intent.population_scale`
  - `required_modules` from intent always receive score `1.0` regardless of other dimensions
  - Scores are additive across dimensions, then normalized to 0.0–1.0 range
- `ModuleScorer` is a pure function — no side effects, no I/O

## Out of Scope
- Module selection or composition generation (TCK-20260614-WORLDGEN-COMPOSE)
- Seed-based randomization (TCK-20260614-WORLDGEN-SEED-PARAMS)
- Soft dependency ordering between modules

## Acceptance Criteria
- `ModuleScorer.score(intent, modules)` returns a dict with one entry per module
- With `danger_level=3.0`, `goblin_camp_conflict` and `undead_battlefield` score higher than `frontier_village_core`
- `required_modules` entries always score `1.0`
- `settlement_style="none"` gives settlement-type modules a score near 0
- Score dict values are in range `[0.0, 1.0]`
- Pure function — calling twice with same inputs returns identical results

## Related Tickets
- TCK-20260614-WORLDMOD-UNIFY (prerequisite — unified module schema)
- TCK-20260614-WORLDGEN-COMPOSE (depends on this)

## Related Docs
- `docs/world/generator_contract.md`
- `docs/systems/world_generation.md`

## Related Code Areas
- `src/worldgeneration/schema.py` — GenerationIntentSpec
- `src/worldgeneration/scorer.py` — new file
- `src/worldgeneration/generator.py` — WorldProceduralGenerator (context)
- `src/worldmodules/schema.py` — WorldModuleSpec (module_type, tags fields)
- `src/worldmodules/repository.py` — WorldModuleRepository

## Test Summary
- Unit: `tests/unit/worldgeneration/test_module_scorer.py` — danger scoring, settlement_style=none, required_modules always 1.0, score range [0,1], determinism

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
