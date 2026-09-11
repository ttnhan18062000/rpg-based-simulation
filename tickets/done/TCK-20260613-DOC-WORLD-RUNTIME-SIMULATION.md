---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION
phase: done
date: 2026-06-13
tags: [documentation, world, ecology, calamity, threat, raid, boss, spawn, consequences, sovereignty, providers]
---

# TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION

## Title
Document the Living World Simulation Runtime: Ecology, Calamity, Threats, Raid/Boss/Camp, Consequences, Spawn, and Opportunity Providers

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/world/` has four contract docs covering the world **build pipeline**: assembly, compiler, generator, and modules. These explain how a world is constructed from declarative content. They do not explain what the world does **at runtime** — how regions change, how threats propagate, how calamities trigger, how ecology replenishes, how raids and bosses spawn, and how entities receive opportunities from the world.

`src/world/` contains roughly 1,100 lines of runtime simulation logic across 14 files and 3 sub-packages. The parity ledger tracks 112+ `WORLD-*` compliance IDs against this code, confirming it is compliance-critical. Mechanics chapters 05 and 06 name these laws at a surface level (e.g., "ecology replenishes on a schedule") but give no contract-depth coverage of the code behavior.

The result: an agent asked "why did this region change threat level?" or "what triggers a calamity?" cannot answer from docs alone. It must read source.

This ticket creates a suite of runtime contract docs in `docs/world/` that cover the living world simulation distinct from the build pipeline.

## Scope

Create the following docs in `docs/world/`:

### 1. `docs/world/ecology_and_calamity_contract.md`
The two main world evolution drivers. Covers:
- **Ecology**: replenishment schedule (tick-based), node recovery conditions, depletion vs regeneration states, regional ecology health scoring, what caps replenishment rate
- **Calamity**: trigger conditions (threat threshold, ecology collapse, external event), calamity types and their regional effects, duration, resolution conditions, how calamities interact with entity behavior
- Compliance IDs: WORLD-023 through WORLD-028, WORLD-063, SUB-006 (all from `calamity.py`)
- Source areas: `src/world/ecology.py`, `src/world/calamity.py`
- Lifecycle: which engine phase runs these
- Mutation rules: what regional state changes, what must not change within a calamity tick
- Regression tests: cite relevant certification/integration tests

### 2. `docs/world/threat_and_consequences_contract.md`
Regional threat and conquest outcome logic. Covers:
- **Threat classification**: how `region_threat_classifier.py` scores regional danger (entity density, combat activity, faction pressure, calamity overlay)
- **Threat propagation**: how threat spreads between adjacent regions (influence system)
- **Consequences**: what happens to a region after conquest — resource redistribution, sovereignty change, entity behavior shifts, faction standing changes
- **Transformation**: how regions change type or profile as a result of sustained threat or conquest
- Source areas: `src/world/threat.py`, `src/world/region_threat_classifier.py`, `src/world/consequences.py`, `src/world/transformation.py`, `src/world/influence.py`
- Compliance IDs: WORLD-006 (consequences.py), WORLD-032–034 (raid.py)
- Regression tests: cite relevant tests

### 3. `docs/world/raid_boss_camp_contract.md`
Hostile world actor spawning and behavior. Covers:
- **Raids**: trigger conditions, participant selection, raid lifecycle (assembly → assault → resolution), failure conditions
- **Bosses**: spawn conditions (threat level gates, ecology thresholds), boss entity properties vs standard entities, despawn conditions
- **Camps**: camp establishment rules, camp-to-raid escalation, camp persistence model
- **Spawn system**: general entity spawn rules (`spawn.py`, `spawn_config.py`) — what governs when/where entities appear, respawn rules, spawn capacity per region
- Source areas: `src/world/raid.py`, `src/world/boss.py`, `src/world/camp.py`, `src/world/spawn.py`, `src/world/spawn_config.py`
- Regression tests: cite relevant certification or integration tests

### 4. `docs/world/opportunity_providers_contract.md`
How the world exposes opportunities to domain systems. Covers:
- What opportunity providers are: the interface between world state and domain decision systems
- The four provider types: resources, services, requirements, information
- What each provider reads from world state and what it outputs as an opportunity signal
- How providers feed into the adventure domain (route generation) and motivation domain
- The perception gate (`src/world/perception/gate.py`): what filters opportunities before they reach an entity
- The motivation pressure resolver (`src/world/motivation/pressure_resolver.py`): how world pressure shapes entity motivation signals
- Source areas: `src/world/providers/`, `src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py`
- Extension rules: how to add a new opportunity provider type

### 5. `docs/world/regional_sovereignty_runtime_contract.md`
Runtime sovereignty enforcement and transitions. Covers:
- How sovereignty state is maintained tick-to-tick (distinct from the worldbuilding declaration in chapter 06)
- Sovereignty challenge conditions
- How `regional_sovereignty.py` enforces boundaries and resolves conflicts
- Interaction with the consequences system (conquest changes sovereignty)
- Interaction with entity routing (entities check sovereignty before entering regions)
- Source areas: `src/world/regional_sovereignty.py`, `src/world/regions.py`, `src/world/environment.py`
- Links to: `docs/mechanics/regional_sovereignty.md` (mechanics law parent), `docs/mechanics/06_worldbuilding_foundation.md` (declaration parent)

All docs must follow the standard logic-contract template (Purpose, RPG meaning, Inputs, Core rules, Formula/decision logic, Lifecycle, Mutation rules, Edge cases, Examples, Source areas, Regression tests, Extension rules).

## Out of Scope
- The world **build pipeline** (already covered in `docs/world/assembly_contract.md`, `compiler_contract.md`, `generator_contract.md`, `modules_contract.md`)
- Per-file documentation of `src/world/`
- `src/worldassembly/`, `src/worldbuilding/`, `src/worldgeneration/`, `src/worldmodules/` — these back the build pipeline docs

## Acceptance Criteria
- [ ] All 5 docs created in `docs/world/` with correct filenames (no numbered prefixes).
- [ ] Each doc follows the logic-contract template with all sections present.
- [ ] Compliance IDs from source file headers are cited in the relevant doc's `## Regression tests` section.
- [ ] `docs/world/ecology_and_calamity_contract.md` covers both ecology replenishment and calamity triggers with concrete trigger conditions and resolution criteria.
- [ ] `docs/world/threat_and_consequences_contract.md` covers the full threat classification pipeline and what state changes after conquest.
- [ ] `docs/world/raid_boss_camp_contract.md` covers raid lifecycle, boss spawn conditions, and spawn system capacity rules.
- [ ] `docs/world/opportunity_providers_contract.md` explains all four provider types and the perception gate.
- [ ] `docs/world/regional_sovereignty_runtime_contract.md` clearly distinguishes the runtime enforcement from the worldbuilding declaration.
- [ ] Each doc has correct frontmatter: `status: active`, `layer: world`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-DOMAIN-CONTRACTS (opportunity providers feed the adventure and motivation domains — cross-link)
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS (ecology/calamity/threat referenced in adventure routing mechanics)

## Related Docs
- `docs/world/assembly_contract.md` — build pipeline (distinct from this ticket)
- `docs/mechanics/05_world_evolution.md` — world evolution laws (P0 parent for ecology and calamity)
- `docs/mechanics/06_worldbuilding_foundation.md` — worldbuilding foundation (P0 parent for sovereignty)
- `docs/mechanics/regional_sovereignty.md` — sovereignty mechanics (P1)
- `docs/parity_ledger/world_dynamics.yaml` — parity entries for world evolution
- `docs/parity_ledger/substrate.yaml` — substrate parity (spawn, determinism)

## Related Stored Artifacts
None

## Related Code Areas
- `src/world/ecology.py`
- `src/world/calamity.py`
- `src/world/threat.py`
- `src/world/region_threat_classifier.py`
- `src/world/consequences.py`
- `src/world/transformation.py`
- `src/world/influence.py`
- `src/world/raid.py`
- `src/world/boss.py`
- `src/world/camp.py`
- `src/world/spawn.py`
- `src/world/spawn_config.py`
- `src/world/regional_sovereignty.py`
- `src/world/regions.py`
- `src/world/environment.py`
- `src/world/providers/` (information.py, requirements.py, resources.py, services.py)
- `src/world/perception/gate.py`
- `src/world/motivation/pressure_resolver.py`

## Assumptions / Open Questions
- Read compliance ID comments at the top of each source file before writing — they identify which parity ledger entries already exist. Cite them directly in the doc.
- Verify which engine pipeline phase invokes each world system (ecology, calamity, etc.) before writing the lifecycle section.
- The distinction between `docs/world/` (build pipeline) and these new runtime docs should be made explicit in each doc's intro sentence.

## Implementation Notes
1. Start with `ecology.py` and `calamity.py` — these have the most compliance IDs so the parity ledger gives a verification baseline.
2. For each file, read the compliance ID comments at the top, then read `docs/parity_ledger/world_dynamics.yaml` to find the matching entries.
3. Write the threat + consequences doc second — it involves the most cross-file interaction (threat.py, classifier, consequences, transformation, influence).
4. Write opportunity providers last — it ties the world output to the domain input layer and requires understanding all four provider files.

## Test Summary
Not applicable — documentation ticket. Verify via `make knowledge-index-update`.

## Files Changed
- `docs/world/ecology_and_calamity_contract.md` (new)
- `docs/world/threat_and_consequences_contract.md` (new)
- `docs/world/raid_boss_camp_contract.md` (new)
- `docs/world/opportunity_providers_contract.md` (new)
- `docs/world/regional_sovereignty_runtime_contract.md` (new)

## Completion Summary
Created 5 world runtime docs in docs/world/: ecology_and_calamity_contract.md (200-tick ecology cadence, forced calamity 5000-tick interval, CALAMITY_RANDOM_CHANCE dead code noted, environment per-tick modifiers), threat_and_consequences_contract.md (trauma/retaliation dual axes, 6 degradation + 3 recovery transformation paths, influence ±50 thresholds), raid_boss_camp_contract.md (maturity growth, monster cap formula, boss idempotency via boss_region_id, position anchor gap documented), opportunity_providers_contract.md (4 provider types, perception gate formula, motivation pressure 8 dimensions), regional_sovereignty_runtime_contract.md (taxation 100-tick cadence, debuff incomplete implementation documented, no movement gate — routing-only avoidance). Knowledge index: 40 files changed.
