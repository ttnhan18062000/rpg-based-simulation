"""Replay serialization — records tick-by-tick events for deterministic replay."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.core.world_state import WorldState

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
                "pos": [e.pos.x, e.pos.y],
                "hp": e.stats.hp,
                "state": e.ai_state.name,
            }
            for e in world.entities.values()
            if e.alive
        ]
        actions_log = [
            {
                "actor": a.actor_id,
                "verb": a.verb.name,
                "target": (
                    [a.target.x, a.target.y]
                    if hasattr(a.target, "x")
                    else a.target
                ),
                "reason": a.reason,
            }
            for a in applied_actions
        ]

        self._ticks.append(
            {
                "tick": tick,
                "actions": actions_log,
                "entities": entities_snapshot,
            }
        )

    def flush(self) -> None:
        """Write accumulated data to disk."""
        replay = {
            "version": "1.0",
            "seed": self._seed,
            "total_ticks": len(self._ticks),
            "ticks": self._ticks,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
        logger.info("Replay saved to %s (%d ticks)", self._path, len(self._ticks))
