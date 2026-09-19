# Mechanism Registry View — Complete

Generated from `registries/mechanisms.yaml` — regenerate with `make mechanism-registry-view`. Do not hand-edit.

All 93 mechanisms, one row each, sorted by priority (`layer weight × transitive dependent-count`) descending. Deliberately not truncated — see `docs/brainstorm/mechanism_priority_view.md` for the focused, unverified-only, top-25 "verify next" ranking, and `docs/brainstorm/mechanism_verification_view.md` for the full verification ledger with notes. This view exists to answer a third, different question: what matters most, and do we know it works, in a single read.

**Node-set note**: this is the first view generated after `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` confirmed the registry's own node set was incomplete (75 mechanisms, atlas-only seed) and registered 11 real mechanisms the original seed never carded (now 86, for `src/domains/`/`src/systems/` — `src/engine/`/`src/core/`/`src/ai/` remain out of that pass's scope). Any earlier figure computed against the 75-mechanism set — the prior unverified count, priority ranking, or dependency-hub count — was computed against a node set later found to be missing 11 real mechanisms and should be treated as superseded by this view.

**9 runtime-verified, 24 static (`code_trace`)-verified, 60 unverified** — of 93 total.

| Mechanism | Layer | State | Evidence | Verdict | Priority | Transitive Dependents |
|---|---|---|---|---|---|---|
| `belief_cycle` | entity | done | unverified | unverified | 20 | 4 |
| `entity_role` | entity | done | unverified | unverified | 15 | 3 |
| `movement` | entity | done | unverified | unverified | 15 | 3 |
| `goal_hierarchy` | entity | done | static | observed | 10 | 2 |
| `personality` | entity | done | unverified | unverified | 10 | 2 |
| `status_effects` | entity | orphan | static | observed | 10 | 2 |
| `affection_relationship_bonds` | entity | done | unverified | unverified | 5 | 1 |
| `aging_death` | entity | done | unverified | unverified | 5 | 1 |
| `attributes_biology` | entity | done | unverified | unverified | 5 | 1 |
| `combat_resolution` | entity | done | runtime | observed | 5 | 1 |
| `race_archetype` | entity | done | static | observed | 5 | 1 |
| `regional_trauma` | region | done | runtime | contradicted | 4 | 2 |
| `campaigns` | world | done | unverified | unverified | 3 | 3 |
| `diplomacy` | faction | done | unverified | unverified | 3 | 1 |
| `social_memory` | faction | skeleton | unverified | unverified | 3 | 1 |
| `buildings` | world | done | unverified | unverified | 2 | 2 |
| `inventory_trade_conservation` | world | done | unverified | unverified | 2 | 2 |
| `regional_sovereignty` | region | done | static | observed | 2 | 1 |
| `world_generation` | world | done | unverified | unverified | 2 | 2 |
| `action_pacing_readiness` | entity | done | runtime | observed | 0 | 0 |
| `adventure_routing` | entity | done | unverified | unverified | 0 | 0 |
| `belief_institution` | world | partial | unverified | unverified | 0 | 0 |
| `betrayal_siege_war` | faction | done | unverified | unverified | 0 | 0 |
| `breakthrough_bonuses` | entity | done | unverified | unverified | 0 | 0 |
| `build_diversity` | entity | gap | unverified | unverified | 0 | 0 |
| `building_sabotage` | world | done | unverified | unverified | 0 | 0 |
| `calamity_intensity` | world | done | runtime | contradicted | 0 | 0 |
| `camp` | region | done | static | contradicted | 0 | 0 |
| `causal_spatial_memory` | entity | gated | static | observed | 0 | 0 |
| `chronicle` | world | done | unverified | unverified | 0 | 0 |
| `city` | region | partial | static | observed | 0 | 0 |
| `clan` | faction | gap | unverified | unverified | 0 | 0 |
| `class_assignment` | entity | partial | static | observed | 0 | 0 |
| `cognition_capacity_fatigue` | entity | done | unverified | unverified | 0 | 0 |
| `combat_engagement` | entity | done | runtime | observed | 0 | 0 |
| `commitment_betrayal` | entity | done | static | observed | 0 | 0 |
| `commitment_pressure_consequences` | entity | partial | unverified | unverified | 0 | 0 |
| `committed_intentions` | entity | orphan | unverified | unverified | 0 | 0 |
| `concern_intake` | entity | done | unverified | unverified | 0 | 0 |
| `conversation` | entity | gap | unverified | unverified | 0 | 0 |
| `cooperation` | entity | done | unverified | unverified | 0 | 0 |
| `country_lifecycle` | faction | partial | static | observed | 0 | 0 |
| `crafting` | world | partial | unverified | unverified | 0 | 0 |
| `cross_episode_grief_nemesis` | faction | done | static | observed | 0 | 0 |
| `cross_episode_social_consequences` | faction | done | static | observed | 0 | 0 |
| `cultural_drift` | world | done | unverified | unverified | 0 | 0 |
| `declared_cognition_schema` | entity | orphan | unverified | unverified | 0 | 0 |
| `demographic_cohort_cycle` | region | done | static | contradicted | 0 | 0 |
| `derived_stats` | entity | done | unverified | unverified | 0 | 0 |
| `emotion` | entity | done | static | observed | 0 | 0 |
| `entity_trade` | entity | gap | unverified | unverified | 0 | 0 |
| `equipment_scoring` | world | done | unverified | unverified | 0 | 0 |
| `event_interpretation` | region | done | unverified | unverified | 0 | 0 |
| `evolution` | entity | done | runtime | observed | 0 | 0 |
| `fame` | world | done | unverified | unverified | 0 | 0 |
| `fidelity_drift` | world | done | unverified | unverified | 0 | 0 |
| `genetics_aptitude` | entity | gated | static | observed | 0 | 0 |
| `gods_pantheon_blessings` | world | gap | unverified | unverified | 0 | 0 |
| `group_coordination` | group | orphan | unverified | unverified | 0 | 0 |
| `guilds` | group | partial | unverified | unverified | 0 | 0 |
| `information_trust_deception` | entity | gated | static | observed | 0 | 0 |
| `interaction_channeling` | entity | done | unverified | unverified | 0 | 0 |
| `knowledge_model` | entity | gated | unverified | unverified | 0 | 0 |
| `lair` | region | gap | unverified | unverified | 0 | 0 |
| `motivation_doctrine` | entity | gap | static | observed | 0 | 0 |
| `narrative_memory` | world | orphan | unverified | unverified | 0 | 0 |
| `nest` | region | gap | unverified | unverified | 0 | 0 |
| `opportunity_rumor_seeds` | world | gated | static | observed | 0 | 0 |
| `party_formation` | group | done | unverified | unverified | 0 | 0 |
| `perception` | entity | done | unverified | unverified | 0 | 0 |
| `progression_conversion` | entity | gated | static | observed | 0 | 0 |
| `quest_generation_sourcing` | entity | gated | unverified | unverified | 0 | 0 |
| `quest_reward_distribution` | group | orphan | unverified | unverified | 0 | 0 |
| `race_collective_force` | faction | gap | unverified | unverified | 0 | 0 |
| `readiness_speed_scaling` | entity | partial | runtime | contradicted | 0 | 0 |
| `reputation` | faction | done | unverified | unverified | 0 | 0 |
| `resource_harvesting` | world | orphan | unverified | unverified | 0 | 0 |
| `ruins_mines_battlefields` | region | partial | static | observed | 0 | 0 |
| `self_model` | entity | gated | static | observed | 0 | 0 |
| `settlement_capacity_axis` | faction | gap | unverified | unverified | 0 | 0 |
| `skill_unlocks` | entity | partial | unverified | unverified | 0 | 0 |
| `social_contracts` | faction | done | unverified | unverified | 0 | 0 |
| `strategic_intelligence_core` | entity | done | unverified | unverified | 0 | 0 |
| `strategic_learning_bias` | entity | done | unverified | unverified | 0 | 0 |
| `strategic_redirection` | entity | orphan | unverified | unverified | 0 | 0 |
| `succession` | entity | done | static | observed | 0 | 0 |
| `tactical_decision` | entity | done | runtime | contradicted | 0 | 0 |
| `team_up` | entity | gap | unverified | unverified | 0 | 0 |
| `temporal_pressure` | entity | skeleton | unverified | unverified | 0 | 0 |
| `town_services` | world | done | unverified | unverified | 0 | 0 |
| `trauma` | entity | orphan | static | observed | 0 | 0 |
| `world_boss_spawn` | world | done | static | observed | 0 | 0 |
| `xp_leveling` | entity | partial | runtime | observed | 0 | 0 |
