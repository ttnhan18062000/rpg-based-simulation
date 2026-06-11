---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260528-ENTITY-ENHANCE-FUSION
artifact_type: plan
tags: [entity, enhance, fusion]
---

# Implementation Plan - Integrating Enhanced Domain Cognitive / World Loop (Phases 1-10)

This plan outlines how to integrate the 10 domain enhancement phases (Self-Model, Adventure Decisions, Combat Engagement, Information/Belief, Progression, Cooperation, World Emergence, Campaigns, Optimization) into the `AuthoritativeApplyPipeline` and resolve the critical architectural findings listed in `entity_enhance_fix.md`.

## User Review Required

> [!IMPORTANT]
> The enhanced domains will be integrated behind **Feature Flags** in the authoritative loop.
> By default, we will introduce a config option (rollout profile / feature flags) allowing modes:
> - `OFF`: All enhanced domain phases are skipped. The state remains completely bit-identical to the original V2 behavior (verified via hash parity).
> - `SHADOW`: Enhanced domain phases run and generate updates, but their final state changes are discarded so that the authoritative hash remains unchanged.
> - `ON`: Enhanced domain phases are active and mutate the world/entity states deterministically.
> - `STRICT`: Enhanced domain phases are active and run with full performance monitoring and budget restrictions.

## Proposed Changes

We will modify several components to wire these phases into the authoritative cycle:

### 1. Authoritative Apply Pipeline (`src/engine/pipeline.py`)
- Wire the following new phases into `AuthoritativeApplyPipeline.refine`:
  1. `self_model`: Execute `SelfModelUpdatePhase.apply`.
  2. `information_belief`: Execute `InformationBeliefPhase.apply`.
  3. `cooperation`: Execute `CooperationPhase.apply`.
  4. `adventure_decision`: Execute `AdventureDecisionPhase.apply`.
  5. `combat_engagement`: Execute `CombatEngagementPhase.apply`.
  6. `progression_conversion`: Execute `ProgressionConversionPhase.apply`.
  7. `world_emergence`: Execute `WorldEmergencePhase.apply`.
- Interleave these phases correctly based on causality:
  - `self_model` -> updates self awareness and needs.
  - `information_belief` -> processes facts and pending responses, updating the entity's knowledge model.
  - `cooperation` -> handles group recruitment, posture, and cooperation alignment.
  - `adventure_decision` -> uses current needs/weaknesses/opportunities to choose high-level routes.
  - `combat_engagement` -> assesses threat levels and filters targets.
  - `progression_conversion` -> updates leveling and breakthroughs.
  - `world_emergence` -> aggregates region pressure and scarcity.
- Respect `SHADOW` mode: If a flag is in `SHADOW` mode, run the phase's logic (for telemetry, logging, and validation) but do not merge the returned `StateUpdate` into the authoritative pipeline's progressive update.

### 2. Phase Dependency Graph (`src/engine/phase_graph.py`)
- Register the new phases with appropriate input/output domain sets to allow the `DirtySetBuilder` and skip-scheduler optimization to properly skip execution when there is no relevant dirty state:
  - `self_model`: input domains `{"strategic", "attributes"}`, output `{"strategic"}`
  - `information_belief`: input domains `{"strategic", "social"}`, output `{"strategic"}`
  - `cooperation`: input domains `{"social", "strategic"}`, output `{"social", "strategic"}`
  - `adventure_decision`: input domains `{"strategic", "movement"}`, output `{"strategic"}`
  - `combat_engagement`: input domains `{"combat", "movement"}`, output `{"combat", "strategic"}`
  - `progression_conversion`: input domains `{"attributes", "combat"}`, output `{"attributes"}`
  - `world_emergence`: input domains `{"all"}`, output `{"all"}`

### 3. Scenario Runner (`src/testing/scenario_runner.py`)
- Replace the fake/mock execution loop that always returns `defer_with_reason`.
- Execute a real tick-loop using `AuthoritativeApplyPipeline` and the `ApplyPath`.
- Ensure that the opportunity providers read from live world states.

### 4. State-Driven Opportunity Providers (`src/world/providers/resources.py`)
- Ensure `ResourceOpportunityProvider` inspects `state.resource_nodes` and active chests rather than static lists.

### 5. Combat Engagement Spatial Optimization (`src/domains/combat_engagement/`)
- Capping target considerations per entity to a spatial maximum (e.g. up to 8 closest targets within a sensory range) rather than executing an $O(n^2)$ full scan.

## Verification Plan

### Automated Tests
We will add/run a dedicated suite under `tests/integration/domains/` to prove:
- `test_feature_shadow_mode_preserves_authoritative_hash`: Ensures that running in `SHADOW` mode yields the exact same authoritative state hash as `OFF`.
- `test_self_model_phase_runs_in_shadow_without_state_mutation`: Runs the self-model phase and asserts it doesn't mutate live state in SHADOW mode.
- `test_adventure_phase_receives_nonempty_world_opportunities`: Ensures dynamic opportunities flow correctly from providers to decisions.
- `test_resource_provider_uses_state_resource_nodes_and_depletion`: Proves that depleted resource nodes generate zero opportunities.
- `test_information_belief_phase_persists_assimilated_knowledge`: Proves that assimilated facts persist correctly in `entity.self_model` across ticks.
- `test_combat_engagement_targets_considered_are_capped`: Asserts that target consideration scale is $O(1)$ spatially rather than $O(N)$ with target entity count.
- `test_scenario_runner_uses_real_kernel_not_fixed_defer`: Proves that `ScenarioRunner` yields real route selections from live simulations.
