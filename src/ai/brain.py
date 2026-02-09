"""AIBrain — stateless decision engine with Utility AI goal selection.

Hybrid architecture:
  1. For "decision" states (IDLE, WANDER, RESTING_IN_TOWN, GUARD_CAMP),
     the GoalEvaluator scores all viable goals and picks one via weighted
     random.  The selected goal sets the AIState, then the state handler
     executes it.
  2. For "execution" states (HUNT, COMBAT, FLEE, LOOTING, VISIT_*, etc.),
     the state handler runs directly — the entity is already committed to
     an action and shouldn’t re-evaluate every tick.

Uses the STATE_HANDLERS registry from ``ai.states`` and the FactionRegistry
for faction-aware enemy/ally detection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.ai.goals import GoalEvaluator
from src.ai.perception import Perception
from src.ai.states import AIContext, STATE_HANDLERS, IdleHandler
from src.core.enums import AIState, Domain
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

    __slots__ = ("_config", "_rng", "_faction_reg", "_goal_evaluator")

    def __init__(
        self,
        config: SimulationConfig,
        rng: DeterministicRNG,
        faction_reg: FactionRegistry | None = None,
    ) -> None:
        self._config = config
        self._rng = rng
        self._faction_reg = faction_reg or FactionRegistry.default()
        self._goal_evaluator = GoalEvaluator()

    # States where the goal evaluator runs before the handler
    _DECISION_STATES = frozenset({
        AIState.IDLE, AIState.WANDER,
        AIState.RESTING_IN_TOWN, AIState.GUARD_CAMP,
    })

    def decide(self, actor: Entity, snapshot: Snapshot) -> tuple[AIState, ActionProposal]:
        """Run the AI for *actor*: goal evaluation + state handler."""
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self._config,
            rng=self._rng,
            faction_reg=self._faction_reg,
        )

        # --- Goal evaluation for decision states ---
        if actor.ai_state in self._DECISION_STATES:
            goal_scores = self._goal_evaluator.evaluate(ctx)
            if goal_scores:
                rng_val = self._rng.next_float(
                    Domain.AI_DECISION, actor.id, snapshot.tick + 50)
                selected = self._goal_evaluator.select(goal_scores, rng_val)
                if selected:
                    # Transition actor to the goal's state before handler runs
                    actor.ai_state = selected.target_state

        handler = STATE_HANDLERS.get(actor.ai_state, _FALLBACK)
        new_state, proposal = handler.handle(ctx)

        # Update memory: remember visible hostile entities
        visible = Perception.visible_entities(actor, snapshot, self._config.vision_range)
        for e in visible:
            if self._faction_reg.is_hostile(actor.faction, e.faction):
                actor.memory[e.id] = e.pos

        return new_state, proposal
