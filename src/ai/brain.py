"""AIBrain — stateless decision engine dispatching to class-based state handlers.

Uses the STATE_HANDLERS registry from ``ai.states`` and the FactionRegistry
for faction-aware enemy/ally detection.  Adding a new state or faction requires
zero changes here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.ai.perception import Perception
from src.ai.states import AIContext, STATE_HANDLERS, IdleHandler
from src.core.enums import AIState
from src.core.faction import FactionRegistry

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models import Entity
    from src.core.snapshot import Snapshot
    from src.systems.rng import DeterministicRNG

_FALLBACK = IdleHandler()


class AIBrain:
    """Dispatches entity AI decisions based on their current state.

    Fully stateless — safe to call from any thread.
    """

    __slots__ = ("_config", "_rng", "_faction_reg")

    def __init__(
        self,
        config: SimulationConfig,
        rng: DeterministicRNG,
        faction_reg: FactionRegistry | None = None,
    ) -> None:
        self._config = config
        self._rng = rng
        self._faction_reg = faction_reg or FactionRegistry.default()

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI state machine for *actor* and return (new_state, proposal)."""
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self._config,
            rng=self._rng,
            faction_reg=self._faction_reg,
        )

        handler = STATE_HANDLERS.get(actor.ai_state, _FALLBACK)
        new_state, proposal = handler.handle(ctx)

        # Update memory: remember visible hostile entities
        visible = Perception.visible_entities(actor, snapshot, self._config.vision_range)
        for e in visible:
            if self._faction_reg.is_hostile(actor.faction, e.faction):
                actor.memory[e.id] = e.pos

        return new_state, proposal
