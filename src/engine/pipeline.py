from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional, Any, Set
from dataclasses import replace
import logging

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate

logger = logging.getLogger(__name__)

class AuthoritativeApplyPipeline:
    """
    Law: The pipeline is the singular bottleneck for authoritative truth.
    Proof: All mutations must pass through refine() and be bit-identical.
    VERIFIED v2: AuthoritativeApplyPipeline (Milestone D)
    """

    @staticmethod
    def refine(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Singular entry point for authoritative state transition refinement.
        Orchestrates systems in the correct causal order.
        """
        # 1. Identity & Lifecycle (High Priority)
        # 2. Strategic Intents (Evaluating long-term projects)
        from src.systems.strategic import StrategicIntelligenceSystem
        from src.systems.redirection import StrategicRedirectionSystem
        from src.systems.navigation import NavigationSystem
        from src.engine.interaction import InteractionSystem
        from src.engine.blacksmith import BlacksmithSystem
        from src.systems.groups import GroupSystem
        from src.systems.lifecycle import LifecycleSystem
        from src.engine.legality import LegalityServiceV2
        from src.core.updates import EntityUpdate
        
        # 0. Trust Boundary: strip raw world-side effects from worker proposals.
        update = AuthoritativeApplyPipeline._strip_untrusted_world_effects(update)
        
        # 0.1 Actor Validity
        # Reject proposals from dead/inactive/incapacitated actors before any subsystem
        # can route their movement, actions, resource intents, or interaction progress.
        #
        # This must run after trust-boundary stripping because raw worker rewards/world
        # mutations should already be removed, but before contract/quest/action/movement
        # routing because invalid actors must not participate in the tick.
        update = AuthoritativeApplyPipeline._resolve_actor_validity(state, update)
        
        # 0.1 Contract Lifecycle
        # Expire stale social contracts before any later system can consume them.
        #
        # Why this must run early:
        #   - expired recruitment offers should not be accepted
        #   - expired POSITION_SWAP contracts should not move entities
        #   - expired loan/protection/merchant contracts should not affect strategy
        #
        # This phase only updates contract statuses. It should not move entities,
        # transfer inventory, or mutate world resources.
        update = AuthoritativeApplyPipeline._resolve_contract_expirations(state, update)
        
        # 1. Apply Blacksmith/Crafting Laws (Milestone 3)
        update = BlacksmithSystem.enforce(state, update)
        
        # 2. Task/Intent Routing (Converting high-level tasks to low-level intents)
        update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
        
        # 3. Interaction Enforcement (Harvesting, Chests)
        update = InteractionSystem.enforce(state, update)
        
        # 4. Action Enforcement (Combat, Abilities)
        update = AuthoritativeApplyPipeline._route_action_intent(state, update)
        
        # 4.1 Near-Death Hardening
        # Must run after action/combat routing, because it depends on CombatUpdate.hp_delta.
        # Must run before lifecycle/evolution finalization so the hardened combat update
        # is part of the same authoritative tick.
        update = AuthoritativeApplyPipeline._apply_near_death_hardening(state, update)
        
        # Phase 8: Infrastructure Sabotage (LEG-RPG-006)
        from src.engine.sabotage import BuildingSabotageSystem
        from src.engine.town_resolution import TownResolutionSystem
        update = BuildingSabotageSystem.resolve(state, update)
        update = TownResolutionSystem.resolve(state, update)
        
        # Phase 7 Implementation: World Dynamics (Hazards, Spawns, Decays)
        # VERIFIED v2: passive_world_progression
        from src.systems.generator import EntityGenerator
        from src.engine.world_dynamics import WorldDynamicsSystem
        generator = EntityGenerator(state.seed + state.tick)
        generator._last_id = state.next_entity_id - 1
        update = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
        
        # 4.5 Quest Reward Authority
        # Converts quest completion / reward retry into ResourceTransferIntent.
        # This must run before _resolve_resource_transactions so reward delivery is
        # capacity-checked atomically.
        update = AuthoritativeApplyPipeline._resolve_quest_rewards(state, update)
        
        # 5. Resource Transaction Laws (Transfers, Drops)
        # Atomic Resource Transactions
        from src.engine.shop import ShopSystem
        update = ShopSystem.enforce(state, update)
        update = AuthoritativeApplyPipeline._resolve_resource_transactions(state, update)
        
        # Phase 8: Evolution & Leveling (LEG-RPG-143)
        from src.engine.evolution import EvolutionSystem
        update = EvolutionSystem.evaluate(state, update)
        
        # 6. Strategic Evaluation (Blockers, Projects, Concerns)
        update = StrategicIntelligenceSystem.resolve_blockers(state, update)
        update = StrategicIntelligenceSystem.evaluate_all_concerns(state, update)
        update = StrategicIntelligenceSystem.evaluate_all_strategic_intents(state, update)
        update = StrategicRedirectionSystem.enforce(state, update)
        
        # 7.0 Position Swap Contracts / Mutual Corridor Passing
        # This must run before normal movement routing. Otherwise MovementSystem sees
        # the target tile as occupied and may choose sidestep/yield/failure instead of
        # the explicit consensual adjacent swap.
        update = AuthoritativeApplyPipeline._resolve_position_swaps(state, update)
        
        # 7.1 Navigation & Movement (Pathfinding, Obstacles)
        update = AuthoritativeApplyPipeline._route_movement_intent(state, update)

        # 7.5 Final Occupancy Conflict Resolution
        # This protects the authoritative apply path from invalid worker proposals
        # that directly set EntityUpdate.new_position.
        update = AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, update)
        
        # 8. Lifecycle Enforcement (Death, Respawn)
        update = LifecycleSystem.resolve_lifecycle(state, update)
        
        # 9. Group Logic (Formation & Coordination)
        update = AuthoritativeApplyPipeline._resolve_groups(state, update)

        return update
    
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