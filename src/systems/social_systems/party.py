from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from src.ai.goals.base import GoalScore
from src.core.strategic import ContractStatus, ContractKind

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class PartyCoordinationSystem:
    """
    Authoritative logic for group-based strategic synchronization.
    Implements 'Individual Agency with Leadership Influence' model (Phase 7).
    """

    @staticmethod
    def apply_leadership_influence(
        entity: EntityState,
        state: AuthoritativeState,
        scores: List[GoalScore]
    ) -> List[GoalScore]:
        """
        Injects the leader's active objective as a candidate goal for the member.
        Follows Section 1 of Phase 7 design.
        """
        if getattr(state, "_has_contracts_cache", None) is False or not entity.strategic.contracts:
            return scores

        # 1. Find active party contract where entity is target (member)
        active_contract = None
        for contract in entity.strategic.contracts.values():
            if contract.status == ContractStatus.ACTIVE and contract.kind == ContractKind.RECRUITMENT:
                active_contract = contract
                break
        
        if not active_contract:
            return scores
            
        # 2. Identify the Leader
        leader = state.entities.get(active_contract.source_id)
        if not leader or not leader.combat.alive or not leader.lifecycle.active:
            return scores
            
        # 3. Retrieve Leader's Active Objective
        leader_proj_id = leader.strategic.current_project_id
        if not leader_proj_id:
            return scores
            
        leader_proj = leader.strategic.projects.get(leader_proj_id)
        if not leader_proj or not leader_proj.active_objective_id:
            return scores
            
        leader_obj = next((o for o in leader_proj.objectives if o.id == leader_proj.active_objective_id), None)
        if not leader_obj:
            return scores
            
        # 4. Calculate Leadership Boost (Phase 7 Rule)
        # utility = Base_Obligation + (Trust_in_Leader * Modifier)
        bond = entity.social.bonds.get(leader.id)
        # Trust mapping: sentiment=1.0 -> 1.0, sentiment=-1.0 -> 0.0
        trust_score = (bond.sentiment + 1.0) / 2.0 if bond else entity.social.trust_history.get(leader.id, 0.5)
        
        # Base boost from having an active recruitment contract (Obligation)
        # 25.0 is a strong push but allows survival (hunger/HP) to override if they are high enough.
        boost = 25.0 + (trust_score * 15.0)
        
        # 5. Create Party Objective Goal
        # We reuse the leader's objective kind and target to ensure alignment.
        # This allows the member to perform the same task or reach the same spot.
        party_goal = GoalScore(
            kind=leader_obj.kind,
            utility=boost,
            target_id=leader_obj.target,
            metadata={
                "party_sync": True,
                "leader_id": leader.id,
                "contract_id": active_contract.id
            }
        )
        
        # Append to candidates for standard scoring evaluation
        return scores + [party_goal]

    @staticmethod
    def coordinate_party_objectives(
        leader: EntityState,
        members: List[EntityState],
        tick: int
    ) -> List[Any]: # List[EntityUpdate]
        """
        Propagates the leader's current objective to all active party members.
        In V2, this is primarily handled via apply_leadership_influence during scoring,
        but we can use this for forced sync or state cleaning.
        """
        return []

    @staticmethod
    def validate_shared_target(
        group_id: int,
        state: AuthoritativeState
    ) -> Optional[int]:
        """
        Ensures the shared party target is still alive and valid.
        Clears if target is dead, inactive, or out of range.
        """
        group = state.groups.get(group_id)
        if not group or group.shared_target_id is None:
            return None
            
        target = state.entities.get(group.shared_target_id)
        if not target or not target.combat.alive or not target.lifecycle.active:
            # Clear target logic
            return None
            
        # Optional: range check against group anchor
        dx = target.navigation.position[0] - group.anchor[0]
        dy = target.navigation.position[1] - group.anchor[1]
        if (dx*dx + dy*dy) > (group.cohesion_radius * 2.0)**2:
             return None
             
        return group.shared_target_id

    @staticmethod
    def issue_party_command(
        leader: EntityState,
        command_kind: str, # 'REGROUP', 'RETREAT', 'ATTACK'
        target_pos: Optional[tuple[float, float]],
        tick: int
    ) -> StrategicUpdate:
        """
        Creates a high-priority directive for all party members.
        """
        from src.core.strategic import DirectiveState, DirectivePriority
        
        directive = DirectiveState(
            id=f"party_cmd_{command_kind}_{tick}",
            kind=command_kind,
            target=str(target_pos) if target_pos else "",
            priority=DirectivePriority.CRITICAL,
            salience=1.0,
            created_tick=tick
        )
        
        return StrategicUpdate(directives_add_or_update=[directive])
