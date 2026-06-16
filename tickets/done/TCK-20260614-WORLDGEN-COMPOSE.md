---
status: done
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-COMPOSE
phase: done
date: 2026-06-14
tags: [worldgen, procedural, composition, generator]
---

# TCK-20260614-WORLDGEN-COMPOSE

## Title
Procedural composition generator — intent to WorldCompositionSpec YAML

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
There is no code path from `GenerationIntentSpec` to a `WorldCompositionSpec`. The procedural generator (`WorldProceduralGenerator`) builds a `WorldSpec` directly, bypassing the module/composition pipeline entirely. This ticket implements `ProceduralCompositionGenerator` that selects modules via scores from `ModuleScorer`, resolves their dependency graph, and emits a valid `WorldCompositionSpec` YAML to disk. The output is a first-class file — inspectable, editable, and passable to the existing assembly pipeline unchanged.

## Scope
- `GenerationCompositionError` exception class in `src/worldgeneration/generator.py`
- `ProceduralCompositionGenerator` class in `src/worldgeneration/generator.py`
- `generate` subcommand in `src/worldbuilding/cli.py`
- Unit tests: `tests/unit/worldgeneration/test_composition_generator.py`
- Integration test in `tests/integration/worldassembly/`
- Parity ledger entry: SUBSTRATE-NEW-009

## Out of Scope
- Seed-based parameter value randomization (TCK-20260614-WORLDGEN-SEED-PARAMS)
- Full compile and simulation smoke (TCK-20260614-WORLDGEN-E2E-SMOKE)
- Soft conflict resolution or scoring-based avoidance

## Acceptance Criteria
- `generate(intent, repo)` with `danger_level=3, settlement_style=frontier, seed=42` produces a YAML at `data/content/world_compositions/generated/generated_frontier_3_42.yaml`
- Output YAML is a valid `WorldCompositionSpec`
- Calling twice with same intent and seed produces identical YAML
- Dependency modules are automatically included
- Conflicting modules raise `GenerationCompositionError`
- CLI subcommand prints the output path

## Related Tickets
- TCK-20260614-WORLDGEN-SCORING (prerequisite)
- TCK-20260614-WORLDMOD-UNIFY (prerequisite)
- TCK-20260614-WORLDGEN-SEED-PARAMS (follows this)

## Related Docs
- `docs/world/generator_contract.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260614-WORLDGEN-COMPOSE/`

## Related Code Areas
- `src/worldgeneration/generator.py`
- `src/worldgeneration/scorer.py`
- `src/worldassembly/schema.py`
- `src/worldmodules/repository.py`
- `src/worldbuilding/cli.py`

## Assumptions / Open Questions
- `budget` defaults to 6; no intent field for it yet
- `WorldModuleSpec.provides` strings treated as exclusive features for conflict detection
- Conflict check is strict fail-fast; no soft resolution

## Implementation Notes
- `WorldModuleRepository.list_modules()` is the method (not get_all)
- `WorldCompositionSpec` requires schema_version="worldcomposition.v1", world_id, name
- `ModuleRefSpec` fields: module_id, enabled, order, parameters, namespace
- Dependency resolution uses BFS with a visited set to avoid infinite loops
- Deterministic sort: (-score, module_id) for tie-breaking

## Test Summary
- 11 unit tests in `tests/unit/worldgeneration/test_composition_generator.py` — all pass
- 2 integration tests in `tests/integration/worldassembly/test_real_content_world_compositions.py` — all pass
- Pre-existing failures confirmed unchanged (1 unrelated generator test, 1 teardown leak)

## Files Changed
- `src/worldgeneration/generator.py` — added `GenerationCompositionError`, `ProceduralCompositionGenerator`
- `src/worldbuilding/cli.py` — added `handle_generate()`, `generate` subparser
- `tests/unit/worldgeneration/test_composition_generator.py` — new file (11 unit tests)
- `tests/integration/worldassembly/test_real_content_world_compositions.py` — appended 2 integration tests
- `docs/parity_ledger/substrate.yaml` — added SUBSTRATE-NEW-010
- `data/content/world_compositions/generated/` — output directory created

## Completion Summary
Implemented ProceduralCompositionGenerator with full selection pipeline (terrain first, settlement conditional, budget fill, BFS dependency resolution, fail-fast conflict check), WorldCompositionSpec YAML output, and `generate` CLI subcommand. All acceptance criteria met. 13 new tests pass (11 unit + 2 integration).
