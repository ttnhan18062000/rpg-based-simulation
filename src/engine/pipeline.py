# Compliance IDs: API-002, INFRA-178, PERF-007, PERF-012, SOC-200, STRAT-200
# Compliance IDs: INFRA-001, INFRA-002, SOC-182, SOC-186, TOWN-004, TOWN-008, TOWN-147, TOWN-148, TOWN-149, TOWN-155, TOWN-164, TOWN-165, TOWN-166, TOWN-167
# Compliance IDs: INFRA-001, INFRA-002
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional, Any, Set
import time
from dataclasses import replace
import logging

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate
    from src.engine.cadence import SystemCadence

from src.engine.cadence import SystemCadence as DefaultCadence, should_run
from src.engine.blacksmith import BlacksmithSystem
from src.engine.interaction import InteractionSystem
from src.engine.legality import LegalityServiceV2
from src.engine.sabotage import BuildingSabotageSystem
from src.engine.town_resolution import TownResolutionSystem
from src.engine.world_dynamics import WorldDynamicsSystem
from src.engine.shop import ShopSystem
from src.engine.evolution import EvolutionSystem
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.lifecycle import LifecycleSystem
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
from src.systems.world_systems.generator import EntityGenerator
from src.engine.compactor import StateUpdateCompactor
from src.engine.phase_graph import PhaseDependencyGraph

logger = logging.getLogger(__name__)

class AuthoritativeApplyPipeline:
    """
    Law: The pipeline is the singular bottleneck for authoritative truth.
    Proof: All mutations must pass through refine() and be bit-identical.
    VERIFIED v2: AuthoritativeApplyPipeline (Milestone D)
    """

    @staticmethod
    def refine(state: AuthoritativeState, update: StateUpdate, cadence: SystemCadence | None = None, force_full_scan: bool = False) -> StateUpdate:
        """
        Singular entry point for authoritative state transition refinement.
        Logic ID: TOWN-147 (Every update enters the same pipeline)
        Logic ID: TOWN-148 (No AI/system mutates world state directly)
        Orchestrates systems in the correct causal order across 17 distinct phases.
        """
        if force_full_scan:
             update = replace(update, force_full_scan=True)
        if getattr(state, "_force_full_scan", False):
             update = replace(update, force_full_scan=True)

        cadence = cadence or DefaultCadence(strategic_intelligence=1)

        # M7 Optimization: Use a builder to avoid redundant set cloning.
        from src.core.dirty import DirtySetBuilder
        dirty_builder = DirtySetBuilder(update.dirty_set)
        if update.dirty_set is None:
            dirty_builder.mark_from_update(state, update)

        # M8 Optimization: Ensure per-tick stable occupancy snapshot is initialized.
        from src.engine.occupancy_snapshot import OccupancySnapshot
        if getattr(state, "occupancy_snapshot", None) is None or getattr(state, "occupancy_snapshot").tick != state.tick:
            object.__setattr__(state, "occupancy_snapshot", OccupancySnapshot.from_state(state))

        costs = {}

        # M10 Feature flags manager
        from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
        ff_manager = FeatureFlagManager()
        # Retrieve overrides if configured on the state/profile
        if getattr(state, "rollout_profile", None) is not None:
             # Merge profile flags
             for flag_name in state.rollout_profile.enabled_phases:
                 ff_manager.set_flag_mode(flag_name, FeatureMode.ON)
             for flag_name in state.rollout_profile.shadow_phases:
                 ff_manager.set_flag_mode(flag_name, FeatureMode.SHADOW)
             for flag_name in state.rollout_profile.disabled_phases:
                 ff_manager.set_flag_mode(flag_name, FeatureMode.OFF)

        # Allow simple direct state config flags
        if getattr(state, "feature_flags", None) is not None:
             for k, v in state.feature_flags.items():
                 ff_manager.set_flag_mode(k, v)

        # Allow mapping flags from state.pressure_signals dictionary
        if getattr(state, "pressure_signals", None) is not None:
             for k, v in state.pressure_signals.items():
                 if k.startswith("ENABLE_"):
                     # If pressure signal is non-zero, treat as active (ON)
                     mode = FeatureMode.ON if v > 0.0 else FeatureMode.OFF
                     ff_manager.set_flag_mode(k, mode)

        # --- Phase 1: Trust & Validity ---
        t_start = time.perf_counter_ns()
        update, compaction_metrics = StateUpdateCompactor.compact_with_metrics(state, update)
        metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        metric_counters["raw_entity_updates"] = compaction_metrics.raw_entity_updates
        metric_counters["compacted_entity_updates"] = compaction_metrics.compacted_entity_updates
        update = replace(update, metric_counters=metric_counters)

        def run_phase(phase_name: str, upd: StateUpdate, phase_fn, feature_flag: Optional[str] = None) -> StateUpdate:
            # 1. Evaluate Feature Rollout Mode
            mode = FeatureMode.ON
            if feature_flag:
                mode = ff_manager.get_flag_mode(feature_flag)

            if mode == FeatureMode.OFF:
                metric_counters[f"skip_{phase_name}"] = metric_counters.get(f"skip_{phase_name}", 0) + 1
                return upd

            # 2. Evaluate skip dependency policies
            if PhaseDependencyGraph.should_run_phase(phase_name, state, upd, cadence):
                metric_counters["phase_runs"] = metric_counters.get("phase_runs", 0) + 1
                metric_counters[f"run_{phase_name}"] = metric_counters.get(f"run_{phase_name}", 0) + 1
                
                phase_upd = phase_fn(upd)
                
                # 3. Strictly enforce SHADOW mode: discard all aspect mutations from update
                if mode == FeatureMode.SHADOW:
                    # In shadow mode, we return a copy with original entity/world/group updates,
                    # but we keep metric counters and diagnostic telemetry
                    shadow_upd = replace(
                        upd,
                        metric_counters=phase_upd.metric_counters,
                        sub_phase_costs=phase_upd.sub_phase_costs
                    )
                    return shadow_upd
                return phase_upd
            else:
                metric_counters["phase_skips"] = metric_counters.get("phase_skips", 0) + 1
                metric_counters[f"skip_{phase_name}"] = metric_counters.get(f"skip_{phase_name}", 0) + 1
                return upd

        update = run_phase("trust_boundary", update, lambda u: AuthoritativeApplyPipeline._strip_untrusted_world_effects(u))
        update = run_phase("actor_validity", update, lambda u: AuthoritativeApplyPipeline._resolve_actor_validity(state, u))

        costs["trust_validity"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 2: Self Model Cognition ---
        t_start = time.perf_counter_ns()
        from src.cognition import SelfModelUpdatePhase
        update = run_phase("self_model", update, lambda u: SelfModelUpdatePhase.apply(state, u), "ENABLE_SELF_MODEL_COGNITION")
        costs["self_model"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 5: Belief Assimilation ---
        t_start = time.perf_counter_ns()
        from src.domains.information.phase import InformationBeliefPhase
        # Retrieve dynamic profiles/pending responses from state or context if present
        source_profiles = getattr(state, "information_source_profiles", [])
        pending_resps = getattr(state, "pending_information_responses", [])
        update = run_phase("information_belief", update, lambda u: u.merge(InformationBeliefPhase.apply(state, source_profiles, pending_resps)), "ENABLE_BELIEF_ASSIMILATION")
        costs["information_belief"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 6: Information Intent Execution (self-model query-routing) ---
        t_start = time.perf_counter_ns()
        from src.engine.pipeline_phases.information_intent_execution import InformationIntentExecutionPhase
        update = run_phase(
            "information_intent_execution", update,
            lambda u: InformationIntentExecutionPhase.execute(state, u),
            "ENABLE_INFORMATION_INTENT_EXECUTION",
        )
        costs["information_intent_execution"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 7: Social Cooperation ---
        t_start = time.perf_counter_ns()
        from src.domains.cooperation.phase import CooperationPhase
        update = run_phase("cooperation", update, lambda u: CooperationPhase.execute(state, u), "ENABLE_SOCIAL_COOPERATION")
        costs["cooperation"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 2: Contracts & Production ---
        t_start = time.perf_counter_ns()
        update = run_phase("contracts", update, lambda u: AuthoritativeApplyPipeline._resolve_contract_expirations(state, u))
        update = run_phase("blacksmith", update, lambda u: BlacksmithSystem.enforce(state, u))
        costs["contracts_production"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 8b: Faction Decision (runs before adventure routing) ---
        # Must run every tick (no cadence gate) so faction_directives is stable input for scoring.
        t_start = time.perf_counter_ns()
        from src.engine.faction_decision import FactionDecisionPhase, FactionAwarenessService
        faction_directives: list = FactionDecisionPhase.execute(state, policy=None)
        costs["faction_decision"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 8c: Faction Awareness (tension from last-tick resource events) ---
        # recent_world_events reflects last tick's window — one-tick lag is inherent (state frozen).
        t_start = time.perf_counter_ns()
        from src.core.updates import StateUpdate as _SU_fa
        _recent_events = getattr(state, "recent_world_events", [])
        update = run_phase(
            "faction_awareness", update,
            lambda u: u.merge(_SU_fa(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events))),
        )
        costs["faction_awareness"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 8d: Diplomatic State Machine + Alliance Generation (E53Bc/Bd) ---
        t_start = time.perf_counter_ns()
        from src.domains.faction.diplomatic_state_machine import (
            compute_transitions, compute_common_enemy_pairs, events_from_transitions,
        )
        _diplo_transition_updates = compute_transitions(state.factions)
        _diplo_alliance_updates: list = []
        # Alliance generation: factions with a common hostile enemy get an AllianceProposal
        if state.factions:
            from src.engine.faction_decision import AllianceProposal
            from src.domains.faction.diplomatic_actions import handle as _diplo_handle
            for _fa_id, _fb_id, _ps in compute_common_enemy_pairs(state.factions):
                _diplo_alliance_updates.extend(_diplo_handle(
                    AllianceProposal(
                        faction_id=_fa_id, directive_kind="ALLIANCE_PROPOSAL",
                        from_faction=_fa_id, to_faction=_fb_id, proposer_strength=_ps,
                    ),
                    state.factions,
                ))
        _diplo_updates = _diplo_transition_updates + _diplo_alliance_updates
        _diplo_world_events = events_from_transitions(
            _diplo_transition_updates, _diplo_alliance_updates, state.factions, state.tick,
        )
        from src.core.updates import StateUpdate as _SU_dt
        update = run_phase(
            "diplomatic_transitions", update,
            lambda u: u.merge(_SU_dt(faction_updates=_diplo_updates, world_events_add=_diplo_world_events)),
        )
        costs["diplomatic_transitions"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 8e: Military Conflict Phase (E53Ca) ---
        t_start = time.perf_counter_ns()
        from src.engine.military_conflict import MilitaryConflictPhase
        from src.core.updates import StateUpdate as _SU_mc
        update = run_phase(
            "military_conflict", update,
            lambda u: u.merge(MilitaryConflictPhase.execute(state)),
        )
        costs["military_conflict"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 3: Adventure Routing ---
        t_start = time.perf_counter_ns()
        from src.domains.adventure.phase import AdventureDecisionPhase
        update = run_phase(
            "adventure_decision", update,
            lambda u: u.merge(AdventureDecisionPhase.apply(
                state,
                faction_directives=faction_directives,
                factions=state.factions,
            )),
            "ENABLE_ADVENTURE_ROUTING",
        )
        costs["adventure_decision"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 3: Action & Movement Routing ---
        t_start = time.perf_counter_ns()
        update = run_phase("action_routing", update, lambda u: AuthoritativeApplyPipeline._route_action_intent(state, u))
        update = run_phase("position_swaps", update, lambda u: AuthoritativeApplyPipeline._resolve_position_swaps(state, u))
        update = run_phase("movement_routing", update, lambda u: AuthoritativeApplyPipeline._route_movement_intent(state, u))
        costs["locomotion"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 4: Combat Engagement ---
        t_start = time.perf_counter_ns()
        from src.domains.combat_engagement.phase import CombatEngagementPhase
        update = run_phase("combat_engagement", update, lambda u: CombatEngagementPhase.apply(state), "ENABLE_COMBAT_ENGAGEMENT")
        costs["combat_engagement"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 4: Interaction & World Effects ---
        t_start = time.perf_counter_ns()
        # InteractionSystem and TownResolution need an accurate dirty set
        dirty_builder.mark_from_update(state, update)
        built_dirty = dirty_builder.build()
        update = update.replace(dirty_set=built_dirty)
        if getattr(state, "movement_cache", None) is not None:
            state.movement_cache.invalidate_for_dirty(built_dirty)
        
        update = run_phase("interaction_routing", update, lambda u: AuthoritativeApplyPipeline._route_interaction_intent(state, u))
        update = run_phase("interaction_enforcement", update, lambda u: InteractionSystem.enforce(state, u))
        update = run_phase("building_sabotage", update, lambda u: BuildingSabotageSystem.resolve(state, u))
        costs["interaction"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 5: Governance & Ecology ---
        t_start = time.perf_counter_ns()
        update = run_phase("town_resolution", update, lambda u: TownResolutionSystem.resolve(state, u, cadence=cadence))

        # Gold Sink (E33C): inject fee/tax intents on INFLATION_SPIRAL windows.
        # Runs after town_resolution so shop-service context is already resolved.
        from src.engine.gold_sink import GoldSinkSystem
        update = run_phase("gold_sink", update, lambda u: GoldSinkSystem.apply(state, u, cadence))

        generator = EntityGenerator(state.seed + state.tick)
        generator._last_id = state.next_entity_id - 1
        update = run_phase("world_dynamics", update, lambda u: WorldDynamicsSystem.resolve_dynamics(state, u, generator, cadence=cadence))
        costs["governance_ecology"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 8: World Emergence ---
        t_start = time.perf_counter_ns()
        from src.domains.world_emergence.phase import WorldEmergencePhase
        recent_world_events = getattr(state, "recent_world_events", [])
        update = run_phase("world_emergence", update, lambda u: WorldEmergencePhase.execute(state, u, recent_world_events)[0], "ENABLE_WORLD_EMERGENCE")
        costs["world_emergence"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 6: Economy & Evolution ---
        # Refresh dirty set to capture resource_transfers added by town_resolution and world_dynamics
        t_start = time.perf_counter_ns()
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
        update = run_phase("quest_rewards", update, lambda u: AuthoritativeApplyPipeline._resolve_quest_rewards(state, u))

        # TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING: guild-visit arrival detection + completion.
        # Placed adjacent to quest_rewards — new project completion/lead generation is
        # conceptually part of this phase group, not earlier trust/validity phases.
        from src.engine.pipeline_phases.guild_visit import GuildVisitPhase
        update = run_phase("guild_visit", update, lambda u: GuildVisitPhase.resolve(state, u), "ENABLE_GUILD_QUEST_GENERATION")

        update = run_phase("shop", update, lambda u: ShopSystem.enforce(state, u))

        # E42C: Paid information transactions — inject intents before resolver runs.
        from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
        update = run_phase("paid_information", update, lambda u: PaidInformationTransactionSystem.enforce(state, u))

        update = run_phase("resource_transactions", update, lambda u: AuthoritativeApplyPipeline._resolve_resource_transactions(state, u))
        # Refresh dirty set to capture reward_upd set by resource_transactions (XP rewards)
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
        update = run_phase("evolution", update, lambda u: EvolutionSystem.evaluate(state, u))
        costs["economy"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Enhanced RPG Phase 6: Progression & Conversion ---
        t_start = time.perf_counter_ns()
        from src.domains.progression.phase import ProgressionConversionPhase
        update = run_phase("progression_conversion", update, lambda u: ProgressionConversionPhase.execute(state, u), "ENABLE_PROGRESSION_EVOLUTION")
        costs["progression_conversion"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 7: Cognitive & Final Integrity ---
        t_start = time.perf_counter_ns()
        # Refresh dirty set before final strategic pass
        t0 = time.perf_counter_ns()
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
        t1 = time.perf_counter_ns()
        
        update = run_phase("strategic_intelligence", update, lambda u: StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))
        t2 = time.perf_counter_ns()
        update = run_phase("near_death_hardening", update, lambda u: AuthoritativeApplyPipeline._apply_near_death_hardening(state, u))
        t3 = time.perf_counter_ns()
        update = run_phase("occupancy_resolution", update, lambda u: AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, u))
        t4 = time.perf_counter_ns()
        update = run_phase("lifecycle", update, lambda u: LifecycleSystem.resolve_lifecycle(state, u))
        t5 = time.perf_counter_ns()
        update = run_phase("groups", update, lambda u: AuthoritativeApplyPipeline._resolve_groups(state, u))
        t6 = time.perf_counter_ns()
        
        from src.systems.social_systems.contracts import ContractService
        update = run_phase("active_contracts", update, lambda u: ContractService.process_active_contracts(state, u))
        update = run_phase("expired_offers", update, lambda u: ContractService.reap_expired_offers(state, u))
        
        update = run_phase("capacity_enforcement", update, lambda u: CapacityEnforcementPhase.enforce(state, u))
        t7 = time.perf_counter_ns()
        
        # Final dirty set for result application
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
        t8 = time.perf_counter_ns()
        costs["final_integrity"] = (t8 - t_start) / 1e6
        if state.tick in (10, 20, 30, 40, 50) and len(state.entities) >= 500:
            logger.debug(f"[Tick {state.tick}] final_integrity breakdown (ms): dirty1={(t1-t0)/1e6:.2f}, fused={(t2-t1)/1e6:.2f}, hardening={(t3-t2)/1e6:.2f}, occupancy={(t4-t3)/1e6:.2f}, lifecycle={(t5-t4)/1e6:.2f}, groups={(t6-t5)/1e6:.2f}, capacity={(t7-t6)/1e6:.2f}, dirty2={(t8-t7)/1e6:.2f}")

        final_metrics = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        final_metrics.update(metric_counters)
        return update.replace(sub_phase_costs=costs, metric_counters=final_metrics)
    @staticmethod
    def _refresh_dirty_set(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Hardening Phase: Ensure DirtySet is always current.
        Logic ID: PERF-006-REFRESH
        M7 Optimization: Incremental derivation.
        """
        from src.core.dirty import DirtySet
        
        # Phase 17 Law: If force_full_scan is True, the dirty set must include ALL entities.
        if update.force_full_scan:
            all_ids = set(state.entities.keys())
            new_dirty = DirtySet(
                movement_entities=all_ids,
                combat_entities=all_ids,
                inventory_entities=all_ids,
                strategic_entities=all_ids,
                social_entities=all_ids,
                lifecycle_entities=all_ids,
                town_entities=state.town_entity_ids,
                biological_entities=all_ids,
                attribute_entities=all_ids
            )
            return update.replace(dirty_set=new_dirty)
            
        new_dirty = DirtySet.from_update(state, update, base_dirty=update.dirty_set)
        return update.replace(dirty_set=new_dirty)
    
    @staticmethod
    def _strip_untrusted_world_effects(update: StateUpdate) -> StateUpdate:
        from src.engine.pipeline_phases.trust import TrustBoundaryPhase
        return TrustBoundaryPhase.strip(update)
        
    @staticmethod
    def _resolve_actor_validity(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.actor_validity import ActorValidityPhase
        return ActorValidityPhase.resolve(state, update)
        
    @staticmethod
    def _resolve_contract_expirations(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.contracts import ContractLifecyclePhase
        return ContractLifecyclePhase.resolve_expirations(state, update)

    @staticmethod
    def _resolve_groups(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.groups import GroupPhase
        return GroupPhase.resolve(state, update)

    @staticmethod
    def _route_interaction_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.pipeline_phases.interactions import InteractionPhase
        return InteractionPhase.route_interaction_intent(state, update)

    @staticmethod
    def _route_action_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.pipeline_phases.actions import ActionRoutingPhase
        return ActionRoutingPhase.route(state, update)
        
    @staticmethod
    def _apply_near_death_hardening(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase
        return NearDeathHardeningPhase.apply(state, update)
    
    @staticmethod
    def _resolve_quest_rewards(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.quests import QuestRewardPhase
        return QuestRewardPhase.resolve(state, update)

    @staticmethod
    def _resolve_resource_transactions(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.pipeline_phases.resources import ResourceTransactionPhase
        return ResourceTransactionPhase.resolve(state, update)

    @staticmethod
    def _resolve_position_swaps(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.movement import MovementPhase
        return MovementPhase.resolve_position_swaps(state, update)

    @staticmethod
    def _route_movement_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.pipeline_phases.movement import MovementPhase
        return MovementPhase.route_movement_intent(state, update)

    @staticmethod
    def _resolve_occupancy_conflicts(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.pipeline_phases.occupancy import OccupancyPhase
        return OccupancyPhase.resolve(state, update)