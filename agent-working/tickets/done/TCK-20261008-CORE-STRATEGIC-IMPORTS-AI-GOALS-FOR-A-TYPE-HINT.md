---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261008-CORE-STRATEGIC-IMPORTS-AI-GOALS-FOR-A-TYPE-HINT
phase: done
date: 2026-10-08
tags: [strategy, architecture]
---

# TCK-20261008-CORE-STRATEGIC-IMPORTS-AI-GOALS-FOR-A-TYPE-HINT

## Title
Five imports break the registry layer order: `src/core/strategic.py` and `src/engine/tactical_rest.py` import the AI package, and KNOW-04's `src/cognition/common_knowledge.py` is imported by the world compiler and spawner (content pipeline importing cognition) while itself importing the engine.

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Owner-confirmed small hotfix for #416: the import-linter contract "Registry layer order" flips to blocking on 2026-10-19. Violations fixed here: (1) the `TYPE_CHECKING` import of `GoalScore` in `src/core/strategic.py` (added by #406); (2) `src/engine/tactical_rest.py` importing `src.ai.goals.need_pull` (mine, #414, SURV-07); and the three that #412 (KNOW-04) added: (3) `src.worldbuilding.compiler -> src.cognition.common_knowledge`, (4) `src.worldassembly.entity_spawner -> src.cognition.common_knowledge`, (5) `src.cognition.common_knowledge -> src.engine.behavior_consumers`. No behaviour change, so hash-neutral.

## Scope
1. `with_live_current_score` stays in `src/core/strategic.py`. Its `live_scores` parameter is typed by a small `LiveScore` Protocol defined in core (read-only properties `kind` and `utility`); the `TYPE_CHECKING` import of `GoalScore` is dropped. `GoalScore` satisfies the protocol structurally.
2. `need_pull.py` is a pure curve used by both the AI scorers and the tactical pass, so it moves from `src/ai/goals/` to `src/engine/` (ai may import engine, not the reverse). Imports, the test file (`tests/unit/engine/test_need_pull.py`) and the doc and ledger path references move with it.

3. KNOW-04's seeding moves to the content layer: `src/content/common_knowledge_seed.py` holds the constants, `danger_fact_key`, `common_knowledge_facts`, `seeded_knowledge` and `default_self_model`, so the compiler, the spawner and the archetype factory (content-pipeline and domain layers) seed a subject without importing cognition. The warmed catalog is reached through a provider the engine installs at import (`install_warm_catalog_provider`, called from `behavior_consumers`); with none installed the default catalog is loaded once in the seed module. `src/cognition/common_knowledge.py` keeps `combat_capability_against` (the reading half) and re-exports the seeding names; it no longer imports the engine. `COMMON_KNOWLEDGE_CERTAINTY` moves with the seeding and `capability_estimate` imports it. `registries/mechanisms.yaml` `knowledge_model.implemented_by` points `seeded_knowledge` at its new path.

## Out of Scope
- Any behaviour or constant; the other ignored imports of the advisory contract.

## Acceptance Criteria
- [x] `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml` reports **17 kept, 0 broken** (on current main it is 16 kept, 1 broken: five violations).
- [x] Hash-neutral: a compiled world's seeding is byte-identical before and after (`probes`-style check: per entity `self_model` facts and `repr(self_model)` hashed for `crowded_frontier`, `frontier_living_world`, `urban_political`, `hero_guild_routing`, `dungeon_crawl`, seed 42; hashes equal, 38 / 49 / 30 / 31 / 12 entities and 266 / 343 / 210 / 217 / 84 facts).
- [x] `tests/unit/strategic/test_project_switch_uses_live_current_score.py` passes (6), and the need and rest tests pass (`tests/unit/engine/test_need_pull.py`, `tests/unit/ai/test_need_scorers.py`, `tests/unit/engine/test_rest_in_place.py`).
- [x] mypy gate (`codebase.gates.mypy_gate`) exits 0 and the code-health ratchet reports 0 new, 0 worse.

## Related Tickets
- `TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE` (#406), `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07` (#414).

## Related Docs
- `codebase/structure/importlinter.toml`; the SURV-07 references in `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml` (STRAT-280) and `docs/guidelines/intentional_divergences.md` (2.81) now name `src/engine/need_pull.py`.

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- `src/core/strategic.py`, `src/engine/need_pull.py`, `src/engine/tactical_rest.py`, `src/ai/goals/scorers.py`.

## Assumptions / Open Questions
- The closed SURV-07 ticket and its stored artifacts still name `src/ai/goals/need_pull.py`; they are history and are left as written.

## Implementation Notes
`LiveScore` is a `Protocol` with read-only `kind` and `utility` properties. `git mv src/ai/goals/need_pull.py src/engine/need_pull.py` and its test; `ruff --fix` for the import order the move changed in `tactical_rest.py`.

## Test Summary
import-linter 17 kept, 0 broken (was 16 kept, 1 broken); project-switch tests 6 passed; need and rest tests and the mechanism completeness pins pass (49 passed in the combined run); mypy gate exit 0; code-health ratchet 0 new, 0 worse.

## Files Changed
`src/core/strategic.py`, `src/engine/need_pull.py` (moved), `src/engine/tactical_rest.py`, `src/ai/goals/scorers.py`, `src/content/common_knowledge_seed.py` (new), `src/cognition/common_knowledge.py`, `src/cognition/capability_estimate.py`, `src/engine/behavior_consumers.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/entity_spawner.py`, `src/entities/archetype_factory.py`, `registries/mechanisms.yaml`, `tests/unit/engine/test_need_pull.py` (moved), `tests/unit/ai/test_need_scorers.py`, `tests/unit/tools/test_mechanism_registry_completeness_check.py` (comment path), `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`, `docs/guidelines/intentional_divergences.md`, `docs/REGISTRY.yaml`.

## Completion Summary
Core no longer imports the AI layer for a type hint, the engine no longer imports the AI layer for the pull curve, and KNOW-04's seeding no longer drags cognition and the engine into the world compiler and spawner. Contracts: 17 kept, 0 broken. No behaviour change; seeding hashes are identical.
