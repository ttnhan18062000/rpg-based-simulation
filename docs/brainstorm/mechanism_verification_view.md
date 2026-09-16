# Mechanism Verification View

Generated from `docs/brainstorm/mechanisms.yaml` — regenerate with `make mechanism-verification-view`. Do not hand-edit.

9 of 75 mechanisms have a recorded verdict. The remaining 66 are rendered explicitly as `unverified` below, not omitted — a mechanism with no verdict is not the same as a mechanism known to work.

**Static vs runtime evidence, grouped separately below**: `code_trace` proves what the code *says* (reachable, called, a field never written) and can never establish that reachable code has its claimed runtime effect. `census`/`scenario`/`corpus_run` prove what the simulation actually *does*. A `code_trace` row is not equivalent evidence to a runtime-confirmed row.

| Mechanism | Layer | State | Evidence | Instrument | Verdict | Date | Note |
|---|---|---|---|---|---|---|---|
| `action_pacing_readiness` | entity | partial | runtime | scenario | observed | 2026-09-16 | Differential scenario (tests/mechanic_scenarios/test_action_pacing_readiness_gate.py): readiness=50.0 withholds a staged attack (INSUFFICIENT_READINESS), readiness=100.0 lets it proceed, through a real Kernel tick against a real compiled world. The gate itself -- what all 23 transitive dependents actually need -- genuinely works. state stays partial: the separate agility-scaling half (readiness_speed) has a real formula (TCK-20260831) but only applies via engine/apply.py's stats_dirty recalculation, never at spawn. Follow-up direct measurement (instrumented call-counting, 3 real corpus worlds, 1000 ticks each) found this path was never observed firing for any of 75 tested entities -- broader than the already-known COMB-318 gap. See TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED- IN-CORPUS (filed, not yet root-caused as content-gap vs wiring-gap). |
| `combat_engagement` | entity | done | runtime | scenario | observed | 2026-09-16 | Corpus: posture gate moved attacks 1960 -> 837. Scenario: risk-rejected posture -> 0 attacks vs no posture -> attack proceeds, all else identical. |
| `camp` | region | done | static | code_trace | contradicted | 2026-09-16 | CampState is real (spawns monsters, triggers raids, a real clearing-reward loop) but no compiled or procedurally-generated world seeds state.camps -- a permanent no-op in every world today. state stays done (the code is correct and wired, not defective) -- the missing thing is world data, not the mechanism itself. See docs/plans/world_composition_precondition_gap_finding.md; same family as the lair-trauma and calamity-intensity cases. |
| `cross_episode_grief_nemesis` | faction | done | static | code_trace | observed | 2026-09-16 | Confirmed live, called from Campaign orchestrator (dead ally -> grief concern; repeated betrayal -> party-formation blocker); narrow trigger. |
| `information_trust_deception` | entity | gated | static | code_trace | observed | 2026-09-16 | Code read confirms the mechanism is correctly built; currently flag-gated off (see state). |
| `motivation_doctrine` | entity | gap | static | code_trace | observed | 2026-09-16 | Found while tracing dependency edges for TCK-20260916-MECHANISM-DEPENDENCY-GRAPH- POPULATION, not this ticket's own target. src/domains/motivation/__init__.py's own docstring: DoctrineResolver and MotivationBiasService were DELETED (TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT, 2026-09-08) -- resolver.py/service.py no longer exist, confirmed dead in production before removal (see docs/guidelines/intentional_divergences.md #2.53), superseded by adventure_routing's own live personality_bias mechanism. gap, not orphan: orphan means dead code still physically present with zero callers (this registry's own established usage, e.g. target_race); here the implementing code itself is gone, so "zero production callers" would be a false claim about code that doesn't exist -- gap is the value that survives becoming an executable assertion (claims-as-tests phase 2). Only evaluator.py (RoleFitEvaluator, an unrelated gear/skill/role-fit scorer) remains in the module. |
| `opportunity_rumor_seeds` | world | gated | static | code_trace | observed | 2026-09-16 | Code read confirms the mechanism is correctly built; currently flag-gated off (see state). |
| `self_model` | entity | gated | static | code_trace | observed | 2026-09-16 | Code read confirms the mechanism is correctly built; currently flag-gated off (see state). |
| `succession` | entity | orphan | static | code_trace | observed | 2026-09-16 | heir_entity_id confirmed never populated by any write path (repo-wide search) -- confirms the orphan claim, does not contradict it. |
| `adventure_routing` | entity | done | unverified | — | unverified | — | — |
| `affection_relationship_bonds` | entity | done | unverified | — | unverified | — | — |
| `aging_death` | entity | done | unverified | — | unverified | — | — |
| `attributes_biology` | entity | done | unverified | — | unverified | — | — |
| `belief_cycle` | entity | done | unverified | — | unverified | — | — |
| `betrayal_siege_war` | faction | done | unverified | — | unverified | — | — |
| `breakthrough_bonuses` | entity | done | unverified | — | unverified | — | — |
| `build_diversity` | entity | gap | unverified | — | unverified | — | — |
| `building_sabotage` | world | done | unverified | — | unverified | — | — |
| `buildings_town_services` | world | done | unverified | — | unverified | — | — |
| `calamities_boss_spawns` | world | done | unverified | — | unverified | — | — |
| `campaigns` | world | done | unverified | — | unverified | — | — |
| `causal_spatial_memory` | entity | orphan | unverified | — | unverified | — | — |
| `chronicle` | world | done | unverified | — | unverified | — | — |
| `city` | region | partial | unverified | — | unverified | — | — |
| `clan` | faction | gap | unverified | — | unverified | — | — |
| `class_assignment` | entity | partial | unverified | — | unverified | — | — |
| `cognition_capacity_fatigue` | entity | done | unverified | — | unverified | — | — |
| `combat_resolution` | entity | done | unverified | — | unverified | — | — |
| `commitment_betrayal` | entity | done | unverified | — | unverified | — | — |
| `committed_intentions` | entity | orphan | unverified | — | unverified | — | — |
| `conversation` | entity | gap | unverified | — | unverified | — | — |
| `country_lifecycle` | faction | partial | unverified | — | unverified | — | — |
| `crafting` | world | partial | unverified | — | unverified | — | — |
| `cross_episode_social_consequences` | faction | orphan | unverified | — | unverified | — | — |
| `cultural_drift` | world | done | unverified | — | unverified | — | — |
| `declared_cognition_schema` | entity | orphan | unverified | — | unverified | — | — |
| `demographic_cohort_cycle` | region | orphan | unverified | — | unverified | — | — |
| `derived_stats` | entity | done | unverified | — | unverified | — | — |
| `diplomacy` | faction | done | unverified | — | unverified | — | — |
| `emotion` | entity | orphan | unverified | — | unverified | — | — |
| `entity_role` | entity | done | unverified | — | unverified | — | — |
| `entity_trade` | entity | gap | unverified | — | unverified | — | — |
| `equipment_scoring` | world | done | unverified | — | unverified | — | — |
| `evolution` | entity | done | unverified | — | unverified | — | — |
| `genetics_aptitude` | entity | orphan | unverified | — | unverified | — | — |
| `goal_hierarchy` | entity | done | unverified | — | unverified | — | — |
| `gods_pantheon_blessings` | world | gap | unverified | — | unverified | — | — |
| `guilds` | group | partial | unverified | — | unverified | — | — |
| `interaction_channeling` | entity | done | unverified | — | unverified | — | — |
| `inventory_trade_conservation` | world | done | unverified | — | unverified | — | — |
| `knowledge_model` | entity | gated | unverified | — | unverified | — | — |
| `lair` | region | gap | unverified | — | unverified | — | — |
| `movement` | entity | done | unverified | — | unverified | — | — |
| `nest` | region | gap | unverified | — | unverified | — | — |
| `party_formation` | group | done | unverified | — | unverified | — | — |
| `perception` | entity | done | unverified | — | unverified | — | — |
| `personality` | entity | done | unverified | — | unverified | — | — |
| `quest_generation_sourcing` | entity | gated | unverified | — | unverified | — | — |
| `race_archetype` | entity | done | unverified | — | unverified | — | — |
| `race_collective_force` | faction | gap | unverified | — | unverified | — | — |
| `regional_trauma_hazards_sovereignty` | region | done | unverified | — | unverified | — | — |
| `reputation` | faction | done | unverified | — | unverified | — | — |
| `ruins_mines_battlefields` | region | partial | unverified | — | unverified | — | — |
| `settlement_capacity_axis` | faction | gap | unverified | — | unverified | — | — |
| `skill_unlocks` | entity | partial | unverified | — | unverified | — | — |
| `social_contracts` | faction | done | unverified | — | unverified | — | — |
| `social_memory` | faction | skeleton | unverified | — | unverified | — | — |
| `status_effects` | entity | partial | unverified | — | unverified | — | — |
| `strategic_intelligence_core` | entity | done | unverified | — | unverified | — | — |
| `tactical_decision` | entity | done | unverified | — | unverified | — | — |
| `team_up` | entity | gap | unverified | — | unverified | — | — |
| `temporal_pressure` | entity | skeleton | unverified | — | unverified | — | — |
| `trauma` | entity | done | unverified | — | unverified | — | — |
| `world_generation` | world | done | unverified | — | unverified | — | — |
| `xp_leveling` | entity | done | unverified | — | unverified | — | — |
