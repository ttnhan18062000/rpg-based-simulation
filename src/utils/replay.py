"""Replay serialization — records tick-by-tick events for deterministic replay."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.core.models.world_state import WorldState
from src.core.models.enums import AIState, ActionType, StrategicStatus

logger = logging.getLogger(__name__)


class ReplayRecorder:
    """Accumulates tick events and flushes to a JSON replay file."""

    __slots__ = ("_path", "_ticks", "_seed")

    def __init__(self, path: str | Path, seed: int) -> None:
        self._path = Path(path)
        self._seed = seed
        self._ticks: list[dict[str, Any]] = []

    def record_tick(
        self,
        tick: int,
        applied_actions: list[ActionProposal],
        world: WorldState,
    ) -> None:
        entities_snapshot = [
            {
                "id": e.id,
                "kind": e.kind,
                "pos": [e.spatial.pos.x, e.spatial.pos.y],
                "hp": e.combat.hp,
                "state": e.mind.decision.ai_state.name if hasattr(e.mind.decision.ai_state, "name") else str(e.mind.decision.ai_state),
                "strategy": {
                    "project_id": e.mind.strategic.current_project_id,
                    "objective_id": e.mind.strategic.current_objective_id,
                    "interrupted_by": e.mind.strategic.interrupted_project_id,
                    "concern_count": len(e.mind.strategic.concerns)
                }
            }
            for e in world.entities.values()
            if e.combat.alive
        ]
        actions_log = [
            {
                "actor": a.actor_id,
                "verb": a.verb.name if hasattr(a.verb, "name") else ActionType(a.verb).name,
                "target": (
                    [a.target.x, a.target.y]
                    if hasattr(a.target, "x")
                    else a.target
                ),
                "reason": a.reason,
            }
            for a in applied_actions
        ]

        strategic_snapshot = {
            "opportunities": [opp.label for opp in world.strategic_registry.opportunities.values() if opp.status == StrategicStatus.ACTIVE],
            "obligations": [obl.label for obl in world.strategic_registry.obligations.values()]
        }

        self._ticks.append(
            {
                "tick": tick,
                "actions": actions_log,
                "entities": entities_snapshot,
                "world_strategic": strategic_snapshot
            }
        )

    def flush(self) -> None:
        """Write accumulated data to disk."""
        replay = {
            "version": "2.0",
            "seed": self._seed,
            "total_ticks": len(self._ticks),
            "ticks": self._ticks,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
        logger.info("Replay saved to %s (%d ticks)", self._path, len(self._ticks))
