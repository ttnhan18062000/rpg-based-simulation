---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, audit]
---

# `src/` Package Structure Audit

Decision record for `TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT` (M5 of `python_code_craft_roadmap.md`).
It records decisions only. No file under `src/` is moved, merged or deleted by this audit, and nothing
moves before the owner reopens `src/` (M7). It seeds the package registry
(`TCK-20261004-PACKAGE-REGISTRY-VALIDATOR`).

## Method

- Population: top-level directories of `git ls-files src` with at least one tracked file: **36** packages.
  `src/social/` and `src/graphify-out/` are untracked local leftovers (a `__pycache__` only; a June graphify
  output). They are not packages. The owner may delete them; no ticket action.
- Size: tracked `.py` files and lines per package, measured on `origin/main` 9793aee08 (2026-10-04).
- Import graph: an `ast` scan of every tracked `.py` file (src, tests, tools, codebase, agent-working,
  experiments, visual_assets), counting **files** that import another top-level package. It resolves both
  `src.x` and bare `x` forms, counts function-local and `TYPE_CHECKING` imports, and ignores relative imports
  (they stay inside a package). `src/` has namespace packages (no `__init__.py` in `core`, `api`, `perf`,
  `certification`, `content_semantics`), so a grimp build over `src` sees only 215 modules and is not used here.
  The brief's importer counts were grep counts; the figures below replace them.
- Layer model: D14 (`docs/audits/D14_coupling_depth.md`, "Layer Architecture") names 8 of the 36 packages.
  This audit assigns the other 28 to the layers below. The layer is the **intended** place; "upward imports"
  lists packages the row imports that sit in a higher layer. Where D14 and the observed graph disagree, both
  are shown.

| Layer | Packages |
|---|---|
| L0 foundation | core, platform, logging, config |
| L1 content pipeline | content, content_semantics, worldmodules, worldassembly, worldbuilding, worldgeneration |
| L2 domain | domains, entities, progression, cognition, strategy, quests, economy |
| L3 engine | engine, scenarios, replay, runtime |
| L4 simulation systems | systems, world, town, ai, actions |
| L5 consumer | observability, api, lab, cli, perf, certification, simulation_quality, rendering, testing, views |

## Package decisions

Decisions: `keep`, `merge-candidate into <pkg>`, `retire-candidate`, `investigate`.

| Package | Purpose | Files / lines | Importers | Layer | Decision and evidence |
|---|---|---|---|---|---|
| `actions` | Two legacy action classes (HarvestAction, LootAction) | 2 / 88 | 0 src / 2 outside | L4 simulation systems; D14: not covered; upward imports: none | **retire-candidate**. 0 src importers, 2 test importers; same responsibilities as `systems/harvest_system.py` and `systems/loot_system.py`; `town/` holds the other `*Action` classes. Owner rpg-planner. |
| `ai` | Life-stage, personality and goal scorers | 11 / 1,318 | 3 src / 26 outside | L4 simulation systems; D14: not covered; upward imports: observability | **keep**. 3 files import it, all in `systems`; `ai/goals` overlaps `strategy`/`cognition` by name only, not verified by import edges. |
| `api` | FastAPI service, presenters, read models | 41 / 7,965 | 3 src / 42 outside | L5 consumer; D14: engine + core; upward imports: none | **keep**. D14 layer; imports 13 packages, 3 of them (`scenarios`, `simulation_quality`, `economy`) not named by D14. |
| `certification` | Certification and scoring harness | 7 / 1,843 | 2 src / 24 outside | L5 consumer; D14: not covered; upward imports: none | **keep**. Imported only by `engine` (1 file) and `scenarios` (1 file) from src. |
| `cli` | Command-line entry points | 3 / 1,077 | 0 src / 9 outside | L5 consumer; D14: not covered; upward imports: none | **keep**. Entry point, no src importer. |
| `cognition` | Self-model, capability estimate, knowledge model, self-model phase | 7 / 1,027 | 3 src / 9 outside | L2 domain; D14: not covered; upward imports: world | **keep**. Distinct from `strategy` (capacity, leads, role-model imitation); both are domain services used by `engine`. See `strategy`. |
| `config` | Runtime configuration | 5 / 631 | 26 src / 180 outside | L0 foundation; D14: not covered; upward imports: engine | **keep**. Imports `engine` and `logging`; 8 src packages import it. |
| `content` | Content schema, loaders, validator | 9 / 3,648 | 26 src / 68 outside | L1 content pipeline; D14: isolated (imports nothing); upward imports: engine | **keep**. D14 says isolated; observed imports `engine`, `worldassembly`, `worldmodules`, `content_semantics`. Shares `ValidationIssue` with `worldbuilding`. |
| `content_semantics` | Semantic services over content (faction, role, relation, personality) | 5 / 668 | 17 src / 13 outside | L1 content pipeline; D14: not covered; upward imports: none | **keep**. 17 src files in 8 packages import it; cycle with `content` (each imports the other). |
| `core` | Entity, state, registry and item primitives | 49 / 9,456 | 291 src / 738 outside | L0 foundation; D14: imports nothing; upward imports: systems, domains, content, replay, engine | **keep**. D14 says imports nothing; observed imports `content`, `domains`, `engine`, `logging`, `replay`, `systems`. Largest fan-in (291 src files). |
| `domains` | Domain services and phase handlers | 133 / 16,577 | 34 src / 274 outside | L2 domain; D14: core only; upward imports: world, systems, engine, observability, scenarios | **keep**. D14 layer; observed imports 15 packages including `engine`, `observability`, `systems` (D14: core only). Subpackages out of scope. |
| `economy` | Economy health monitor and vacancy service | 3 / 159 | 4 src / 4 outside | L2 domain; D14: not covered; upward imports: observability, engine | **merge-candidate into systems**. 3 files, 159 lines; `systems/economy.py` and `systems/economy_systems/` cover the same area. Importers: `api` 1, `engine` 2, `systems` 1. Owner rpg-planner. |
| `engine` | Kernel, pipeline, phases | 94 / 19,823 | 59 src / 463 outside | L3 engine; D14: core + domains; upward imports: systems, world, town, observability, simulation_quality, certification | **keep**. D14 layer; imports 20 packages (D14: core + domains). `pipeline.py` is the engine to domains point. |
| `entities` | Archetype factory, identity resolver, runtime contract | 5 / 472 | 4 src / 7 outside | L2 domain; D14: not covered; upward imports: none | **keep**. Imported by `engine` (3) and `worldassembly` (1). |
| `lab` | Simulation lab, experiments | 28 / 7,957 | 0 src / 41 outside | L5 consumer; D14: engine; upward imports: none | **keep**. D14 layer; 0 src importers (entry point). |
| `logging` | JSON formatter and logging context | 1 / 71 | 112 src / 30 outside | L0 foundation; D14: not covered; upward imports: none | **keep**. 1 file, 71 lines, 112 src importers. The package name shadows the stdlib `logging` name for any import path that has `src/` itself on `sys.path`; not checked here. Record for the owner; no move. |
| `observability` | Event recording, monitors, analysis | 136 / 27,642 | 37 src / 230 outside | L5 consumer; D14: engine; upward imports: none | **keep**. D14 layer; observed imports `domains`, `systems`, `worldbuilding`, `perf` (D14: engine). |
| `perf` | Performance harness | 7 / 1,403 | 2 src / 28 outside | L5 consumer; D14: not covered; upward imports: none | **keep**. Imported by `observability` only; imports `api`. |
| `platform` | RNG, scenario registry, spatial hash | 4 / 192 | 28 src / 139 outside | L0 foundation; D14: not covered; upward imports: none | **keep**. 4 files, 192 lines, 157 outside importers; the deterministic RNG home. `platform/scenarios.py` (`ScenarioRegistry`) overlaps the name of the `scenarios` package: investigate inside the keep. |
| `progression` | Leveling, veterancy, class tiers, skills | 6 / 376 | 4 src / 12 outside | L2 domain; D14: not covered; upward imports: none | **keep**. Imported only by `engine` (4). `SkillScalingService` also exists in `engine/rpg_depth.py`. |
| `quests` | Quest templates, generator, service | 4 / 319 | 4 src / 1 outside | L2 domain; D14: not covered; upward imports: none | **investigate**. `QuestGenerator` exists here and in `systems/world_systems/quest_generator.py`; `QuestTemplate` in three modules (`quests/generator.py`, `quests/templates.py`, `systems/world_systems/quests.py`). Likely a merge with `systems`; needs behaviour comparison. Owner rpg-planner. |
| `rendering` | Map and density rendering | 11 / 1,232 | 0 src / 13 outside | L5 consumer; D14: not covered; upward imports: none | **keep**. 11 files; imports `core` only (the stdlib+src rule in the boundary tests). |
| `replay` | State fingerprinting | 2 / 282 | 2 src / 6 outside | L3 engine; D14: not covered; upward imports: none | **investigate**. 2 files, 282 lines, 2 src importers (`core`, `worldbuilding`); `core` imports `replay` and `replay` imports `core` (cycle). Candidate home is `core` or `engine`; needs the owner. |
| `runtime` | Mode-governed registry bootstrap | 2 / 193 | 0 src / 2 outside | L3 engine; D14: not covered; upward imports: none | **investigate**. 0 src importers, 2 test importers; `bootstrap_registries` overlaps `worldassembly` and `core` registries. May be dead; may be called dynamically. Owner rpg-planner. |
| `scenarios` | Scenario definitions and feature validator | 7 / 662 | 4 src / 22 outside | L3 engine; D14: not covered; upward imports: certification | **keep**. Distinct from `platform/scenarios.py`; see `platform`. |
| `simulation_quality` | SimQ scoring | 25 / 2,834 | 3 src / 32 outside | L5 consumer; D14: not covered; upward imports: none | **keep**. Own pillar contract (`docs/simulation_quality/`). |
| `strategy` | Capacity, leads, role-model imitation | 5 / 300 | 3 src / 6 outside | L2 domain; D14: not covered; upward imports: engine | **investigate**. `capacity.py` and `cognition_capacity.py` both define `CapacityService`; the `cognition` package holds the other half of cognition. Needs a decision on one home. Owner rpg-planner. |
| `systems` | Gameplay systems (economy, crafting, harvest, social, strategic, world) | 71 / 7,983 | 44 src / 164 outside | L4 simulation systems; D14: core + engine (pinned exceptions); upward imports: observability | **keep**. D14 layer; imports `ai`, `strategy`, `economy`, `world`, `observability` beyond core + engine. |
| `testing` | Route-family classifier, scenario runner | 2 / 276 | 0 src / 2 outside | L5 consumer; D14: not covered; upward imports: none | **investigate**. 0 src importers, 2 test importers: test support living in `src/`. Candidate move to `tests/` support. Owner testing planner. |
| `town` | Town buildings and services (blacksmith, guild, inn, home, shop) | 8 / 613 | 3 src / 8 outside | L4 simulation systems; D14: not covered; upward imports: none | **keep**. Imported by `engine` (2) and `world` (1); depends on `quests` and `systems`. |
| `views` | Derived readiness views | 1 / 63 | 0 src / 1 outside | L5 consumer; D14: not covered; upward imports: none | **investigate**. 1 file, 63 lines, 1 test importer, 0 src importers; named in `docs/architecture/cognition_domain_ownership.md` and a parity-ledger entry. Owner rpg-planner. |
| `world` | World state, providers, simulation | 27 / 3,210 | 19 src / 50 outside | L4 simulation systems; D14: not covered; upward imports: none | **keep**. 27 files; imports `town`, `systems`, `domains`, `engine`. |
| `worldassembly` | World module assembly | 5 / 1,823 | 10 src / 25 outside | L1 content pipeline; D14: not covered; upward imports: entities | **keep**. Part of the `world*` family; see family note. |
| `worldbuilding` | Worldbuilding validation and repository | 8 / 2,707 | 18 src / 109 outside | L1 content pipeline; D14: not covered; upward imports: replay, engine, domains, world | **keep**. Shares `ValidationIssue` with `content`; imports 11 packages. |
| `worldgeneration` | Procedural world generator | 3 / 743 | 1 src / 5 outside | L1 content pipeline; D14: not covered; upward imports: none | **keep**. 3 files; its only src importer is `worldbuilding`. |
| `worldmodules` | World module schema, repository, normalizer | 5 / 488 | 9 src / 33 outside | L1 content pipeline; D14: not covered; upward imports: none | **keep**. 42 outside importers; imports only `content` and `worldbuilding` (cycle with `worldbuilding`). |

## Findings

1. **The layer model is not what the graph shows.** D14 says `core` imports nothing. `core` imports
   `content`, `domains`, `engine`, `logging`, `replay` and `systems`. D14 says `content` is isolated. It imports
   `engine`, `worldassembly` and `worldmodules`. The registry's `layer` field records the intended layer; the
   disagreement is data for the import-linter evaluation (`TCK-20261004-IMPORT-LINTER-EVALUATION`), not a
   claim that the model is wrong.
2. **Four packages have no src importer and only test importers:** `actions`, `runtime`, `testing`, `views`.
   `cli`, `lab` and `rendering` also have none but are entry points or tool-facing. No dynamic use (string
   imports, entry-point config) was searched for beyond a text search of non-`.py` files, which found only
   baselines, the docs registry and archived docs. An owner decision must precede any retirement.
3. **Overlap with evidence:** `quests` and `systems/world_systems` (`QuestGenerator`, `QuestTemplate`);
   `strategy/capacity.py` and `strategy/cognition_capacity.py` (`CapacityService`); `economy` and
   `systems/economy*`; `progression` and `engine/rpg_depth.py` (`SkillScalingService`); `platform/scenarios.py`
   and the `scenarios` package (name only). `content` and `worldbuilding` both define `ValidationIssue`.
4. **The `world*` family** (`world`, `worldassembly`, `worldbuilding`, `worldgeneration`, `worldmodules`) has
   two import cycles: `worldbuilding` and `worldmodules` import each other; `worldbuilding`, `worldassembly`
   and `worldgeneration` form another. They do not read as five independent packages. No merge is proposed
   before the cycles are understood: that is the `investigate` item for the owner, not a decision here.
5. **`logging` shares its name with the stdlib module.** Left as is; recorded so the owner can decide at M7.

## Handoff

Non-`keep` decisions go to the owning planner as notes in `.claude/handover/codebase-planner-outbox.md`
(status: pending): `actions`, `economy`, `quests`, `replay`, `runtime`, `strategy`, `views` to `rpg-planner`;
`testing` to the `testing` planner. Nothing moves in M5.
