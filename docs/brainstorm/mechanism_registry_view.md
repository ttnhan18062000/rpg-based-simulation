# Mechanism Registry View — Complete

Generated from `registries/mechanisms.yaml` — regenerate with `make mechanism-registry-view`. Do not hand-edit.

All 89 mechanisms, one row each, sorted by priority (`layer weight × transitive dependent-count`) descending. Deliberately not truncated — see `docs/brainstorm/mechanism_priority_view.md` for the focused, unverified-only, top-25 "verify next" ranking, and `docs/brainstorm/mechanism_verification_view.md` for the full verification ledger with notes. This view exists to answer a third, different question: what matters most, and do we know it works, in a single read.

**Node-set note**: this is the first view generated after `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` confirmed the registry's own node set was incomplete (75 mechanisms, atlas-only seed) and registered 11 real mechanisms the original seed never carded (now 86, for `src/domains/`/`src/systems/` — `src/engine/`/`src/core/`/`src/ai/` remain out of that pass's scope). Any earlier figure computed against the 75-mechanism set — the prior unverified count, priority ranking, or dependency-hub count — was computed against a node set later found to be missing 11 real mechanisms and should be treated as superseded by this view.

**6 runtime-verified, 13 static (`code_trace`)-verified, 70 unverified** — of 89 total.

| Mechanism | Layer | State | Evidence | Verdict | Priority | Transitive Dependents |
|---|---|---|---|---|---|---|
| `action_pacing_readiness` | entity | partial | runtime | observed | 125 | 25 |
| `movement` | entity | done | unverified | unverified | 75 | 15 |
| `personality` | entity | done | unverified | unverified | 75 | 15 |
| `tactical_decision` | entity | done | runtime | contradicted | 75 | 15 |
| `combat_engagement` | entity | done | runtime | observed | 70 | 14 |
| `entity_role` | entity | done | unverified | unverified | 70 | 14 |
| `skill_unlocks` | entity | partial | unverified | unverified | 70 | 14 |
| `status_effects` | entity | partial | unverified | unverified | 70 | 14 |
| `combat_resolution` | entity | done | runtime | observed | 65 | 13 |
| `cognition_capacity_fatigue` | entity | done | unverified | unverified | 45 | 9 |
| `perception` | entity | done | unverified | unverified | 40 | 8 |
| `trauma` | entity | done | unverified | unverified | 40 | 8 |
| `self_model` | entity | gated | static | observed | 35 | 7 |
| `betrayal_siege_war` | faction | done | unverified | unverified | 33 | 11 |
| `belief_cycle` | entity | done | unverified | unverified | 30 | 6 |
| `interaction_channeling` | entity | done | unverified | unverified | 30 | 6 |
| `affection_relationship_bonds` | entity | done | unverified | unverified | 25 | 5 |
| `regional_trauma_hazards_sovereignty` | region | done | unverified | unverified | 16 | 8 |
| `goal_hierarchy` | entity | done | unverified | unverified | 15 | 3 |
| `race_archetype` | entity | done | unverified | unverified | 15 | 3 |
| `reputation` | faction | done | unverified | unverified | 12 | 4 |
| `attributes_biology` | entity | done | unverified | unverified | 10 | 2 |
| `world_generation` | world | done | unverified | unverified | 9 | 9 |
| `aging_death` | entity | done | unverified | unverified | 5 | 1 |
| `class_assignment` | entity | partial | unverified | unverified | 5 | 1 |
| `commitment_betrayal` | entity | done | unverified | unverified | 5 | 1 |
| `derived_stats` | entity | done | unverified | unverified | 5 | 1 |
| `motivation_doctrine` | entity | gap | static | observed | 5 | 1 |
| `xp_leveling` | entity | partial | runtime | observed | 5 | 1 |
| `campaigns` | world | done | unverified | unverified | 4 | 4 |
| `city` | region | partial | unverified | unverified | 4 | 2 |
| `diplomacy` | faction | done | unverified | unverified | 3 | 1 |
| `inventory_trade_conservation` | world | done | unverified | unverified | 3 | 3 |
| `social_memory` | faction | skeleton | unverified | unverified | 3 | 1 |
| `camp` | region | done | static | contradicted | 2 | 1 |
| `buildings_town_services` | world | done | unverified | unverified | 1 | 1 |
| `adventure_routing` | entity | done | unverified | unverified | 0 | 0 |
| `belief_institution` | world | partial | unverified | unverified | 0 | 0 |
| `breakthrough_bonuses` | entity | done | unverified | unverified | 0 | 0 |
| `build_diversity` | entity | gap | unverified | unverified | 0 | 0 |
| `building_sabotage` | world | done | unverified | unverified | 0 | 0 |
| `calamities_boss_spawns` | world | done | unverified | unverified | 0 | 0 |
| `causal_spatial_memory` | entity | gated | static | observed | 0 | 0 |
| `chronicle` | world | done | unverified | unverified | 0 | 0 |
| `clan` | faction | gap | unverified | unverified | 0 | 0 |
| `commitment_pressure_consequences` | entity | partial | unverified | unverified | 0 | 0 |
| `committed_intentions` | entity | orphan | unverified | unverified | 0 | 0 |
| `concern_intake` | entity | done | unverified | unverified | 0 | 0 |
| `conversation` | entity | gap | unverified | unverified | 0 | 0 |
| `cooperation` | entity | done | unverified | unverified | 0 | 0 |
| `country_lifecycle` | faction | partial | unverified | unverified | 0 | 0 |
| `crafting` | world | partial | unverified | unverified | 0 | 0 |
| `cross_episode_grief_nemesis` | faction | done | static | observed | 0 | 0 |
| `cross_episode_social_consequences` | faction | done | static | observed | 0 | 0 |
| `cultural_drift` | world | done | unverified | unverified | 0 | 0 |
| `declared_cognition_schema` | entity | orphan | unverified | unverified | 0 | 0 |
| `demographic_cohort_cycle` | region | done | static | contradicted | 0 | 0 |
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
| `knowledge_model` | entity | gated | unverified | unverified | 0 | 0 |
| `lair` | region | gap | unverified | unverified | 0 | 0 |
| `narrative_memory` | world | orphan | unverified | unverified | 0 | 0 |
| `nest` | region | gap | unverified | unverified | 0 | 0 |
| `opportunity_rumor_seeds` | world | gated | static | observed | 0 | 0 |
| `party_formation` | group | done | unverified | unverified | 0 | 0 |
| `progression_conversion` | entity | gated | static | observed | 0 | 0 |
| `quest_generation_sourcing` | entity | gated | unverified | unverified | 0 | 0 |
| `quest_reward_distribution` | group | orphan | unverified | unverified | 0 | 0 |
| `race_collective_force` | faction | gap | unverified | unverified | 0 | 0 |
| `resource_harvesting` | world | orphan | unverified | unverified | 0 | 0 |
| `ruins_mines_battlefields` | region | partial | unverified | unverified | 0 | 0 |
| `settlement_capacity_axis` | faction | gap | unverified | unverified | 0 | 0 |
| `social_contracts` | faction | done | unverified | unverified | 0 | 0 |
| `strategic_intelligence_core` | entity | done | unverified | unverified | 0 | 0 |
| `strategic_learning_bias` | entity | done | unverified | unverified | 0 | 0 |
| `strategic_redirection` | entity | orphan | unverified | unverified | 0 | 0 |
| `succession` | entity | done | static | observed | 0 | 0 |
| `team_up` | entity | gap | unverified | unverified | 0 | 0 |
| `temporal_pressure` | entity | skeleton | unverified | unverified | 0 | 0 |
