# Investigation: TCK-20260619-E-CAP-REGISTRY

## Current Behavior
- `docs/engine/known_limitations.md` lists unsupported/limited features in human-readable prose only — no machine-readable capability matrix.
- No `src/engine/capability.py` or `docs/engine/capability_registry.yaml` exists.
- No existing backend-readable OFFICIAL/SUPPORTED/EXPERIMENTAL/DEPRECATED/UNSUPPORTED capability tracking.

## Capability IDs to Register (derived from known_limitations.md + done tickets)

### OFFICIAL (core, fully ratified)
- `deterministic_replay` — deterministic tick execution + replay manifest (parity ratified)
- `entity_state` — EntityState and all component types
- `authoritative_pipeline` — 17-phase authoritative mutation pipeline
- `kernel_loop` — 6-phase kernel tick loop
- `combat_resolution` — damage formula, tactical modifiers, durability decay
- `combat_movement` — movement with congestion, legality guards
- `resource_harvesting` — resource node harvesting, atomic conservation
- `town_resolution` — Blacksmith/Inn/Tavern building resolution
- `strategic_cognition` — goal hierarchy, interruption resistance, lead tracking
- `perception` — salience filtering, attention bounds
- `world_generation` — worldgen module system, declarative topology
- `world_composition` — world composition spec, sovereignty
- `xp_rewards` — XP scaling, reward ledger
- `observability_events` — SimulationEvent extraction, JSONL output
- `entity_identity` — personality/identity inspection, behavioral differentiation (E11)
- `phase_domain_permissions` — per-phase read/write/emit domain declarations

### SUPPORTED (implemented, not fully ratified)
- `crafting` — basic crafting recipes (8 active)
- `quest_generation` — static quest generation, objective chains
- `skill_advancement` — AP/equipment progression decisions
- `world_evolution` — regional trauma, ecology basics
- `worker_concurrency` — thread-based worker execution (parity only ratified for sequential mode)

### EXPERIMENTAL
- `worker_concurrency_parity` — bit-identical concurrent worker parity (not yet fully ratified)

### UNSUPPORTED
- `complex_resource_regen` — seasonal growth, depletion cooldowns (resource nodes static/reset on reload)
- `guild_buildings` — Guild, Class Hall, other building types beyond Blacksmith/Inn/Tavern
- `social_blocker_resolution` — social/capability/plot-based strategic blockers
- `person_based_leads` — person/concept-based strategic leads (coordinate-only currently)
- `complex_pathfinding` — dynamic obstacle pathfinding (linear stepping only)
- `complex_social_contention` — negotiation/roll-off for resource contention (deterministic registration order only)
- `metric_export` — per-entity strategic bandwidth and granular metric export to external dashboards

Total: 29 entries (≥20 AC met).

## Architecture Constraints
- Reader must be pure Python, no new runtime dependencies.
- YAML schema must be self-validating via the reader.
- Architecture guard test uses file-based static analysis only.

## Parity Ledger Overlap
- New entry INFRA-209 will be added after INFRA-208 (just added for E-PHASE-PERMISSIONS).

## Risks
- None critical. Additive documentation + thin reader layer.
