---
status: active
layer: systems
authority: P1
audience: developer
---

# Gameplay Systems

Technical specifications for individual simulation domains.

## Domains
- [Strategic Cognition](../systems/strategic_cognition.md): Bounded cognition and project management.
- [Faction Contract](../systems/faction_contract.md): Faction relationships and diplomatic state.

## Retired (2026-08-10)

`TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT` found that `combat_and_progression.md`,
`world.md`, `buildings_and_economy.md`, `world_generation.md`, `world_evolution_and_resilience.md`,
`ai_system.md`, and this directory's own unlinked `mechanics.md`/`state_machines.md` all describe a
`src/actions/`-and-`src/ai/states.py`-centric architecture that predates the current codebase
structure — moved to `docs/archive/systems/` with pointer notes to their real current replacements
(mostly `docs/mechanics/`, `docs/engine/`, and `docs/simulation/` contract docs; some ground —
buildings, progression/XP, tile/terrain-detail, biome/region design — has no single current
reference doc yet, a disclosed gap rather than a silent one).
