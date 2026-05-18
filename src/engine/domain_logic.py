# src/engine/domain_logic.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Any, Optional, List
from dataclasses import replace

from src.core.updates import (
    EntityUpdate, IdentityUpdate, CombatUpdate, 
    LifecycleUpdate, StateUpdate, RewardUpdate,
    SocialUpdate, NavigationUpdate
)
from src.core.enums import ReasonCode

if TYPE_CHECKING:
    from src.core.state import EntityState

class SimulationDomainLogic:
    """
    Law: Absolute semantic truth for RPG domain operations.
    Isolated from networking, concurrency, or worker protocols.
    """

    @staticmethod
    def execute_move(
        state: AuthoritativeState,
        entity: EntityState, 
        target_pos: Tuple[float, float]
    ) -> Dict[int, EntityUpdate]:
        from src.engine.domain.movement_actions import MovementActions
        return MovementActions.execute_move(state, entity, target_pos)

    @staticmethod
    def execute_brain(
        state: AuthoritativeState,
        entity: EntityState,
        force: bool = False
    ) -> Dict[int, EntityUpdate]:
        """RPG TACTICAL COGNITION."""
        from src.engine.domain.cognition import CognitionDomain
        return CognitionDomain.execute_brain(state, entity, force)

    @staticmethod
    def execute_action(
        entity: EntityState, 
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """
        Standard action cost and routine logic.
        Delegates to ActionRouter for domain logic.
        """
        from src.engine.domain.action_router import ActionRouter
        return ActionRouter.execute_action(
            entity, payload, current_tick, neighbor_view, context
        )
    @staticmethod
    def drain_debt(owner_id: str, profile) -> int:
        """
        Milestone C Law: Authoritative Drain Logic.
        Determines how much work debt is cleared in a single execution unit.
        """
        # owner_id is the subsystem name (e.g. "REPLAY", "KERNEL")
        return -profile.max_worker_count

    @staticmethod
    def get_neighbor_view(
        state: AuthoritativeState,
        subject: EntityState, 
        radius: float = 10.0
    ) -> List[tuple[int, EntityState]]:
        from src.engine.domain.view import DomainView
        return DomainView.get_neighbor_view(state, subject, radius)


    @staticmethod
    def get_region_trauma(
        state: AuthoritativeState,
        pos: Tuple[float, float]
    ) -> float:
        from src.engine.domain.view import DomainView
        return DomainView.get_region_trauma(state, pos)
