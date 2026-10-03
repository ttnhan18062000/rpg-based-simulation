# Implementation Plan — TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION

Date: 2026-06-13
Status: Active

---

## Goal

Create 5 runtime contract docs in `docs/world/` covering the living world simulation subsystems. All docs must follow the standard logic-contract template with frontmatter.

---

## Deliverables

| File | Source files | Compliance IDs |
|---|---|---|
| `docs/world/ecology_and_calamity_contract.md` | ecology.py, calamity.py, environment.py | SUB-006, WORLD-023–028, WORLD-029, WORLD-060, WORLD-061, WORLD-063 |
| `docs/world/threat_and_consequences_contract.md` | threat.py, region_threat_classifier.py, consequences.py, transformation.py, influence.py | WORLD-006, WORLD-062 |
| `docs/world/raid_boss_camp_contract.md` | raid.py, boss.py, camp.py, spawn.py, spawn_config.py | WORLD-030–037, WORLD-048, WORLD-049 |
| `docs/world/opportunity_providers_contract.md` | providers/resources.py, providers/services.py, providers/information.py, providers/requirements.py, perception/gate.py, motivation/pressure_resolver.py | (no compliance header IDs — covered via behavior) |
| `docs/world/regional_sovereignty_runtime_contract.md` | regional_sovereignty.py, regions.py, environment.py | SUB-275–279, WORLD-038, WORLD-041–043, WORLD-052–059 |

---

## Doc Template

Each doc uses this structure:

```
---
status: active
layer: world
authority: P1
audience: agent
last_verified: 2026-06-13
---

# [Title]

## Purpose
## RPG Meaning
## Inputs
## Core Rules
## Formula / Decision Logic
## Lifecycle (which engine phase)
## Mutation Rules
## Edge Cases
## Examples
## Source Areas
## Regression Tests (cite compliance IDs)
## Extension Rules
```

---

## Writing Order

**Doc 1 — Ecology and Calamity** (write first)
- Ecology: 200-tick interval, stability-scaled node target, 50% seeding chance, biome-mapped node kind
- Calamity: 1000-tick maturity, 5000-tick forced spawn after 2000-tick minimum, intensity > 0.3 gate, world_boss spawn at difficulty tier 4
- Hero death consequence: +0.05 calamity intensity if hazard > 0.5
- Environment effects: hazard drain formula, MIASMA modifier, weather multipliers, stronghold aura
- Note the CALAMITY_RANDOM_CHANCE constant that is defined but currently inactive

**Doc 2 — Threat and Consequences** (write second)
- Threat: two-axis model (trauma_score long-term vs retaliation_pressure short-term), decay rates, peaceful-state definition
- Classifier: read-only perspective-based labels, RelationProjectionService path vs legacy bucket fallback
- Consequences: scar types (BATTLE_FIELD severity formula, RAID_DAMAGE fixed 0.8), per-tick baseline recovery
- Influence: DEATH_INFLUENCE_SHIFT=5, conquest at -50, liberation at 50; stronghold spawn/remove lifecycle
- Transformation: threshold table with all 6 degradation paths and 3 recovery paths; most-complex-first selection rule

**Doc 3 — Raid, Boss, Camp, Spawn** (write third)
- Raids: 500-tick interval, maturity-scaled size, deterministic RNG angle, goblin_raider tier 4, no lifecycle tracking
- Bosses: dual gate (maturity ≥ 50 AND trauma ≥ 20), idempotency via boss_region_id, ancient_sentinel → world_boss retyping, ancient_core loot, -20 trauma on death
- Camps: 0.05/tick growth, ×1.5 at trauma > 50, spawn cap formula, raid trigger at maturity ≥ 80, clearing reward -10 trauma
- Spawn: 50-tick interval, density formula, SPAWN_POOLS table, DIFFICULTY_ZONES table, full DifficultyMultipliers table

**Doc 4 — Opportunity Providers** (write fourth)
- Opportunity struct fields and kind enum
- ResourceOpportunityProvider: blocker reward boost, depletion scaling, requirements
- ServiceOpportunityProvider: affordance dispatch table, per-service reward values
- Information providers: Guide/Blacksmith/Guild query contracts, moon_resin special case, Phase 1 mock note
- RequirementEvaluator: all 7 supported kinds and their blocker tags
- PerformanceBudgets: 500 calls total, 1000 requirements total
- PerceptionGate: sense-to-signal channel mapping, score formula, profile fallback
- MotivationPressureResolver: 8 pressures, merge rule, level-to-float table

**Doc 5 — Regional Sovereignty Runtime** (write last)
- Distinguish from worldbuilding declaration (mechanics chapter 06)
- Taxation: 100-tick interval, per-entity and per-building rates, faction gold accumulation
- Debuffs: ATK×0.8, DEF×0.8, SPD×0.9 in monster-owned regions; note apply-path dependency
- Border enforcement: no movement-blocking gate; routing deterrence via threat classifier
- Link to influence.py for sovereignty state transitions (conquest/liberation)
- Link to regions.py for position-to-region resolution that underlies all sovereignty checks

---

## Post-Completion Steps

1. Run `make knowledge-index-update` (required per CLAUDE.md since docs/ files are created)
2. Run `make docs-registry` (to register new docs in REGISTRY.yaml)
3. Move staging artifacts to `stored_artifacts/TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION/`
4. Update ticket status → DONE, move to `tickets/done/`
5. Append to `tickets/working_log.csv`
6. Write agent monitoring entries (run + events)

---

## Architecture Constraints

- All docs are authoritative (authority: P1) but subordinate to Mechanics Bible chapters 05 and 06 (P0)
- Docs must distinguish runtime behavior from build-pipeline behavior (clearly stated in each doc's first sentence)
- Compliance IDs cited under Regression Tests must match exactly what appears in source file headers and/or the parity ledger
- Do not introduce behavioral claims not grounded in the source files read during investigation
