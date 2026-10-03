---
status: active
ticket_id: TCK-20260613-DOC-DOMAIN-CONTRACTS
phase: investigation
date: 2026-06-13
---

# Investigation: TCK-20260613-DOC-DOMAIN-CONTRACTS

Source read as of 2026-06-13T11:14:49Z.

---

## 1. adventure domain

**Source:** `src/domains/adventure/` — generator.py, scoring.py, resolver.py, service.py, phase.py, schema.py, mapper.py

**Engine phase:** Phase 3 — `AdventureDecisionPhase.apply()` is the entry point. Invoked on all alive, active heroes each tick unless the hero's current project lock has not expired (`tick < active_proj.lock_until_tick`).

**Owns:**
- `AdventureRouteOption` — candidate route with family, score, blockers, source_opportunity_ids (transient, discarded after tick)
- `AdventureDecisionResult` — selected route + rejected list + proposed ProjectState/ObjectiveState (bridge output)
- `RouteFamily` enum — 13 families (RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, TRAIN_SKILL, TAKE_EASY_QUEST, HUNT_WEAK_ENEMY, GATHER_RESOURCE, SELL_LOOT_FOR_GOLD, ASK_INFORMATION, SCOUT_LOCATION, FORM_PARTY, RETURN_TOWN, DEFER_WITH_REASON)

**Reads:**
- `entity.combat.alive`, `entity.lifecycle.active` — eligibility
- `entity.strategic.current_project_id`, `entity.strategic.projects[id].lock_until_tick` — lock bypass
- `entity.inventory.gold`, `entity.inventory.items` — blocker checks (insufficient_gold, missing_item)
- `entity.self_model.self_awareness.perceived_weaknesses` — structural route generation (RECOVER, ASK_INFORMATION)
- `entity.self_model.needs.active_needs` — urgency scoring
- `entity.identity.personality` (bravery, caution, greed, curiosity, industry, sociability) — personality biases
- `state` (AuthoritativeState) — passed to generator; opportunities come from `src/world/providers/resources.Opportunity`

**Decisions made:**
- Which `RouteFamily` to pursue this tick
- Which candidate to select (highest score among unblocked, deterministic sort: score, confidence, expected_benefit)
- Whether to defer (DEFER_WITH_REASON) when no candidates or all blocked
- Maps selection → `ProjectState` + `ObjectiveState` via `RouteToProjectMapper`

**May mutate (via intents):**
- `entity.strategic` — `StrategicUpdate(projects_add_or_update, current_project_id_set, current_objective_id_set)` via `EntityUpdate`
- `entity.identity.properties` — `last_routing_tick`, `last_routing_family` (debug trace)

**Must NOT mutate:**
- World state, AuthoritativeState directly
- Any other entity's state
- Combat state, inventory (no gold deducted here)

**Domain interactions:**
- Calls `AdventureRouteGenerator.generate()` (internal)
- Calls `AdventureDecisionService.decide()` (internal, invokes AdventureRouteScorer + RouteToProjectMapper)
- Output feeds into `ObjectiveIntentResolver` which produces `ActionIntent` consumed by Phase 5 (information) or the general action resolution layer
- Outputs read by: cooperation domain (shared objectives in PartnerFitEvaluator)

**Tests:**
- `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`
- `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py`
- `tests/unit/domains/adventure/test_phase3_route_families.py`
- `tests/unit/domains/adventure/test_phase3_route_generator.py`
- `tests/unit/domains/adventure/test_phase3_route_scoring.py`
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`
- `tests/perf/test_phase3_adventure_decision_budget.py`

---

## 2. motivation domain

**Source:** `src/domains/motivation/` — evaluator.py (RoleFitEvaluator), resolver.py (DoctrineResolver), service.py (MotivationBiasService)

**Backing implementation:** `src/world/motivation/pressure_resolver.py` (MotivationPressureResolver) — catalog-driven need/drive profile resolution

**Engine phase:** Phase 14 — referenced as "Phase 14" in all file docstrings. No `phase.py` file — invoked inline by other systems that need motivation bias (e.g., adventure scoring, cooperation decision). The motivation domain provides utility services consumed by the cognition layer.

**Owns:**
- `IdentityDoctrine` (from `src/core/cognition`) — class-specific preferred/avoided route tags, combat style bias, cooperation bias; resolved per `class_id` by `DoctrineResolver`
- `RoleFitPreference` scoring results (tag-match floats)
- Multiplier outputs from `MotivationBiasService.compute_bias_multiplier()` — applied to route/action scores

**Reads:**
- `entity.cognition.motivation.doctrine` (preferred_route_tags, avoided_route_tags) — from MotivationBiasService
- `entity.cognition.motivation.values` (survival, pride, curiosity, reward) — value biases
- `RoleFitPreference.weapon_tags / armor_tags / skill_tags / party_role_tags / quest_tags` — from RoleFitEvaluator
- Catalog `need_profile_id`, `drive_profile_id` from `entity.identity.properties` — backing MotivationPressureResolver

**Decisions made:**
- Doctrine resolution: maps `class_id` → `IdentityDoctrine` (warrior, ranger, mage, or default)
- Role fit scoring: tag overlap scoring for weapons, armor, skills, party roles, quests
- Bias multiplier: boost/penalty applied to route scores based on doctrine + value profile

**May mutate (via intents):**
- None — this domain is purely read and compute. Its outputs are passed as scoring multipliers/modifiers to callers (adventure, cooperation). No entity updates produced directly.

**Must NOT mutate:**
- Any entity state
- AuthoritativeState

**Domain interactions:**
- Called by adventure scoring (scoring.py reads personality; motivation service reads doctrine/values — these are complementary layers, not direct calls between domain packages)
- `MotivationPressureResolver` (in `src/world/motivation/`) backs catalog-driven pressure derivation; the domain service (`src/domains/motivation/`) handles in-flight per-tick scoring bias

**Tests:**
- `tests/unit/domains/motivation/test_phase14_bias_service.py`
- `tests/unit/domains/motivation/test_phase14_doctrine_resolver.py`
- `tests/unit/domains/motivation/test_phase14_motivation_models.py`
- `tests/unit/domains/motivation/test_phase14_role_fit_evaluator.py`
- `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`
- `tests/unit/world/test_motivation_pressure_resolver.py` (backing layer)

---

## 3. progression domain (src/domains/progression/)

**Source:** `src/domains/progression/` — phase.py (ProgressionConversionPhase), ledger.py (RewardLedgerService), generator.py (ConversionOptionGenerator), resolver.py (ConversionIntentResolver), schema.py, possession.py (PossessionUnderstandingService), gaps.py (GrowthGapEvaluator), interpretation.py (RewardInterpretationService), selector.py (ConversionDecisionService)

**Backing/split with src/progression/:** `src/progression/leveling.py` (LevelingService) implements the actual mechanics — XP threshold formula `100 * (level ** 1.5)`, level-up execution, AP award (5 per level), skill unlocks, stat recalculation from attributes + equipment. `src/domains/progression/` handles tick-orchestration: evaluates possession understanding, identifies growth gaps, interprets reward ledger entries, generates and selects conversion options, then maps decisions to EntityUpdate intents.

**Engine phase:** Phase 6 — `ProgressionConversionPhase.execute()` receives `(state, update)` and returns a merged `StateUpdate`.

**Owns:**
- `RewardLedgerComponent` — bounded (MAX_ENTRIES=20) event-driven ledger of recently gained XP/gold/items per entity; stored in `entity.identity.properties["reward_ledger"]`
- `PossessionUnderstandingComponent` — subjective value understanding of inventory items (keep/sell/equip/craft priority)
- `GrowthGapReport` — identified progression weaknesses (weapon_gap, repair_gap, material_gap, gold_gap, level_gap)
- `ConversionOption` — scored choices (EQUIP_ITEM, REPAIR_GEAR, SELL_LOOT, CRAFT_ITEM, TRAIN_SKILL, ALLOCATE_AP, etc.)
- `ProgressionDecisionResult` — selected conversion with trace

**Reads:**
- `entity.lifecycle.active`, `entity.combat.alive` — skip check
- `entity.identity.properties["reward_ledger"]` — reward history
- `entity.inventory.*` — items, gold for possession understanding
- `entity.equipment.*` — slot durability for gap evaluation
- `entity.identity.evolution_level`, `entity.identity.evolution_points` — level/XP state (read-only in domain; mutations go through leveling.py)

**Decisions made:**
- What to do with recently acquired rewards (equip, craft, repair, sell, allocate AP, or save)
- Which growth gap is dominant
- Conversion option ranking (capped at 10)

**May mutate (via EntityUpdate intents):**
- `equipment` — `EquipmentUpdate(slot_updates)` for EQUIP_ITEM
- `task` — `TaskUpdate(work_kind_set, payload_set)` for REPAIR_GEAR, CRAFT_ITEM, ASK_ITEM_USE
- `resource_transfers` — `ResourceTransferIntent` for SELL_LOOT
- `identity` — `IdentityUpdate(unspent_ap_delta=-1)` for ALLOCATE_AP
- `identity.properties["last_progression_decision"]` — debug trace

**Must NOT mutate:**
- XP/level directly — this goes through `src/progression/leveling.py` via the authoritative pipeline
- World state, other entities

**Domain interactions:**
- Reads output of world/item systems via inventory state
- `ProgressionConversionPhase.execute()` merges into the ongoing `StateUpdate` passed from the engine
- `LevelingService` (src/progression/) is the authoritative level-up mechanics layer — domain phase reads current level but does not call LevelingService directly

**Tests:**
- `tests/unit/domains/progression/test_phase6_conversion_decision_service.py`
- `tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py`
- `tests/unit/domains/progression/test_phase6_conversion_option_generator.py`
- `tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py`
- `tests/unit/domains/progression/test_phase6_possession_understanding_service.py`
- `tests/unit/domains/progression/test_phase6_progression_boundary.py`
- `tests/unit/domains/progression/test_phase6_progression_events.py`
- `tests/unit/domains/progression/test_phase6_reward_interpretation_service.py`
- `tests/unit/domains/progression/test_phase6_reward_ledger_service.py`
- `tests/integration/domains/progression/test_phase6_progression_conversion_phase.py`
- `tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py`
- `tests/perf/test_phase6_progression_conversion_budget.py`
- `tests/unit/progression/test_leveling_veterancy.py` (src/progression/ layer)
- `tests/unit/progression/test_progression_v2.py`
- `tests/unit/progression/test_rpg_advancement.py`

---

## 4. perception domain

**Source:** `src/domains/perception/` — phase.py (PerceptionUpdatePhase), filter.py (PerceptionFilterService + PerceptionBudget), salience.py (SignalSalienceEvaluator + WorldSignal), service.py (AttentionFocusService)

**Backing implementation:** `src/world/perception/gate.py` (PerceptionGate) — catalog-driven binary perception gating using sense profiles (vision, hearing, smell, magic_sense, life_sense, vibration, social_reading), distance factor, terrain modifier, alertness.

**Engine phase:** Phase 12 — `PerceptionUpdatePhase.run()` takes `(entities, world_signals, tick)` and returns an updated entity list. Note: operates on entity list directly (not via StateUpdate pattern — returns updated EntityState list).

**Owns:**
- `PerceptionModel` (in `src/core/cognition`) — attention_focus, perceived_entities, perceived_resources, perceived_services, perceived_threats, perceived_opportunities, ignored_signals, last_updated_tick
- `PerceptionBudget` — `max_perceived=10`, `max_ignored_to_record=5`
- `WorldSignal` — raw candidate signals with kind, position, base_relevance, danger_level, is_novel

**Reads:**
- `entity.cognition.subjective.self.needs.dominant_need` — attention focus
- `entity.strategic.current_project_id` — project-biased attention
- `entity.cognition.subjective.emotion.fear` — threat salience boost
- `entity.cognition.subjective.emotion.curiosity` — novel signal salience boost
- `entity.navigation.position` — distance penalty in salience computation
- World signals (external input, not from entity state)

**Decisions made:**
- What attention focus tags apply this tick (AttentionFocusService)
- Salience score per signal: `base_relevance + attention_bonus + danger×(1+fear) + novelty×(1+curiosity) - distance×0.01`
- Which signals are perceived vs. ignored (budget cap: top 10 by salience)
- How perceived signals are typed into entities/resources/services/threats/opportunities

**May mutate:**
- `entity.cognition.subjective.perception` — overwrites PerceptionModel in the returned EntityState (via `dataclasses.replace` — immutable pattern)
- No StateUpdate/EntityUpdate types used; updates applied by direct entity replacement in the entity list

**Must NOT mutate:**
- AuthoritativeState directly
- Entity strategic, combat, inventory, identity

**Domain interactions:**
- `PerceptionGate` (src/world/perception/) provides binary can-perceive checks upstream of this domain (catalog sense profiles)
- `KnowledgeModelService` (src/cognition/) assimilates perceived facts into entity knowledge — downstream consumer of perception output
- Adventure domain generator reads perceived opportunities from entity self-model (indirect read of perception output)
- Cooperation domain reads perceived entities/threats (indirect)

**Tests:**
- `tests/unit/domains/perception/test_phase12_attention_focus_service.py`
- `tests/unit/domains/perception/test_phase12_perception_filter_service.py`
- `tests/unit/domains/perception/test_phase12_signal_salience_evaluator.py`
- `tests/integration/domains/perception/test_phase12_perception_phase.py`
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`
- `tests/unit/entity/test_phase12_perception_model.py`
- `tests/unit/world/test_sense_perception_gate.py` (PerceptionGate)

---

## 5. emotion domain

**Source:** `src/domains/emotion/` — emotion_service.py (EmotionUpdateService), habit_service.py (HabitBiasService), opportunity_cost.py (OpportunityCostEvaluator), recovery_service.py (RecoveryReadinessService)

**Engine phase:** Phase 16 — all file docstrings label Phase 16. No `phase.py` — services invoked inline by the cognition hierarchy or scenario tests. Emotion updates are event-driven (triggered by specific outcome events), not every-tick.

**Owns:**
- `EmotionalModel` (in `src/core/cognition`) — fear, confidence, frustration, curiosity, satisfaction, panic, boredom (all float 0.0–1.0)
- `HabitMemory` (in `src/core/cognition`) — `patterns: dict[pattern_id → bias float]`; bias ±0.4 applied to base score
- `RecoveryState` (in `src/core/cognition`) — recent_near_death flag, confidence_loss, retry_readiness, recovery_until_tick, trauma_tags

**Reads:**
- `EmotionalModel` fields — for update_on_event transitions
- `HabitMemory.patterns` — for bias scoring
- `RecoveryState.recent_near_death`, `.retry_readiness`, `.recovery_until_tick` — for readiness checks

**Decisions made:**
- Emotional delta per event (EmotionUpdateService.update_on_event):
  - near_death: fear +0.4, panic +0.5, confidence −0.3
  - easy_win: confidence +0.1, satisfaction +0.1, fear −0.2
  - repeated_failure: frustration +0.3, confidence −0.1
  - new_unknown: curiosity +0.2
  - successful_goal: satisfaction +0.2, frustration −0.3
  - stagnation: boredom +0.1
- Habit bias: record_outcome shifts pattern bias ±0.1 per outcome; apply_habit_bias scales base score by (bias−0.5)×0.4
- OpportunityCostEvaluator: returns float opportunity cost for sell_material (0.1–0.9) and join_party (0.5) actions
- RecoveryReadinessService: determines if entity is ready to retry after near-death (recovery_until_tick or retry_readiness ≥ 0.8)

**May mutate (via returned models):**
- `EmotionalModel` — returned as new instance (immutable replace pattern)
- `HabitMemory` — returned as new instance
- `RecoveryState` — returned as new instance; register_near_death forces 30-tick recovery window

**Must NOT mutate:**
- AuthoritativeState or EntityState fields directly
- Combat stats, inventory, strategic state

**Domain interactions:**
- Perception domain salience evaluator reads `entity.cognition.subjective.emotion.fear` and `.curiosity` — emotion state feeds perception priority
- Cooperation domain (PartnerFitEvaluator) implicitly reads emotion via trust/grudge state — indirect dependency
- Adventure scoring reads personality (caution, bravery) which partially proxies for emotional state

**Tests:**
- `tests/unit/domains/emotion/test_phase16_emotion_update_service.py`
- `tests/unit/domains/emotion/test_phase16_emotional_model.py`
- `tests/unit/domains/emotion/test_phase16_habit_bias_service.py`
- `tests/unit/domains/emotion/test_phase16_habit_memory_model.py`
- `tests/unit/domains/emotion/test_phase16_opportunity_cost_evaluator.py`
- `tests/unit/domains/emotion/test_phase16_recovery_readiness_service.py`
- `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py`

---

## 6. commitment domain

**Source:** `src/domains/commitment/` — abandonment.py (AbandonmentEvaluator), impact.py (CommitmentReputationRouteImpact), pressure.py (CommitmentPressureService), reputation.py (ReputationUpdateService)

**Engine phase:** Phase 15 — all file docstrings label Phase 15. No `phase.py` — four utility services invoked inline by the cognition/cooperation layer. No orchestrator phase class.

**Owns:**
- `CommitmentEntry` (in `src/core/cognition`) — commitment records with kind, target_id, strength, deadline_tick; accessed via `entity.cognition.commitment.active_commitments`
- `PublicReputationProfile` (in `src/core/cognition`) — labels dict (`reliable`, `betrayer`, `camp_clearer`, `heroic`)
- Abandonment decision record: `{is_betrayal, penalty, reason}` (plain dict, ephemeral)
- Commitment pressure float (0.0–1.0)

**Reads:**
- `entity.cognition.commitment.active_commitments` — active commitment entries for pressure/impact
- `entity.combat.hp`, `entity.combat.max_hp` — HP ratio for abandonment and pressure scaling
- `CommitmentEntry.strength`, `.deadline_tick` — for pressure computation
- `entity.identity.personality` (implicit: greed) — abandonment evaluator checks `is_greed_driven`
- `PublicReputationProfile.labels` — updated by ReputationUpdateService

**Decisions made:**
- `CommitmentPressureService.compute_pressure()`: pressure = strength + deadline urgency, scaled by HP (below 0.2 HP: pressure × 0.1)
- `AbandonmentEvaluator.evaluate_abandonment()`: survival abandon (HP < 20% → not betrayal), greedy desertion under combat (betrayal, penalty 0.8), voluntary quit (penalty 0.2)
- `CommitmentReputationRouteImpact.apply_route_bias()`: boosts route score by commitment strength × 0.5 if route matches commitment kind/target
- `ReputationUpdateService.process_witnessed_event()`: updates reputation labels on witnessed events (escort→reliable, betrayal→betrayer+reliable−, camp_clear→camp_clearer+heroic)

**May mutate (via returned models):**
- `PublicReputationProfile` — returned as new instance (immutable replace)
- Score floats returned to callers for integration

**Must NOT mutate:**
- AuthoritativeState or EntityState directly
- Commitment entries are read — not created or removed by this domain (commitment lifecycle managed authoritatively)

**Domain interactions:**
- Cooperation domain uses CommitmentReputationRouteImpact for partner fit scoring (`apply_partner_fit_bias`)
- Adventure scoring could use commitment pressure as urgency modifier (integration point, not currently direct)

**Tests:**
- `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`
- `tests/unit/domains/commitment/test_phase15_commitment_pressure.py`
- `tests/unit/domains/commitment/test_phase15_reputation_update.py`
- `tests/unit/domains/commitment/test_phase15_route_impact.py`
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`

---

## 7. cooperation domain

**Source:** `src/domains/cooperation/` — phase.py (CooperationPhase), evaluators.py (HelpNeedEvaluator, PartnerFitEvaluator), events.py (observability events), postures.py (CooperationPosture enum + definitions), services.py (CooperationDecisionService, CooperationIntentBridge, PartyObjectiveAlignmentService, PartyCohesionService, CooperationLearningService), providers.py (PartnerCandidateProvider + CandidateBudget)

**Engine phase:** Phase 7 — `CooperationPhase.execute()` receives `(state, update)` and returns merged `StateUpdate`. Feature-flagged (`social_cooperation_enabled`).

**Owns:**
- `CooperationDecisionResult` — selected posture + partner_id + fit_score + rejected_partners + trace
- `HelpNeed` — need record with key, severity, reason, required_support_tags, acceptable_postures
- `PartnerFitReport` — fit_score, trust_score, capability_match, objective_alignment, risk per candidate
- 12 `CooperationPosture` values: SOLO, REQUEST_HELP, OFFER_HELP, JOIN_PARTY, HIRE_SUPPORT, FOLLOW_LEADER, LEAD_PARTY, AVOID_PARTNER, DEFER_NO_PARTNER, ABANDON_PARTY, RESCUE_ALLY, GUARD_ALLY
- Observability events: HelpNeedDetectedEvent, PartnerSelectedEvent, PartnerRejectedEvent, CooperationDecisionSelectedEvent, CooperationOutcomeLearnedEvent

**Reads:**
- `entity.strategic.current_objective_id`, `.current_project_id`, `.projects`, `.beliefs["combat_risk"]`, `.turning_points` — for help need evaluation
- `entity.combat.hp`, `.max_hp`, `.tactical_role` — health/role for needs and partner capability
- `entity.navigation.target`, `.region_id` — guide need detection
- `entity.inventory.gold` — carry/hire cost checks
- `entity.social.trust_history`, `.familiarity_history`, `.bonds`, `.grudge_history` — partner trust
- `entity.identity.personality` (sociability, bravery, caution, greed) — solo vs coop score
- `entity.identity.group_id` — skip if not in group and no help need
- `entity.identity.role` — hireling detection
- `state.groups` — party cohesion checks

**Decisions made:**
- Help need detection (4 triggers: high combat risk/near-death, critical HP < 30%, unknown region, heavy gold load)
- Partner scoring: fit = trust×0.35 + capability×0.3 + alignment×0.2 + (1−risk)×0.15 − poor_penalty
- Posture selection: SOLO if no needs; REQUEST_HELP or HIRE_SUPPORT if good partner + coop_score > solo_score; DEFER_NO_PARTNER if need too severe but no partner
- Party cohesion: STABLE / NEEDS_REGROUP / MEMBER_ABANDONING / LEADER_LOST
- Cooperation learning: trust_delta/grudge_delta from outcome type (success +0.08, rescue +0.22, abandoned −0.25, betrayal −0.75)

**May mutate (via EntityUpdate intents):**
- `entity.strategic` — `StrategicUpdate(blockers_add_or_update)` for DEFER_NO_PARTNER; `StrategicUpdate(contracts_add_or_update)` for REQUEST_HELP/HIRE_SUPPORT
- `entity.social` — `SocialUpdate(trust_delta)` for party cohesion collapse (trust −0.25 for leader loss/abandonment)
- `entity.identity.properties["last_cooperation_decision"]` — debug trace
- `entity.identity.properties["proposed_cooperation_contract"]` — contract ID trace
- `entity.timeline` — appends observability events (bounded by timeline length < 150)

**Must NOT mutate:**
- AuthoritativeState directly
- Commitment entries, emotion state, perception

**Domain interactions:**
- Reads social state (trust, grudge, bonds) — social_systems layer owns the durable update
- Uses `ContractService` from `src/systems/social_systems/contracts` for contract creation (cooperation → social systems boundary crossing via explicit import inside method body)
- `CooperationLearningResult` returned to caller for application (not applied inline)
- `entity.timeline.append()` — NOTE: this is a DIRECT mutation of a mutable list on entity. This is a known architectural issue in the current code — timeline events are appended in-place rather than via an update intent.

**Tests:**
- `tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_events.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_learning.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_postures.py`
- `tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py`
- `tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py`
- `tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py`
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`
- `tests/perf/test_phase7_social_cooperation_budget.py`

---

## 8. world_emergence domain

**Source:** `src/domains/world_emergence/` — phase.py (WorldEmergencePhase), aggregators.py (WorldEventAggregator), models.py (RegionalPressureModel, ScarcityModel, ServiceStatePressureModel), schema.py, services.py (WorldOpportunityPressureService, DynamicQuestSeedService, RumorSeedService, WorldToEntitySignalBridge)

**Engine phase:** Phase 8 — `WorldEmergencePhase.execute()` receives `(state, update, recent_events)` and returns `(StateUpdate, WorldEmergenceResult)`. Feature-flagged (`world_emergence_enabled`).

**Owns:**
- `WorldEvent` — typed event record (category, tick, region_id, subject, severity)
- 15 `WorldEventCategory` values: ENTITY_DEATH, NEAR_DEATH, RESOURCE_HARVESTED, RESOURCE_DEPLETED, QUEST_COMPLETED, QUEST_FAILED, CAMP_CLEARED, CAMP_RAID, SHOP_STOCK_DEPLETED, SERVICE_UNAVAILABLE, REGION_ENTERED, REGION_AVOIDED, RUMOR_CONFIRMED, RUMOR_CONTRADICTED, PARTY_ABANDONED
- `WorldEventAggregate` — grouped summary (region_id, category, subject, count, severity_sum, first/last_tick)
- `RegionalPressure` — intensity 0.0–1.0 per region per pressure_kind (danger, resource, camp)
- `ResourceScarcitySignal` — per-region per-resource availability + trend
- `WorldOpportunityPressure` — actionable opportunity derived from pressures/scarcity
- `QuestSeed` — deterministic quest seed (MD5 of opp_id + tick, capped at 10)
- `RumorSeed` — lower-certainty information seed (capped at 10)
- `ServicePressure` — blacksmith material shortage, healer demand, guild threat pressure, shop supply disruption
- `WorldEmergenceResult` — aggregated output bundle

**Reads:**
- `recent_events` — bounded 100-tick window of WorldEvent records
- `state.regions` — all active regions (trauma_score, hazard_level)
- `entity.lifecycle.active`, `entity.combat.alive` — for signal bridge
- `entity.navigation.position`, `.region_id` — spatial filtering for signal exposure

**Decisions made:**
- Aggregate events by (region_id, category, subject) within 100-tick window
- Regional danger pressure: `death_count×0.15 + sev×0.05 + quest_fail×0.08 + raid×0.25 − clear×0.20 + trauma/100 + hazard×0.2`
- Resource scarcity: `harvest×0.08 + depletion×0.25` per (region, resource_type)
- Camp pressure: raids − clears
- QuestSeed generation: deterministic ID from MD5(opp_id + tick)
- Rumor generation: danger (intensity > 0.2) and scarcity (level > 0.3)
- Service pressures: iron scarcity → blacksmith material; deaths → healer demand; max_danger > 0.2 → guild threat; > 0.4 → shop supply chain
- Entity signal exposure: spatial filtering — direct observation in same region, rumor via town channel

**May mutate (via EntityUpdate intents):**
- `entity.identity.properties["exposed_world_signals"]` — list of exposure dicts
- `entity.identity.properties["force_route_reevaluation"]` — boolean flag (set when danger > 0.2)
- `update.world_updates` — world-level update dict (currently populated but content unspecified in phase)
- `metric_counters` — world_emergence_ms, aggregates_generated

**Must NOT mutate:**
- Region trauma_score or hazard_level directly (reads only)
- Entity combat, strategic, inventory state

**Domain interactions:**
- Outputs `WorldEmergenceResult` consumed by adventure domain generator (route scoring inputs)
- QuestSeeds and RumorSeeds feed into quest/information systems (exact consumer not traced in this domain's code)
- WorldToEntitySignalBridge pushes signals into entity properties → adventure scoring reads `force_route_reevaluation`

**Tests:**
- `tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py`
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`
- `tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py`
- `tests/unit/domains/world_emergence/test_phase8_scarcity_model.py`
- `tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py`
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py`
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py`
- `tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py`
- `tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py`
- `tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py`
- `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py`
- `tests/integration/scenarios/test_phase8_world_emergence_scenarios.py`
- `tests/perf/test_phase8_world_emergence_budget.py`

---

## 9. memory domain

**Source:** `src/domains/memory/` — phase.py (MemoryUpdatePhase), attribution.py (CausalAttributionService), spatial_update.py (SpatialMemoryUpdateService)

**Backing implementation:** `src/cognition/knowledge_model.py` (KnowledgeModelService) — assimilates InformationResponse into entity-owned KnowledgeModelComponent (`entity.self_model.knowledge`). The knowledge model is the informational layer; causal and spatial memory are the experiential layer.

**Engine phase:** Phase 13 — `MemoryUpdatePhase.run()` takes `(entities, tick, trigger_event)` and returns updated entity list. Operates directly on entity list (same pattern as perception — not via StateUpdate). Calls `TemporalPressureService` from `src/domains/time/`.

**Owns:**
- `CausalMemory` (in `src/core/cognition`) — bounded list of `CausalMemoryEntry` records with `capacity` enforcement (evict oldest when full)
- `CausalMemoryEntry` — event_id, event_kind, interpreted_causes, confidence (0.8), future_advice, tick, region_id
- `SpatialMemory` (in `src/core/cognition`) — visited_regions (RegionVisitMemory: visit_count, familiarity 0.0→1.0 +0.15/visit, is_dangerous), known_resource_sites, route_memory, failed_search_memory
- `TemporalModel.urgency` — recalculated each tick via TemporalPressureService

**Reads:**
- `entity.lifecycle.active`, `entity.combat.alive` — skip check
- `entity.cognition.memory.causal.entries`, `.capacity` — for bounded append
- `entity.cognition.memory.spatial.visited_regions` — for visit/danger updates
- `entity.navigation.region_id` — current region for spatial update
- `entity.combat.hp`, `.max_hp`, `entity.stamina.current`, `entity.equipment.durability` — for causal attribution of combat_loss
- `trigger_event` dict — optional: entity_id, kind, id, region_id

**Decisions made (CausalAttributionService):**
- combat_loss causes: low_health (HP < 30%), low_stamina (< 20), damaged_weapon (durability < 20%), else strong_enemy
- failed_search: wrong_location + bad_rumor
- failed_craft: missing_material + unknown_recipe
- party_abandoned: grudge_decay + cohesion_lost
- Advice generated per cause

**Decisions made (SpatialMemoryUpdateService):**
- update_region_visit: familiarity = min(1.0, old + 0.15), visit_count++
- mark_region_danger: sets is_dangerous flag on RegionVisitMemory
- record_resource_site: registers ResourceSiteMemory

**May mutate:**
- `entity.cognition.memory.causal` — via immutable replace, returned in entity list
- `entity.cognition.memory.spatial` — via immutable replace
- `entity.cognition.subjective.time.urgency` — updated via TemporalPressureService

**Must NOT mutate:**
- AuthoritativeState directly
- Entity strategic, combat, inventory

**Domain interactions:**
- `KnowledgeModelService` (src/cognition/) is the knowledge assimilation layer — memory domain handles experiential causal/spatial records, knowledge model handles assimilated facts/unknowns
- `TemporalPressureService` (src/domains/time/) called from MemoryUpdatePhase for urgency recalculation
- Adventure domain generator reads `entity.self_model.knowledge` (outputs of KnowledgeModelService) for information-based routing
- Perception domain (Phase 12) runs before memory (Phase 13); perception output feeds into memory trigger events indirectly

**Tests:**
- `tests/unit/domains/memory/test_phase13_causal_attribution_service.py`
- `tests/unit/domains/memory/test_phase13_spatial_memory_update_service.py`
- `tests/integration/domains/memory/test_phase13_memory_update_phase.py`
- `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`
- `tests/unit/entity/test_phase13_temporal_model.py`
- `tests/unit/strategic/test_narrative_memory.py`

---

## Progression Split Confirmation

Two distinct layers handle progression:

**`src/domains/progression/`** — tick orchestration domain (Phase 6):
- Evaluates what to DO with recently acquired rewards (conversion decision loop)
- Maintains the `RewardLedgerComponent` (bounded event log of XP/gold/items received)
- Identifies growth gaps (GrowthGapEvaluator)
- Generates and selects conversion options (equip, craft, sell, repair, allocate AP)
- Produces EntityUpdate intents (EquipmentUpdate, TaskUpdate, ResourceTransferIntent, IdentityUpdate)
- Does NOT implement XP thresholds, level-up logic, stat recalculation, or skill unlocks

**`src/progression/leveling.py`** — authoritative mechanics layer (LevelingService):
- Implements XP threshold formula: `100 * (level ** 1.5)` — VERIFIED v2: xp_threshold_formula
- Executes level-up: increments level, deducts XP cost, awards 5 AP per level
- Unlocks skills at level thresholds (power_strike@2, swift_reflexes@5, fireball@10)
- Derives combat stats from attributes + equipment + skills + traits
- Enforces Level 99 cap — VERIFIED v2: level_cap_enforced
- Called from the authoritative pipeline when XP gain events arrive — NOT from the domain phase

An agent searching for "how leveling works" must be directed to `src/progression/leveling.py`. An agent searching for "what does Phase 6 do" must look at `src/domains/progression/phase.py`.

---

## Format Model Notes

The campaigns_contract.md uses these sections:
- Purpose
- [Domain] Lifecycle or Pipeline
- Key schema/types with field descriptions
- Determinism Contract (where applicable)
- Boundary: [Domain] vs [Other] table
- Constraints

Each of the 9 new docs will follow the same structure with the 9 required questions answered:
1. Owns
2. Reads as input
3. Decisions
4. May mutate (and apply path)
5. Must NOT mutate
6. Pipeline phase
7. Domain interactions
8. Test protection
9. Extension rules

---

## Edge Cases and Architecture Flags

1. **Cooperation phase direct timeline mutation**: `entity.timeline.append()` in CooperationPhase is a direct mutable list append — not routed through an update intent. This is a known pattern (same exists in other phases) but should be noted in the contract.

2. **Perception and memory return entity lists, not StateUpdates**: Both PerceptionUpdatePhase and MemoryUpdatePhase use the `list[EntityState]` return pattern (immutable replaces via dataclasses.replace) rather than the `StateUpdate` pattern. This differs from adventure (Phase 3) and cooperation (Phase 7) and progression (Phase 6) which use StateUpdate. Both patterns are authoritative — the entity list is the state.

3. **Motivation domain has no phase file**: The motivation domain is purely a set of utility services (evaluator, resolver, service). It is called from within other phases' scoring logic, not as a named phase step.

4. **Commitment and emotion domains similarly have no phase.py**: Both are utility service collections. Commitment runs as Phase 15 inline; emotion as Phase 16 inline.

5. **PerceptionGate (src/world/perception/)**: Is a catalog-driven binary gating layer that runs BEFORE the PerceptionUpdatePhase (Phase 12) in the world pipeline. The domain docs should cross-link both layers clearly.
