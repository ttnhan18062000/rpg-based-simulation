---
status: authoritative
layer: simulation
authority: P1
audience: developer
last_verified: 2026-07-04
---

# SimQ Event Type Coverage

**Status:** Certified Level 1 — Authoritative  
**Ticket:** TCK-20260630-SIMQ-TRANSLATE  
**Date:** 2026-06-30  
**Audit base:** calibration runs in `data/calibration/` (sandbox_world seeds 42/137/999 200t, dungeon_crawl 200t, urban_political 200t, wilderness_survival 200t, simq_routing_test 500t)  
**Last updated:** 2026-07-04 (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B — `self_model_phase.py`'s `events=[]` hardcoding fixed, `pipeline.py:152`'s `information_belief` merge-clobber fixed, and `self_model_bundle_set` durable materialization fixed (`SelfModelPatch`, `SUB-374`); `belief_assimilated`'s Branch B path (route-a-new-query off `self_model.knowledge.unknowns`) confirmed reachable end-to-end via a test-scoped cross-tick-boundary test with both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` ON — see `INFRA-259`/`INFRA-260`. `ENABLE_SELF_MODEL_COGNITION` stays `OFF` in every shipped calibration profile, so Branch B contributes 0 to any real calibration_hits count; `belief_assimilated`'s measured `1` remains entirely Branch A. Byte-identical canonical hash confirmed for `urban_political`'s shipped profile with/without the `SelfModelPatch` fix — 0 impact on existing baselines)

**Previously updated:** 2026-07-03 (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER — `pending_information_responses` compile-time plumbing (INFRA-257) + kernel tick-alignment fix (INFRA-258) shipped: `belief_assimilated`/`belief_updated` calibration_hits confirmed == 1 in each of all 7 `urban_political_*` calibration runs through the real `Kernel.tick_once()` live loop (INFORMATION pillar C→B in all 7; COGNITION C→B in 6 of 7, natural `belief_updated` consequence); `dungeon_crawl` spot-check stayed 0 — no leakage. `calamity_spawned`'s tick-gate comparison fix is verified correct by a dedicated unit test, but a one-off diagnostic run (`dungeon_crawl_seed42_5200t`, not anchored) did not naturally produce the event — a separate, pre-existing hero-death-dependent `calamity_intensity` precondition, not fixed by this ticket. `GovernorModeChanged` confirmed firing naturally in existing long-running baselines — infrastructure telemetry, not SimQ-scored)

**Previously updated:** 2026-07-03 (TCK-20260702-SIMQ-UPLIFT2-INFORMATION — `information_source_profiles` compile-time plumbing shipped and recalibrated across all 7 `urban_political_*` runs; `AuthoritativeState.information_source_profiles` now compiles with 2 entries (`town_notice_board`, `traveling_merchant_rumors`) and `ENABLE_BELIEF_ASSIMILATION=ON` is injected, but at that time `belief_assimilated`/`lead_certainty_updated` calibration_hits remained 0 in every run pending this ticket's kernel-fix + trigger-plumbing follow-up)

---

## Summary

| Category | Count | Notes |
|---|---|---|
| scored | 83 | +1 `spawn_occupancy_violation` (TCK-20260716-PLACELEGAL-SIMQ-SIGNAL) |
| translation_gap | 0 | — |
| engine_emission_gap | 0 | — |
| no_engine_path | 1 | `camp_constructed` — no dynamic camp construction in simulation; scorer entry is premature |
| p0_a_blocked | 3 | Unchanged — campaign/scenario gate |
| unscored_intentional | 13 | Unchanged |

**Last updated:** 2026-07-30 (TCK-20260716-PLACELEGAL-SIMQ-SIGNAL — added the `spawn_occupancy_violation` `_TRANSLATE_CONDITIONAL` row for `InvariantViolation`/`law_id` starting with "LAW-SPAWN-OCCUPANCY", scored by WorldDynamicsScorer)

**Translation table status:** Complete. All 8 `_TRANSLATE_SIMPLE` and 5 `_TRANSLATE_CONDITIONAL` entries in `quality_hub.py` are correct. No translation table gaps found.

**Remaining gaps:** 0 engine emission gaps. 1 scorer entry has no viable engine path (`camp_constructed` — camps are pre-placed at world generation, no dynamic construction mechanic). See §3.9.

---

## Classification Definitions

| Classification | Meaning |
|---|---|
| `scored` | Event is emitted by the engine AND reaches the correct scorer(s) via direct match or translation |
| `translation_gap` | Event is emitted but the translation table has a missing or wrong mapping so it never reaches the scorer |
| `engine_emission_gap` | SCORER_REGISTRY entry exists (scorer ready) but the engine does not emit this event type yet |
| `p0_a_blocked` | Scorer entry exists but the event is gated by a feature flag (ENABLE_ADVENTURE_ROUTING) or infrastructure (campaigns/scenario system) that is OFF in all calibration runs |
| `unscored_intentional` | Event is emitted by the engine but is not wired to any scorer — deliberate |

---

## §1 Scored Events

All events below are emitted by the engine and reach at least one pillar scorer, either directly (contract vocabulary already matches) or after `QualityHub._translate()` remaps the engine event_type.

### §1.1 Direct Emission — No Translation Required

| event_type | source | scorers | calibration_hits | notes |
|---|---|---|---|---|
| `demographic_mortality` | event_extractor | WorldDynamicsScorer | 0 | Emitted only on despawn-without-attacker; rare in short runs |
| `demographic_birth` | event_extractor | WorldDynamicsScorer | 0 | Emitted on entity spawn; scored via world_dynamics pillar |
| `hero_death_unrecorded` | event_extractor | NarrativeScorer | 0 | Only for kind="hero" entities |
| `combat_damage` | CombatDamageEvent | CombatScorer | 0 | Light/long-run mode suppresses non-lethal; lethal path hits scorer |
| `combat_initiated` | event_extractor | CombatScorer | 117 | Fires when entity at full HP takes first hit |
| `near_death_survival` | event_extractor | CombatScorer, ProgressionScorer | 164 | HP crosses below 20% threshold |
| `xp_granted` | event_extractor | ProgressionScorer | 0 | Fires on identity.evolution_points delta |
| `level_up` | event_extractor | ProgressionScorer | 0 | Direct path; also reachable via `lifecycle` translation |
| `route_selected` | event_extractor | AgencyScorer | 20 | Fires when entity.last_routing_family changes. The 20 hits are entirely from `simq_routing_test` (`ENABLE_ADVENTURE_ROUTING=ON`); zero in every other calibration world because the flag defaults `OFF` and `AdventureDecisionPhase` never runs — see `docs/plans/audit_fix_plan.md` P0-A (archetype-intentional zero hits in default worlds — see `eval_matrix_results.md` AGENCY Cross-World Design Note) |
| `action_executed` | event_extractor | AgencyScorer | 20 | Co-fires with route_selected; same `ENABLE_ADVENTURE_ROUTING` gate — 0 hits outside `simq_routing_test` (archetype-intentional zero hits in default worlds — see `eval_matrix_results.md` AGENCY Cross-World Design Note) |
| `self_model_updated` | event_extractor | CognitionScorer | 0 | Fires on self_model_bundle_set. `self_model_bundle_set` now durably materializes into `EntityState.self_model` via the authoritative apply path (`SelfModelPatch`, `src/engine/patches.py`, 2026-07-04, `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`; see `docs/parity_ledger/substrate.yaml::SUB-374`) — this event itself is read off the `EntityUpdate`, not durable state, so its 0-hit count is unaffected either way; still 0 in every calibration run because `ENABLE_SELF_MODEL_COGNITION` stays `OFF` in every shipped profile. |
| `belief_assimilated` | event_extractor | InformationScorer | 1 | Fires on last_assimilated_tick == prior_state.tick (kernel tick-alignment fix, INFRA-258, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER). `pending_information_responses` compile-time plumbing (INFRA-257) seeds one entry targeting `pop_0` (`bandit_road_danger`, `KNOWN_FACT`) in `urban_political`; confirmed calibration_hits == 1 in each of the 7 `urban_political_*` calibration runs (200t/500t/1000t, seeds 42/123/456) via `calibrate_simq.py` through the real `Kernel.tick_once()` live loop — the seed fires exactly once at the initial compiled state (tick 0), not carried forward by `ApplyPath.apply_generation()` on later ticks. 0 hits in `dungeon_crawl` spot-check (no leakage). INFORMATION pillar grade moved C→B in all 7 `urban_political_*` `grade_anchors.json` entries. Prior to the kernel fix, this measured 0 despite the seed/assimilation mechanism working correctly. **Branch B path (2026-07-04, `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`, `INFRA-259`/`INFRA-260`):** the count above is Branch A only (`pending_information_responses`). Branch B's route-a-new-query path (routed off `self_model.knowledge.unknowns`) is now proven reachable end-to-end via a test-scoped cross-tick-boundary test (`self_model_phase.py`'s `events=[]` fixed, `pipeline.py:152`'s merge-clobber fixed, `self_model_bundle_set` materialization fixed) with both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` ON — but `ENABLE_SELF_MODEL_COGNITION` stays `OFF` in every shipped calibration profile, so Branch B contributes 0 to this event's calibration_hits in any real run. This entry's `1` remains entirely attributable to Branch A. |
| `belief_updated` | event_extractor | CognitionScorer | 1 | Co-fires with belief_assimilated (same kernel tick-alignment fix, INFRA-258); confirmed calibration_hits == 1 in each of the 7 `urban_political_*` runs. Also scored by CognitionScorer (`belief_active` tag, distinct from InformationScorer) — this natural, plan-anticipated consequence moves the COGNITION pillar grade C→B in 6 of the 7 `urban_political_*` entries (one anchor was already B); within tolerance, confirmed via `make evaluate --dry-run` (0 regressions). |
| `cooperation_event` | event_extractor | SocialScorer | 1657 | Fires on last_cooperation_decision; 1657 hits in urban_political_seed42_500t with ENABLE_SOCIAL_COOPERATION=ON (TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO) |
| `resource_harvested` | event_extractor | EconomyScorer | 0 | src_kind=NODE in intent_results |
| `item_crafted` | event_extractor | EconomyScorer | 0 | src_kind=CRAFTING |
| `shop_transaction` | event_extractor | EconomyScorer | 0 | src_kind=SHOP_BUY or SHOP_SELL |
| `trade_executed` | event_extractor | EconomyScorer | 0 | Co-fires with shop_transaction |
| `quest_reward_dispensed` | event_extractor | EconomyScorer | 0 | src_kind=QUEST |
| `gold_sink_fired` | event_extractor | EconomyScorer | 0 | src_kind in (REPAIR_FEE, SERVICE_FEE, TAX) (archetype-blocked in dungeon_crawl — see eval_matrix_results.md DA note) |
| `paid_information_transaction` | event_extractor | InformationScorer | 0 | src_kind=INFORMATION_PURCHASE. Requires an active `INFORMATION_SEEKING` project, which only the orphaned `InformationNeedDetector.detect_and_generate()` / `GuildAction.visit()` (zero callers) ever create — still 0 hits post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration. Deferred to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` |
| `paid_info_transaction` | event_extractor | EconomyScorer | 0 | Second emit on INFORMATION_PURCHASE (distinct pillar target) — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY |
| `conservation_law_verified` | event_extractor | EconomyScorer | 0 | tick % 50 + economy events present — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY |
| `scenario_objective_progressed` | engine/scenario_runtime | NarrativeScorer | 0 | Every tick while objective RUNNING — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY |
| `defer_with_reason` | event_extractor | AgencyScorer | 0 | DEFER_WITH_REASON path in phase.py — TCK-20260701-SIMQ-EMIT-AGENCY2 |
| `route_family_first_use` | event_extractor | AgencyScorer | 0 | First use of a novel routing family per entity per run — TCK-20260701-SIMQ-EMIT-AGENCY2. Gated by the same `ENABLE_ADVENTURE_ROUTING` flag as route_selected/action_executed (defaults `OFF`); 0 in all default-mode worlds (archetype-intentional zero hits — see `eval_matrix_results.md` AGENCY Cross-World Design Note). Also 0 in the existing `simq_routing_test_seed42_500t` calibration artifact because that run predates this emitter (TCK-20260630-SIMQ-ROUTING-TEST ran before TCK-20260701-SIMQ-EMIT-AGENCY2 added it) — not yet recalibrated, tracked under P0-A follow-up, not a new gap |
| `commitment_abandoned` | event_extractor | AgencyScorer | 0 | Behavioral classification: abandonment < 3 ticks after start — TCK-20260701-SIMQ-EMIT-AGENCY2 |
| `rejection_cascade_tick` | event_extractor | AgencyScorer | 0 | Population aggregate: > threshold% failed intent rate — TCK-20260701-SIMQ-EMIT-AGENCY2 |
| `lead_certainty_updated` | event_extractor | InformationScorer | 0 | Certainty enum diff per lead per tick — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration — no code path creates the leads whose certainty this would diff; deferred to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` |
| `lead_contradiction_resolved` | lead_contradiction.py | InformationScorer | 0 | Co-emitted with belief_contradiction — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap as `lead_certainty_updated` |
| `paid_info_changed_goal` | event_extractor | InformationScorer | 0 | INFORMATION_PURCHASE + project_id change same tick — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap |
| `belief_stale` | event_extractor | InformationScorer | 0 | VAGUE/APPROXIMATE lead age > 50 ticks, once per lead per run — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap |
| `decision_diverged_by_belief` | event_extractor | InformationScorer | 0 | VAGUE lead + non-information active project — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap |
| `decision_divergence_detected` | event_extractor | CognitionScorer | 0 | DANGER concern urgency > 0.7 + non-survival project — TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS (archetype-blocked in dungeon_crawl — see eval_matrix_results.md DA note) |
| `skill_unlocked` | event_extractor | ProgressionScorer | 0 | learned_skills set diff — TCK-20260701-SIMQ-EMIT-PROGRESSION |
| `trait_expressed` | event_extractor | ProgressionScorer | 0 | traits set diff — TCK-20260701-SIMQ-EMIT-PROGRESSION |
| `pillar_trait_unlocked` | event_extractor | ProgressionScorer | 0 | active_breakthroughs set diff — TCK-20260701-SIMQ-EMIT-PROGRESSION |
| `progression_conversion_applied` | event_extractor | ProgressionScorer | 0 | unspent_ap decrease — TCK-20260701-SIMQ-EMIT-PROGRESSION |
| `progression_plateau_detected` | event_extractor | ProgressionScorer | 18 | XP unchanged for > 50 ticks from run start — TCK-20260701-SIMQ-EMIT-PROGRESSION; calibration_hits updated 2026-07-02 (TCK-20260701-SIMQ-CALIBRATE-REFRESH) |
| `alliance_proposed` | event_extractor | FactionScorer | 0 | NEUTRAL/HOSTILE → ALLIED transition — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY |
| `resource_seized` | event_extractor | FactionScorer | 0 | territory_add + tension_delta > 0 — TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY |
| `ecology_cycle_completed` | event_extractor | WorldDynamicsScorer | 0 | tick % 200 per region — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS |
| `spawn_cadence_fired` | event_extractor | WorldDynamicsScorer | 0 | tick % 50 + non-boss entities_add — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS |
| `threat_evolved` | event_extractor | WorldDynamicsScorer | 0 | trauma_score threshold crossing 25/50/75/100 — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS |
| `node_recharged` | event_extractor | WorldDynamicsScorer | 0 | remaining_charges 0 → >0 — TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS |
| `hazard_drain_applied` | event_extractor | WorldDynamicsScorer | 322 | combat_upd.outcome_kind=="HAZARD" |
| `building_sabotaged` | event_extractor | WorldDynamicsScorer | 0 | Emitted on hp_delta < 0 in building_updates (BuildingSabotageSystem.resolve()); 0 hits expected in all current calibration runs because no strategic/goal-selection/quest-reward code anywhere in src/ currently sets task_upd.work_kind_set="SABOTAGE" or payload_set["action"]="SABOTAGE" — confirmed via repo-wide grep (investigation.md Risk #1); this is a genuine engine emission path with no live producer yet, not a translation gap or missing-scorer gap. TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL |
| `lead_certainty_changed` | event_extractor | CognitionScorer | 0 | Strategic lead certainty state diff; see §3 note on `lead_certainty_updated`. Still 0 post-TCK-20260702-SIMQ-UPLIFT2-INFORMATION recalibration; same deferred-trigger gap |
| `social_memory_created` | event_extractor | SocialScorer | 0 | trust_history new entry or delta ≥ 0.3; once per (entity_id, other_entity_id) per run — TCK-20260701-SIMQ-EMIT-SOCIAL-MEM |
| `contract_milestone_completed` | event_extractor | SocialScorer | 0 | ACTIVE contract at 25%/50%/75% of duration; once per (contract_id, milestone) per run; attributed to source_id — TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE |
| `group_joined` | event_extractor | SocialScorer | 0 | Entity joins a group |
| `group_expelled` | event_extractor | SocialScorer | 0 | Entity leaves a group |
| `reputation_delta` | event_extractor | SocialScorer | 0 | public_reputation delta > 0.05 |
| `contract_offer_created` | event_extractor | SocialScorer | 0 | New contract in OFFERED state |
| `contract_offer_accepted` | event_extractor | SocialScorer | 0 | OFFERED → ACTIVE transition |
| `contract_completed` | event_extractor | SocialScorer | 0 | Contract reaches FULFILLED |
| `contract_lapsed` | event_extractor | SocialScorer | 0 | ACTIVE → EXPIRED |
| `contract_expired_offer` | event_extractor | SocialScorer | 234 | OFFERED → EXPIRED or contract removed; 234 hits in urban_political_seed42_500t with ENABLE_SOCIAL_COOPERATION=ON (TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO) |
| `resource_node_depleted` | event_extractor | EconomyScorer | 0 | Node remaining_charges drops to 0 |
| `region_trauma_delta` | event_extractor | WorldDynamicsScorer | 11 | Non-zero trauma_delta on world_updates |
| `region_ownership_changed` | event_extractor | WorldDynamicsScorer | 0 | owner_faction_id_set changes |
| `region_transformed` | event_extractor | WorldDynamicsScorer | 0 | kind_set on region update |
| `calamity_spawned` | event_extractor | WorldDynamicsScorer | 0 | last_calamity_tick_set == prior_state.tick (kernel tick-alignment fix, INFRA-258, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER) — the tick-comparison bug that made this permanently unreachable through the real `Kernel.tick_once()` loop is fixed and verified correct by a dedicated unit test (`test_calamity_spawned_fires_through_real_tick_once_loop`, which constructs a state meeting CalamityService's spawn gates directly). A one-off diagnostic calibration run (`dungeon_crawl_seed42_5200t`, not added to `grade_anchors.json`) still shows 0 hits: CalamityService additionally requires `calamity_intensity > 0.3` in some region, only raised when a hero-kind entity dies in a `hazard_level > 0.5` region; no hero died in that run's RNG/gameplay. This is a separate, pre-existing content/mechanics precondition, not fixed by the kernel tick-alignment fix — an informational residual gap, not claimed as resolved. |
| `boss_spawned` | event_extractor | WorldDynamicsScorer | 0 | world-boss-gated: entity kind in (world_boss, ancient_sentinel) |
| `narrative_milestone` | event_extractor | NarrativeScorer | 0 | Co-emitted on boss_spawned, war_declared, sovereignty_shift |
| `raid_party_spawned` | event_extractor | WorldDynamicsScorer | 0 | goblin-raider-gated: entity kind == goblin_raider |
| `diplomatic_transition` | event_extractor | FactionScorer | 29 | Direct emit on faction diplomatic_relations_set change; 29 hits confirmed in all 7 `urban_political_*` calibration runs (200t/500t/1000t, seeds 42/123/456) after `bandit_company`/`town_council` seeded to `initial_tension_level=0.5` via `faction_tension_overrides` (TCK-20260702-SIMQ-UPLIFT2-FACTION); 0 in `dungeon_crawl`/`frontier_extended` (no override declared) |
| `alliance_accepted` | event_extractor | FactionScorer | 0 | Direct emit when new_state == ALLIED |
| `territory_ownership_changed` | event_extractor | FactionScorer | 0 | faction.territory_add |
| `faction_tension_delta` | event_extractor | FactionScorer | 0 | Non-zero tension_delta on faction update; still 0 post-TCK-20260702-SIMQ-UPLIFT2-FACTION recalibration — `initial_tension_level` seeding is a compile-time value, not an ongoing per-tick `tension_delta` on a `FactionUpdate`, so this emitter is not exercised by the fix; `diplomatic_transition` (AC-4) is the confirmed non-zero path |
| `war_declared` | event_extractor | FactionScorer | 0 | WorldEvent category == FACTION_WAR_DECLARED |
| `military_conflict_resolved` | event_extractor | FactionScorer | 0 | WorldEvent in (TERRITORY_TRANSFERRED, WAR_ENDED_EXHAUSTION) |
| `world_emergence_event` | event_extractor | NarrativeScorer | 0 | Every WorldEvent in world_events_add |
| `faction_extinct` | event_extractor | FactionScorer | 0 | Faction has no living members; fires only when faction_updates present |
| `chronicle_entry_created` | campaigns/narrative_ledger, campaigns/orchestrator | NarrativeScorer | 0 | Campaign-gated (see §4) |
| `quest_completed` | campaigns/runner | NarrativeScorer | 0 | Campaign-gated; also reachable via quest_event conditional translation |
| `scenario_objective_completed` | engine/scenario_runtime | NarrativeScorer | 0 | Scenario-gated (see §4) |
| `scenario_stalled` | engine/scenario_runtime | NarrativeScorer | 0 | Scenario-gated (see §4) |

### §1.2 Via `_TRANSLATE_SIMPLE` (one-to-one remaps)

| engine event_type | translation | contract_type | scorers | calibration_hits |
|---|---|---|---|---|
| `combat_kill` | _TRANSLATE_SIMPLE | `entity_killed` | CombatScorer | 1 |
| `gold_transaction` | _TRANSLATE_SIMPLE | `gold_transferred` | EconomyScorer | 0 |
| `StrategicObjectiveChanged` | _TRANSLATE_SIMPLE | `strategic_goal_changed` | CognitionScorer | 0 |
| `StrategicConcernRaised` | _TRANSLATE_SIMPLE | `strategic_goal_changed` | CognitionScorer | 0 |
| `StrategicDetourCreated` | _TRANSLATE_SIMPLE | `project_started` | AgencyScorer | 0 |
| `StrategicLeadExhausted` | _TRANSLATE_SIMPLE | `knowledge_default_fallback` | CognitionScorer | 0 |
| `leadership_changed` | _TRANSLATE_SIMPLE | `diplomatic_transition` | FactionScorer | 0 |
| `alliance_formed` | _TRANSLATE_SIMPLE | `alliance_accepted` | FactionScorer | 0 |

### §1.3 Via `_TRANSLATE_CONDITIONAL` (payload-conditional remaps)

| engine event_type | condition | contract_type | scorers | calibration_hits |
|---|---|---|---|---|
| `quest_event` | payload.status == "started" (default) | `quest_started` | NarrativeScorer | 233 |
| `quest_event` | payload.status == "completed" | `quest_completed` | NarrativeScorer | 0 |
| `quest_event` | payload.status == "failed" | `quest_failed` | NarrativeScorer | 0 |
| `lifecycle` | payload.action == "level_up" | `level_up` | ProgressionScorer | 0 |
| `lifecycle` | payload.action in ("despawn","death") | `entity_killed` | CombatScorer | 0 |
| `lifecycle` | payload.action == "spawn" | passthrough — no translation | none | 0 |
| `StrategicProjectChanged` | "complet" in reason | `project_completed` | AgencyScorer | 0 |
| `StrategicProjectChanged` | "abandon" in reason | `project_abandoned` | AgencyScorer | 0 |
| `StrategicProjectChanged` | default | `project_started` | AgencyScorer | 0 |
| `InvariantViolation` | law_id starts with "COMBAT" | `combat_hard_law_violation` | CombatScorer | 0 |
| `InvariantViolation` | law_id starts with "CONSERVATION" | `conservation_law_violated` | EconomyScorer | 0 |
| `InvariantViolation` | law_id starts with "LAW-SPAWN-OCCUPANCY" | `spawn_occupancy_violation` | WorldDynamicsScorer | 0 |
| `InvariantViolation` | other law_id | passthrough — no translation | none | 0 |
| `betrayal_desertion` | payload.faction_id present | `faction_tension_delta` | FactionScorer | 0 |
| `betrayal_desertion` | no faction_id | `contract_lapsed` | SocialScorer | 0 |

---

## §2 Translation Gaps

**None found.** All 8 `_TRANSLATE_SIMPLE` entries and all 5 `_TRANSLATE_CONDITIONAL` entries in `src/simulation_quality/quality_hub.py` are correct and complete as of this audit. Every engine event_type that the translation table touches maps to a valid contract vocabulary type that exists in `SCORER_REGISTRY`.

Test coverage was incomplete for 3 entries (`leadership_changed`, `alliance_formed`, `betrayal_desertion`). Tests were added in `tests/simulation_quality/test_quality_hub_event_translation.py` as part of this ticket.

---

## §3 Engine Emission Gaps

These contract vocabulary types appear in at least one scorer's `EVENT_TYPES` tuple and are therefore registered in `SCORER_REGISTRY`, but the engine never emits them. Scoring infrastructure is ready; upstream emission is deferred to future engine work.

### §3.1 Agency (AgencyScorer)

> All AGENCY pillar events are now emitted. See §1.1 for the 4 events added by TCK-20260701-SIMQ-EMIT-AGENCY2 (`defer_with_reason`, `route_family_first_use`, `commitment_abandoned`, `rejection_cascade_tick`).

### §3.2 Cognition (CognitionScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS.

| contract_type | resolved by |
|---|---|
| `decision_divergence_detected` | `event_extractor.py` — DANGER concern urgency > 0.7 + non-survival project |

### §3.3 Information (InformationScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS.

| contract_type | resolved by |
|---|---|
| `lead_certainty_updated` | `event_extractor.py` — certainty enum diff per lead per tick |
| `lead_contradiction_resolved` | `lead_contradiction.py` — emitted alongside `belief_contradiction` |
| `paid_info_changed_goal` | `event_extractor.py` — INFORMATION_PURCHASE intent + project_id change |
| `belief_stale` | `event_extractor.py` — VAGUE/APPROXIMATE lead age > 50 ticks, once per lead per run |
| `decision_diverged_by_belief` | `event_extractor.py` — VAGUE lead + non-information active project |

### §3.4 Economy (EconomyScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY.

| contract_type | resolved by |
|---|---|
| `paid_info_transaction` | `event_extractor.py` — second emit on INFORMATION_PURCHASE (distinct from `paid_information_transaction`) |
| `conservation_law_verified` | `event_extractor.py` — tick % 50 guard + economy events present in current tick |

### §3.5 Narrative (NarrativeScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY.

| contract_type | resolved by |
|---|---|
| `scenario_objective_progressed` | `scenario_runtime.py` — emitted every tick while objective is RUNNING |

### §3.6 Progression (ProgressionScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-PROGRESSION.

| contract_type | resolved by |
|---|---|
| `skill_unlocked` | `event_extractor.py` — learned_skills set diff |
| `trait_expressed` | `event_extractor.py` — traits set diff |
| `pillar_trait_unlocked` | `event_extractor.py` — active_breakthroughs set diff |
| `progression_conversion_applied` | `event_extractor.py` — unspent_ap decrease |
| `progression_plateau_detected` | `event_extractor.py` — xp_rate_zero + skill_silence signals |

### §3.7 Faction (FactionScorer)

All previously listed gaps resolved by TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY.

| contract_type | resolved by |
|---|---|
| `alliance_proposed` | `event_extractor.py` — NEUTRAL/HOSTILE → ALLIED transition detected via prior_state.factions |
| `resource_seized` | `event_extractor.py` — FactionUpdate.territory_add with tension_delta > 0 |

### §3.8 Social (SocialScorer)

All gaps resolved.

| contract_type | resolved by |
|---|---|
| `social_memory_created` | `EventExtractor` — `trust_history` delta (new entry or Δ ≥ 0.3, once per pair per run). TCK-20260701-SIMQ-EMIT-SOCIAL-MEM. |
| `contract_milestone_completed` | `EventExtractor` — time-gated: 25%/50%/75% of `(expiry_tick − created_tick)` elapsed for ACTIVE contracts; no schema change needed. Once per `(contract_id, label)` per run, attributed to `source_id`. TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE. |

### §3.9 World Dynamics (WorldDynamicsScorer)

Resolved by TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS. One item reclassified as `no_engine_path` (not a wiring gap).

| contract_type | resolved by / notes |
|---|---|
| `ecology_cycle_completed` | `event_extractor.py` — tick % 200 per region |
| `spawn_cadence_fired` | `event_extractor.py` — tick % 50 + non-boss entities_add |
| `threat_evolved` | `event_extractor.py` — trauma_score crossing 25/50/75/100 thresholds |
| `node_recharged` | `event_extractor.py` — resource_node quantity 0 → >0 |
| `camp_constructed` | **No engine path.** `StateUpdate` has no `camps_add` field. `CampService` only evolves existing camps (maturity, raids). Camps are pre-placed at world generation — no dynamic construction occurs during simulation ticks. Implementing this event requires adding a camp placement mechanic first. TCK-20260701-SIMQ-EMIT-CAMP closed. |

---

## §4 P0-A Blocked

Events in `SCORER_REGISTRY` that are not emitted in calibration runs because the subsystem that generates them (campaigns layer, scenario mode) is not active in sandbox_world/dungeon_crawl/wilderness_survival calibration scenarios.

These events DO pass through the translation layer correctly when the subsystem is active and WILL be scored. They are not engine emission gaps — they would appear in full campaign or scenario-mode runs.

| event_type | blocking gate | scorers |
|---|---|---|
| `chronicle_entry_created` | campaigns layer not active in calibration | NarrativeScorer |
| `scenario_objective_completed` | scenario mode not active in calibration | NarrativeScorer |
| `scenario_stalled` | scenario mode not active in calibration | NarrativeScorer |

Note: `boss_spawned` and `raid_party_spawned` are world-infrastructure-gated (require specific entity kinds), but they ARE emitted when those entities spawn. They are classified as `scored` (§1.1) since the engine path exists.

---

## §5 Unscored Intentional

Events emitted by the engine that are deliberately NOT routed to any scorer. No action required.

| event_type | source | reason |
|---|---|---|
| `movement` | MovementEvent | High-volume positional data; not a quality signal |
| `lifecycle` (spawn action) | LifecycleEvent | Spawn passthrough — no quality contract for raw spawn |
| `resource_node_regenerated` | event_extractor | Not a quality signal; node recharge tracked separately |
| `LEGENDARY_ARRIVAL` | LegendaryArrivalEvent | Social consequence event; quality signal not yet defined |
| `KNOWN_TRAITOR_SPOTTED` | KnownTraitorSpottedEvent | Social consequence event; quality signal not yet defined |
| `OLD_DEBT_COLLECTED` | OldDebtCollectedEvent | Social consequence event; quality signal not yet defined |
| `REFINED_UPDATE` | engine/kernel | Kernel internal; pipeline phase marker |
| `GovernorModeChanged` | engine/kernel | Kernel internal; governance state change. Kernel tick-alignment fix (INFRA-258, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER) fixed a comparison bug (`kernel.py:836`) that made this unreachable through the real `Kernel.tick_once()` loop; confirmed firing naturally (63-73 occurrences) in each of the existing `dungeon_crawl_seed{42,123,456}_2000t` / `sandbox_world_seed42_2000t` calibration baselines post-fix. Not scored by any SimQ pillar — infrastructure telemetry only. |
| `TICK_END` | engine/kernel | Kernel internal; tick lifecycle marker |
| `InvariantViolation` (unknown law) | engine/kernel | Falls through conditional translator; unknown law ID has no contract type |
| `belief_contradiction` | engine/pipeline_phases/lead_contradiction | Not yet wired to quality scoring |
| `plan_revision` | campaigns/plan_revision | Campaign planning artifact; not a simulation quality signal |
| `DEFLATION_RISK`, `INFLATION_SPIRAL`, `ECONOMIC_COLLAPSE`, `GOLD_HOARDING` | EconomyHealthMonitor | Defined in events.py but marked deferred — not yet emitted |

---

## §6 Maintenance Notes

- When adding a new `event_type` to `event_extractor.py` or any domain emitter, check this table first.
- If the event should be scored, either: (a) use contract vocabulary directly, or (b) add a `_TRANSLATE_SIMPLE` / `_TRANSLATE_CONDITIONAL` entry to `quality_hub.py` and update this table.
- Engine emission gap events (§3) are the primary expansion surface for future SimQ coverage.
- All engine emission gaps are resolved. Only `camp_constructed` (§3.9) has no viable engine path — camps are pre-placed at world generation, not dynamically constructed during simulation.
- Run `make knowledge-index-update` after any change to docs in this directory.
