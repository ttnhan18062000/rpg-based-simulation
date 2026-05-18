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

        # --- Phase 1: Trust & Validity ---
        t_start = time.perf_counter_ns()
        update, compaction_metrics = StateUpdateCompactor.compact_with_metrics(state, update)
        metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        metric_counters["raw_entity_updates"] = compaction_metrics.raw_entity_updates
        metric_counters["compacted_entity_updates"] = compaction_metrics.compacted_entity_updates
        update = replace(update, metric_counters=metric_counters)
        update = AuthoritativeApplyPipeline._strip_untrusted_world_effects(update)
        update = AuthoritativeApplyPipeline._resolve_actor_validity(state, update)

        costs["trust_validity"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 2: Contracts & Production ---
        t_start = time.perf_counter_ns()
        update = AuthoritativeApplyPipeline._resolve_contract_expirations(state, update)
        update = BlacksmithSystem.enforce(state, update)
        costs["contracts_production"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 3: Action & Movement Routing ---
        t_start = time.perf_counter_ns()
        update = AuthoritativeApplyPipeline._route_action_intent(state, update)
        update = AuthoritativeApplyPipeline._resolve_position_swaps(state, update)
        update = AuthoritativeApplyPipeline._route_movement_intent(state, update)
        costs["locomotion"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 4: Interaction & World Effects ---
        t_start = time.perf_counter_ns()
        # InteractionSystem and TownResolution need an accurate dirty set
        dirty_builder.mark_from_update(state, update)
        built_dirty = dirty_builder.build()
        update = update.replace(dirty_set=built_dirty)
        if getattr(state, "movement_cache", None) is not None:
            state.movement_cache.invalidate_for_dirty(built_dirty)
        
        update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
        update = InteractionSystem.enforce(state, update)
        if should_run(state.tick, None, cadence.building_sabotage):
            update = BuildingSabotageSystem.resolve(state, update)
        costs["interaction"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 5: Governance & Ecology ---
        t_start = time.perf_counter_ns()
        if should_run(state.tick, None, cadence.town_resolution):
            update = TownResolutionSystem.resolve(state, update, cadence=cadence)
        
        generator = EntityGenerator(state.seed + state.tick)
        generator._last_id = state.next_entity_id - 1
        update = WorldDynamicsSystem.resolve_dynamics(state, update, generator, cadence=cadence)
        costs["governance_ecology"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 6: Economy & Evolution ---
        t_start = time.perf_counter_ns()
        update = AuthoritativeApplyPipeline._resolve_quest_rewards(state, update)
        update = ShopSystem.enforce(state, update)
        update = AuthoritativeApplyPipeline._resolve_resource_transactions(state, update)
        update = EvolutionSystem.evaluate(state, update)
        costs["economy"] = (time.perf_counter_ns() - t_start) / 1e6

        # --- Phase 7: Cognitive & Final Integrity ---
        t_start = time.perf_counter_ns()
        # Refresh dirty set before final strategic pass
        t0 = time.perf_counter_ns()
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
        t1 = time.perf_counter_ns()
        
        update = StrategicIntelligenceSystem.fused_strategic_pass(state, update, cadence=cadence)
        t2 = time.perf_counter_ns()
        update = AuthoritativeApplyPipeline._apply_near_death_hardening(state, update)
        t3 = time.perf_counter_ns()
        update = AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, update)
        t4 = time.perf_counter_ns()
        update = LifecycleSystem.resolve_lifecycle(state, update)
        t5 = time.perf_counter_ns()
        update = AuthoritativeApplyPipeline._resolve_groups(state, update)
        t6 = time.perf_counter_ns()
        update = CapacityEnforcementPhase.enforce(state, update)
        t7 = time.perf_counter_ns()
        
        # Final dirty set for result application
        dirty_builder.mark_from_update(state, update)
        update = update.replace(dirty_set=dirty_builder.build())
        t8 = time.perf_counter_ns()
        costs["final_integrity"] = (t8 - t_start) / 1e6
        if state.tick in (10, 20, 30, 40, 50) and len(state.entities) >= 500:
            logger.debug(f"[Tick {state.tick}] final_integrity breakdown (ms): dirty1={(t1-t0)/1e6:.2f}, fused={(t2-t1)/1e6:.2f}, hardening={(t3-t2)/1e6:.2f}, occupancy={(t4-t3)/1e6:.2f}, lifecycle={(t5-t4)/1e6:.2f}, groups={(t6-t5)/1e6:.2f}, capacity={(t7-t6)/1e6:.2f}, dirty2={(t8-t7)/1e6:.2f}")


        return update.replace(sub_phase_costs=costs)
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