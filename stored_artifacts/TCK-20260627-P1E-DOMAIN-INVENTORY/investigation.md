# Investigation — TCK-20260627-P1E-DOMAIN-INVENTORY

## Ticket
Create `docs/audits/D19_domain_phase_inventory.md` — a complete inventory of every domain
phase wired in `pipeline.py:refine()` and `world_dynamics.py:resolve_dynamics()`.

## Search Results

### mcp__knowledge-search__search_docs
Query: "domain inventory D19 system wiring pipeline coverage undocumented domain"

Key hits:
- `docs/audits/D09_system_wiring.md` Finding 3 (Risk 13/15): explicitly lists 20+ uninventoried
  domain phases and calls for a D02-equivalent inventory document.
- `docs/plans/audit_fix_plan.md` §P1-E: confirms D19 is the documented remediation plan.
- Working log entry for `TCK-20260618-AUDIT-D09-WIRING`: "Found 20+ live domain systems not in D02."

### graphify query
Query: "domain inventory pipeline phase wiring undocumented"

Confirmed `AuthoritativeApplyPipeline` at `src/engine/pipeline.py:L33` as the central node.
Graph traversal surfaced domain phase community nodes and their source paths across
`src/domains/`, `src/engine/pipeline_phases/`, `src/systems/`, and `src/world/`.

## Key Findings

### pipeline.py:refine() — All Phases (in order)

Enumerated by reading `src/engine/pipeline.py` directly. The `run_phase()` inner function
controls execution; phases pass a `feature_flag` param to opt into FeatureMode gating.

**Group — Phase 1: Trust & Validity (always active)**
- `trust_boundary` → `TrustBoundaryPhase` @ `src/engine/pipeline_phases/trust.py`
- `actor_validity` → `ActorValidityPhase` @ `src/engine/pipeline_phases/actor_validity.py`

**Group — Enhanced RPG Phase 2: Self Model Cognition (feature-gated)**
- `self_model` → `SelfModelUpdatePhase` @ `src/cognition/self_model_phase.py`
  flag: `ENABLE_SELF_MODEL_COGNITION`

**Group — Enhanced RPG Phase 5: Belief Assimilation (feature-gated)**
- `information_belief` → `InformationBeliefPhase` @ `src/domains/information/phase.py`
  flag: `ENABLE_BELIEF_ASSIMILATION`

**Group — Enhanced RPG Phase 7: Social Cooperation (feature-gated)**
- `cooperation` → `CooperationPhase` @ `src/domains/cooperation/phase.py`
  flag: `ENABLE_SOCIAL_COOPERATION`

**Group — Phase 2: Contracts & Production (always active)**
- `contracts` → `ContractLifecyclePhase` @ `src/engine/pipeline_phases/contracts.py`
- `blacksmith` → `BlacksmithSystem` @ `src/engine/blacksmith.py`

**Group — Enhanced RPG Phase 8b: Faction Decision (always active — called directly)**
- `faction_decision` → `FactionDecisionPhase` @ `src/engine/faction_decision.py`
  NOTE: called directly (not via `run_phase`); returns directives for later phases.

**Group — Enhanced RPG Phase 8c: Faction Awareness (always active)**
- `faction_awareness` → `FactionAwarenessService` @ `src/engine/faction_decision.py`

**Group — Enhanced RPG Phase 8d: Diplomatic State Machine (always active)**
- `diplomatic_transitions` → `compute_transitions` + `compute_common_enemy_pairs`
  @ `src/domains/faction/diplomatic_state_machine.py`

**Group — Enhanced RPG Phase 8e: Military Conflict (always active)**
- `military_conflict` → `MilitaryConflictPhase` @ `src/engine/military_conflict.py`

**Group — Enhanced RPG Phase 3: Adventure Routing (feature-gated)**
- `adventure_decision` → `AdventureDecisionPhase` @ `src/domains/adventure/phase.py`
  flag: `ENABLE_ADVENTURE_ROUTING`

**Group — Phase 3: Action & Movement Routing (always active)**
- `action_routing` → `ActionRoutingPhase` @ `src/engine/pipeline_phases/actions.py`
- `position_swaps` → `MovementPhase` @ `src/engine/pipeline_phases/movement.py`
- `movement_routing` → `MovementPhase` @ `src/engine/pipeline_phases/movement.py`

**Group — Enhanced RPG Phase 4: Combat Engagement (feature-gated)**
- `combat_engagement` → `CombatEngagementPhase` @ `src/domains/combat_engagement/phase.py`
  flag: `ENABLE_COMBAT_ENGAGEMENT`

**Group — Phase 4: Interaction & World Effects (always active)**
- `interaction_routing` → `InteractionPhase` @ `src/engine/pipeline_phases/interactions.py`
- `interaction_enforcement` → `InteractionSystem` @ `src/engine/interaction.py`
- `building_sabotage` → `BuildingSabotageSystem` @ `src/engine/sabotage.py`

**Group — Phase 5: Governance & Ecology (always active)**
- `town_resolution` → `TownResolutionSystem` @ `src/engine/town_resolution.py`
- `gold_sink` → `GoldSinkSystem` @ `src/engine/gold_sink.py`
- `world_dynamics` → `WorldDynamicsSystem` @ `src/engine/world_dynamics.py` (contains cadence-gated sub-phases)

**Group — Enhanced RPG Phase 8: World Emergence (feature-gated)**
- `world_emergence` → `WorldEmergencePhase` @ `src/domains/world_emergence/phase.py`
  flag: `ENABLE_WORLD_EMERGENCE`

**Group — Phase 6: Economy & Evolution (always active)**
- `quest_rewards` → `QuestRewardPhase` @ `src/engine/pipeline_phases/quests.py`
- `shop` → `ShopSystem` @ `src/engine/shop.py`
- `paid_information` → `PaidInformationTransactionSystem` @ `src/engine/pipeline_phases/paid_information.py`
- `resource_transactions` → `ResourceTransactionPhase` @ `src/engine/pipeline_phases/resources.py`
- `evolution` → `EvolutionSystem` @ `src/engine/evolution.py`

**Group — Enhanced RPG Phase 6: Progression & Conversion (feature-gated)**
- `progression_conversion` → `ProgressionConversionPhase` @ `src/domains/progression/phase.py`
  flag: `ENABLE_PROGRESSION_EVOLUTION`

**Group — Phase 7: Cognitive & Final Integrity (always active)**
- `strategic_intelligence` → `StrategicIntelligenceSystem` @ `src/systems/strategic.py`
- `near_death_hardening` → `NearDeathHardeningPhase` @ `src/engine/pipeline_phases/hardening.py`
- `occupancy_resolution` → `OccupancyPhase` @ `src/engine/pipeline_phases/occupancy.py`
- `lifecycle` → `LifecycleSystem` @ `src/systems/lifecycle.py`
- `groups` → `GroupPhase` @ `src/engine/pipeline_phases/groups.py`
- `active_contracts` → `ContractService` @ `src/systems/social_systems/contracts.py`
- `expired_offers` → `ContractService` @ `src/systems/social_systems/contracts.py`
- `capacity_enforcement` → `CapacityEnforcementPhase` @ `src/engine/pipeline_phases/capacity_enforcement.py`

**Total pipeline phases: 37** (including 1 called directly outside `run_phase`)
**Feature-gated: 7** (`self_model`, `information_belief`, `cooperation`, `adventure_decision`,
  `combat_engagement`, `world_emergence`, `progression_conversion`)
**Always active: 30**

### world_dynamics.py:resolve_dynamics() — Sub-phases

**Every-tick (no cadence gate):**
- Hazard drain loop → `EnvironmentService` @ `src/world/environment.py`
- Death-triggered trauma accumulation (inline, L44–L60)
- Ownership & calamity progression (inline, L62–L94)
- Regional transformation → `TransformationService` @ `src/world/transformation.py`
- Node cooldown / recharge (inline, L169–L181)
- Chest cooldown (inline, L184–L188)
- Corpse decay (inline, L191–L195)

**Cadence-gated (`should_run(state.tick, None, cadence.world_dynamics)`):**
- `CalamityService.process_world_dynamics()` @ `src/world/calamity.py`
- `SpawnService.process_spawns()` @ `src/world/spawn.py`
- `ResourceEcologyService.process_ecology()` @ `src/world/ecology.py`
- `ThreatService.process_threat_evolution()` @ `src/world/threat.py`
- `BossService.check_for_boss_spawn()` @ `src/world/boss.py` (also: `cadence.boss_spawn`)
- `RaidService.check_for_raid()` @ `src/world/raid.py`
- `CampService.process_camps()` @ `src/world/camp.py`
- `DemographicCycleService.process_demographics()` @ `src/domains/demographics/cohort.py`

**Total world_dynamics sub-phases: 15** (7 every-tick, 8 cadence-gated)

### Format Reference
D02 uses per-feature tables with columns: Feature, Status, Evidence, Notes.
D09 Finding 3 requests D19 match D02's structure.
D19 will use a table per phase with columns: Phase ID, Phase Name, Class / Service, File Path,
Wiring Status, Description, Suggested Acceptance Criterion.

### Notes
- `LeadContradictionSystem` exists at `src/engine/pipeline_phases/lead_contradiction.py`
  and is referenced in D09 Finding 3 as "E42D — wired into authoritative pipeline" but
  is NOT visible in the current `pipeline.py:refine()` call sequence. It may be called
  from within `StrategicIntelligenceSystem.fused_strategic_pass()` or is forthcoming.
  Documented as a note in D19, not as a confirmed pipeline phase.
