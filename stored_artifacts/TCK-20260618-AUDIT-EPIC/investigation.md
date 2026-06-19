# TCK-20260618-AUDIT-EPIC — Investigation

## Why This Epic Exists

The engine has grown to 14 simulation domains, 65+ foundation features, and a large doc
ecosystem. No prior work had produced a systematic, cross-cutting picture of what the
engine has, what it needs, and what it wants — in a form that could drive prioritized
planning.

Three planning documents existed in the repo root (`feature_summary.md`,
`expected_first_release.md`, `rpg_feature_direction.md`) but were superseded by
`docs/plans/engine_future_epics_roadmap.md` from a 5-fork parallel investigation.
None of them included a framework for rating features or a structured audit programme.

## What Was Investigated (2026-06-18)

This session investigated the engine from the ground up to define the audit programme.

### Phase 1: RPG Feature Landscape
Inspected `docs/plans/engine_future_epics_roadmap.md` and key domain source files to
produce `rpg_simulation_impact.md` (now `docs/audits/D01_rpg_feature_impact.md`).

Key findings:
- 3 Tier-1 features, 1 missing (Resource Ecology Regeneration)
- 9 Tier-2 features, 4 missing (Campaign Runtime, Faction, Scenario Runtime, Macro-Economy)
- CampaignRunner is analysis-only (confirmed by reading `src/domains/campaigns/runner.py`)
- Zero faction behavior code anywhere in `src/`

### Phase 2: Foundation Feature Inventory
Inspected all major source packages to produce `engine_foundation_features.md` (now
`docs/audits/D02_foundation_features.md`).

Key findings:
- 53 Existing, 9 Partial, 3 Missing across 65 foundation features
- Infrastructure layer is mature (100% parity verified in `infrastructure.yaml`)
- Key P0 open parity bugs: COMB-006, COMB-133/134, STRAT-164/177, SOC-134
- `known_limitations.md` is stale (last updated 2026-04-21)
- Flow-field navigation has known local minima risk

### Phase 3: Audit Framework Design
Designed the framework documented in `docs/audits/audit_dimensions.md`:
- Two axes for the audit inventory: State (none/partial/done) and Method
- Two axes for prioritization: Impact (1–5) and Interest (1–5)
- Priority = Impact + Interest; drives audit sequencing

### Phase 4: Expanded Audit Dimension List
Identified 16 audit dimensions beyond the two pre-existing research documents.
Organized into 3 groups (Simulation Quality, Codebase, Developer Tooling).
Rated all 18 dimensions on Impact and Interest to produce the priority table.

## Source Files Inspected

- `docs/plans/engine_future_epics_roadmap.md`
- `docs/simulation/domains/domain_ownership_map.md`
- `docs/engine/known_limitations.md`
- `src/engine/kernel.py`, `spatial.py`, `spatial_query.py`, `cadence.py`,
  `scheduler.py`, `lod.py`, `combat.py`, `legality.py`, `tactical.py`,
  `movement.py`, `movement_cache.py`, `checkpoint.py`, `cache_registry.py`,
  `metrics.py`, `replay_manager.py`, `compactor.py`, `phase_graph.py`,
  `phases.py`, `world_dynamics.py`
- `src/core/conservation.py`, `immutability.py`, `serialization.py`, `dirty.py`
- `src/domains/optimization/feature_flags.py`
- `src/domains/campaigns/runner.py`
- `src/ai/goals/scorers.py`, `personality.py`, `score_modifiers.py`
- `src/world/ecology.py`, `spawn.py`, `calamity.py`
- `src/worldassembly/`, `src/worldbuilding/`, `src/worldgeneration/`, `src/worldmodules/`
- `docs/parity_ledger/*.yaml` (via `engine_future_epics_roadmap.md` summary)

## Architectural Discoveries

1. **CampaignRunner is analysis-only** — confirmed by reading source. Creates isolated
   `AuthoritativeState`, injects synthetic `quest_completed` events, wraps Kernel for
   tick runs, evaluates scorecards. Not a persistent campaign runtime.

2. **Resource Ecology scaffold exists, internals missing** — `ResourceEcologyService`
   exists and is called from `WorldDynamicsSystem` but contains only density/spawn-rate
   logic. No regeneration cycles, no seasonal growth, no node depletion.

3. **known_limitations.md stale** — at least one claim (blacksmith-only towns) is
   contradicted by `TCK-20260425-PH7-M3-RECOVERY` (confirmed done). Other claims may
   also be stale.

4. **Flow-field navigation confirmed** — not A*. Linear-stepping only. Congestion risk
   documented in `known_limitations.md`.

5. **Zero faction behavior code** — `src/content_semantics/faction.py` is catalog data.
   `grand_strategy.md` describes a legacy system that no longer exists in `src/`.
