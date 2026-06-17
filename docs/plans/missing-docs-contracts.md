---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [planning, contracts, documentation]
---

# Proposal: Missing Engine Contract Documentation for Undocumented src/ Modules

**Author:** Engineering audit  
**Date:** 2026-06-12  
**Context:** Scan of docs/ vs src/ revealed multiple major modules with no engine contracts.
The most critical have Compliance IDs in source code (WORLD-ASM-*, WORLD-*, WORLD-MOD-*,
SCENARIO-*) that reference documents which do not exist, making parity ledger verification
impossible for those systems.

---

## Background

The project has a well-established pattern for engine contracts: each subsystem gets a contract
doc under docs/engine/ or a dedicated docs/<subsystem>/ folder declaring its authoritative
status, resource budget, retention policy, degradation laws, and compliance ID namespace.

A scan of src/ against docs/ found nine major module groups with no contract documents. The
four marked P0 have Compliance IDs already written into the source code — meaning agents and
the parity ledger cannot verify those systems because the backing documents don't exist.

---

## Concern 1: World Assembly Contract (P0)

`src/worldassembly/` has 5 files: resolver.py, entity_spawner.py, models.py, schema.py,
context.py. The resolver carries Compliance IDs WORLD-ASM-008, WORLD-ASM-009, WORLD-ASM-010.
Currently the only coverage is two ADRs (world_assembly_architecture.md,
world_repository_layout.md) — decision records, not pipeline contracts.

We need docs/world/ with a contract covering: the assembly pipeline phases (how a
WorldCompositionSpec becomes a live world), entity spawning rules, schema validation flow,
context lifecycle, and the full WORLD-ASM-* compliance ID namespace with v2_evidence
pointing to the actual source lines.

---

## Concern 2: World Building Contract (P0)

`src/worldbuilding/` has 7 files: compiler.py, recipe.py, repository.py, schema.py,
validator.py, cli.py, __init__.py. compiler.py carries Compliance IDs WORLD-050, WORLD-051,
WORLD-052. Currently docs/mechanics/06_worldbuilding_foundation.md covers the RPG declarative
topology laws but there is no engine contract for the compilation pipeline itself — how
declarative world specs are compiled into WorldCompositionSpec, recipe resolution, validation
rules, and the repository interface.

We need docs/world/ with a contract covering: compiler pipeline, recipe system,
validator rules, repository interface, and the WORLD-* compliance ID namespace.

---

## Concern 3: World Modules Contract (P0)

`src/worldmodules/` has 4 files: normalizer.py, repository.py, schema.py, utils.py.
repository.py carries Compliance IDs WORLD-MOD-004, WORLD-MOD-005. There are zero docs
for this module anywhere in docs/.

We need docs/world/ with a contract covering: the module schema, normalization rules,
repository interface (how modules are loaded and resolved), and the WORLD-MOD-* compliance
ID namespace.

---

## Concern 4: Agentic Lab Contract (P0)

`src/lab/` has 18 files: orchestrator.py, session.py, mutation_orchestrator.py, guardrails.py,
metamorphic.py, audit.py, comparison.py, context.py, mutation.py, registry.py, repository.py,
request.py, schema.py, store.py, validator.py, workflows.py, cli.py. orchestrator.py carries
Compliance IDs SCENARIO-012, SCENARIO-013, SCENARIO-014, SCENARIO-015. The only existing doc
is the historical docs/archive/observability/agentic_lab.md — a phase report, not a contract.

We need docs/simulation/ with a contract covering: lab session lifecycle, mutation pipeline and safety
guardrails, metamorphic testing contract, audit trail rules, human-gated approval flow, and
the SCENARIO-* compliance ID namespace.

---

## Concern 5: Domains Architecture (P1)

`src/domains/` contains 14 domain subsystems — adventure (7 files), campaigns (9),
combat_engagement (10), commitment (4), cooperation (6), emotion (4), information (10),
memory (3), motivation (3), optimization (10), perception (4), progression (9), time (1),
world_emergence (5) — with a total of approximately 85 files. The only partial coverage is
bounded_cognition contracts in docs/strategy/ (covering strategy/cognition only) and
docs/architecture/cognition_domain_ownership.md (cognition only).

We need docs/simulation/domains/ with: a unified domain ownership map covering all 14 subsystems (which
owns what, boundaries, interaction rules), plus individual contracts for the four highest-
complexity domains: combat_engagement, information, campaigns, and optimization. These four
each have 9-10 files and touch critical simulation paths (combat resolution, trust/assimilation,
campaign behavior, cache/degradation/feature flags).

---

## Concern 6: Content Pipeline Contract (P1)

`src/content/` has 8 files: matrix.py, pack_manifest.py, paths.py, reference_graph.py,
repository.py, resolver.py, schema.py, validator.py. `src/content_semantics/` has 4 files:
defaults.py, faction.py, relation.py, role.py. Currently docs/content/content_pack_format.md
covers only the user-facing pack format. ContentUsageMatrix (src/content/matrix.py) is the
canonical consumer validation gate referenced in 10+ recent tickets but has no contract.
content_semantics — the layer providing faction/relation/role semantic defaults — has nothing.

We need docs/content/ expanded with: a content pipeline contract (resolver flow, reference
graph rules, RuntimeContentMode semantics, pack validation lifecycle) and a content_semantics
contract (how semantic defaults for faction, relation, and role are resolved and applied).

---

## Concern 7: World Generation Contract (P1)

`src/worldgeneration/` has 2 files: generator.py, schema.py. docs/systems/world_generation.md
is a high-level system overview, not an engine contract. There is no contract declaring the
generator's authoritative status, its inputs (WorldCompositionSpec), outputs, determinism
guarantees, or its place in the world data pipeline.

We need docs/world/ with a contract covering: generator pipeline, schema definition,
determinism guarantees (seeding rules), and how worldgeneration fits between worldbuilding
(compiler output) and worldassembly (assembly input).

---

## Concern 8: Town Engine Contract (P2)

`src/town/` has 10 files: blacksmith.py, buildings.py, class_hall.py, guild.py, home.py,
home_storage.py, inn.py, sabotage.py, shop.py, town_navigation.py. The only coverage is
docs/mechanics/03_economic_laws.md — RPG economic laws — and docs/systems/buildings_and_economy.md
— a system overview. There is no engine contract for town-level logic: building sabotage rules,
home storage lifecycle, shop transaction flow, or town navigation.

We need docs/simulation/ with a contract covering: building system rules, sabotage pipeline, home
storage lifecycle, shop/trade flow, and how the town subsystem interacts with the authoritative
pipeline phases that reference town logic (phases 4, 9, 12, 15 in authoritative_pipeline.md).

---

## Concern 9: Quest System Contract (P2)

`src/quests/` has 3 files: generator.py, service.py, templates.py. There is no documentation
for the quest system anywhere in docs/. The quest system appears to connect to the reward
pipeline (authoritative pipeline phase 14 — Objective Reward) but there is no contract
documenting how quests are generated, tracked, completed, or expired.

We need docs/simulation/ with a contract covering: quest generation rules, quest lifecycle
(creation, tracking, completion, expiry), template system, and the connection to phase 14
(Objective Reward) in the authoritative pipeline.
