"""Deterministic conflict resolution for parallel action proposals."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.actions.combat import CombatAction
from src.actions.move import MoveAction
from src.actions.rest import RestAction
from src.actions.repair import RepairAction
from src.core.models.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class ConflictResolver:
    """Sorts, validates, and applies proposals in deterministic order.

    Resolution policies:
    - Movement: earliest next_act_at wins; tie-break by lowest entity ID.
    - Combat: processed sequentially by initiative (speed); dead targets fail validation.
    """

    __slots__ = ("_config", "_combat_action")

    PRIORITY_MAP: dict[ActionType, int] = {
        ActionType.USE_ITEM: 10,
        ActionType.MOVE: 20,
        ActionType.ATTACK: 30,
        ActionType.USE_SKILL: 40,
        ActionType.LOOT: 50,
        ActionType.HARVEST: 60,
        ActionType.REPAIR: 70,
        ActionType.REST: 80,
    }

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._combat_action = CombatAction(config, rng)

    def resolve(self, proposals: list[ActionProposal], world: WorldState) -> list[ActionProposal]:
        """Validate and apply proposals. Returns the list of *applied* proposals."""
        if not proposals:
            return []

        sorted_proposals = self._sort(proposals, world)
        applied: list[ActionProposal] = []
        
        # Track positions claimed DURING this resolution tick (AOA Phase 6)
        resolution_occupied: set[tuple[int, int]] = set()

        sorted_proposals = self._sort(proposals, world)
        
        for p in sorted_proposals:
            res = self._apply_one(p, world, resolution_occupied)
            if res:
                applied.append(p)

        print(f"DEBUG: RESOLVE_END: Applied={len(applied)}")
        return applied

    # -- internals --

    @classmethod
    def _sort(cls, proposals: list[ActionProposal], world: WorldState) -> list[ActionProposal]:
        """Deterministic sort: explicit action priority, then next_act_at, then entity ID."""

        def sort_key(p: ActionProposal) -> tuple[int, float, int]:
            entity = world.entities.get(p.actor_id)
            next_act = entity.next_act_at if entity else float("inf")
            priority = cls.PRIORITY_MAP.get(ActionType(p.verb), 100)
            return (priority, next_act, p.actor_id)

        return sorted(proposals, key=sort_key)

    @staticmethod
    def _build_occupied_set(world: WorldState) -> set[tuple[int, int]]:
        """DEPRECATED (AOA Phase 6): Use world.is_occupied() for O(1) lookups."""
        return set()

    def _apply_one(
        self,
        proposal: ActionProposal,
        world: WorldState,
        occupied: set[tuple[int, int]],
    ) -> bool:
        match proposal.verb:
            case ActionType.REPAIR:
                if RepairAction.validate(proposal, world):
                    RepairAction.apply(proposal, world)
                    return True
            case ActionType.REST:
                if RestAction.validate(proposal, world):
                    RestAction.apply(proposal, world)
                    return True

            case ActionType.MOVE:
                if MoveAction.validate(proposal, world, occupied):
                    entity = world.entities.get(proposal.actor_id)
                    if entity:
                        # -- Opportunity Attack Logic --
                        # If the entity was engaged (adjacent to hostiles), they get to strike
                        old_pos = entity.spatial.pos
                        # Opportunity Attack Check: Is anyone adjacent and hostile?
                        for other in world.entities_at_radius(old_pos, 1):
                            if other.id == entity.id or not other.combat.alive: continue
                            if other.identity.faction != entity.identity.faction:
                                # Trigger free Opportunity Attack
                                opp_prop = ActionProposal(actor_id=other.id, verb=ActionType.ATTACK, target=entity.id, reason="Opportunity Attack")
                                if self._combat_action.validate(opp_prop, world):
                                    self._combat_action.apply(opp_prop, world)
                                else:
                                    logger.debug("OA_VALIDATE_FAIL: %d -> %d", other.id, entity.id)

                        # Free old position (if it was claimed this tick)
                        occupied.discard((entity.spatial.pos.x, entity.spatial.pos.y))
                    # Claim target position for this tick's resolution (prevent collisions)
                    target = proposal.target
                    occupied.add((target.x, target.y))
                    
                    # Apply the move immediately so subsequent actions in this tick see the new pos
                    MoveAction.apply(proposal, world)
                    return True

            case ActionType.ATTACK:
                if self._combat_action.validate(proposal, world):
                    self._combat_action.apply(proposal, world)
                    return True

            case ActionType.USE_ITEM | ActionType.LOOT | ActionType.HARVEST | ActionType.USE_SKILL:
                # Validated and applied later in WorldLoop
                entity = world.entities.get(proposal.actor_id)
                if entity and entity.combat.alive:
                    return True

        from src.utils.metrics import SIM_INVALID_ACTIONS_TOTAL
        verb_name = proposal.verb.name if hasattr(proposal.verb, "name") else ActionType(proposal.verb).name
        SIM_INVALID_ACTIONS_TOTAL.labels(action_type=verb_name.lower(), reason="validation_failed").inc()
        
        logger.debug("Rejected: %s", proposal)
        return False
