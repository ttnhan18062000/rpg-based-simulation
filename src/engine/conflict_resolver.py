"""Deterministic conflict resolution for parallel action proposals."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.actions.combat import CombatAction
from src.actions.move import MoveAction
from src.actions.rest import RestAction
from src.core.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.world_state import WorldState
    from src.systems.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class ConflictResolver:
    """Sorts, validates, and applies proposals in deterministic order.

    Resolution policies:
    - Movement: earliest next_act_at wins; tie-break by lowest entity ID.
    - Combat: processed sequentially by initiative (speed); dead targets fail validation.
    """

    __slots__ = ("_config", "_combat_action")

    def __init__(self, config: SimulationConfig, rng: DeterministicRNG) -> None:
        self._config = config
        self._combat_action = CombatAction(config, rng)

    def resolve(self, proposals: list[ActionProposal], world: WorldState) -> list[ActionProposal]:
        """Validate and apply proposals. Returns the list of *applied* proposals."""
        if not proposals:
            return []

        sorted_proposals = self._sort(proposals, world)
        applied: list[ActionProposal] = []
        occupied = self._build_occupied_set(world)

        for proposal in sorted_proposals:
            if self._apply_one(proposal, world, occupied):
                applied.append(proposal)

        return applied

    # -- internals --

    @staticmethod
    def _sort(proposals: list[ActionProposal], world: WorldState) -> list[ActionProposal]:
        """Deterministic sort: action type priority, then next_act_at, then entity ID."""

        def sort_key(p: ActionProposal) -> tuple[int, float, int]:
            entity = world.entities.get(p.actor_id)
            next_act = entity.next_act_at if entity else float("inf")
            return (p.verb.value, next_act, p.actor_id)

        return sorted(proposals, key=sort_key)

    @staticmethod
    def _build_occupied_set(world: WorldState) -> set[tuple[int, int]]:
        return {(e.pos.x, e.pos.y) for e in world.entities.values() if e.alive}

    def _apply_one(
        self,
        proposal: ActionProposal,
        world: WorldState,
        occupied: set[tuple[int, int]],
    ) -> bool:
        match proposal.verb:
            case ActionType.REST:
                if RestAction.validate(proposal, world):
                    RestAction.apply(proposal, world)
                    return True

            case ActionType.MOVE:
                if MoveAction.validate(proposal, world, occupied):
                    entity = world.entities.get(proposal.actor_id)
                    if entity:
                        # Free old position, claim new
                        occupied.discard((entity.pos.x, entity.pos.y))
                    MoveAction.apply(proposal, world)
                    target: Vector2 = proposal.target
                    occupied.add((target.x, target.y))
                    return True

            case ActionType.ATTACK:
                if self._combat_action.validate(proposal, world):
                    self._combat_action.apply(proposal, world)
                    return True

            case ActionType.USE_ITEM | ActionType.LOOT | ActionType.HARVEST | ActionType.USE_SKILL:
                # Validated and applied later in WorldLoop
                entity = world.entities.get(proposal.actor_id)
                if entity and entity.alive:
                    return True

        logger.debug("Rejected: %s", proposal)
        return False
