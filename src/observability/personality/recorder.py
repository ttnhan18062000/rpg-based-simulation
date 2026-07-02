"""
Personality Snapshot Recorder.

Emits per-entity personality snapshots to
``data/runs/{run_id}/entity_personality_snapshots.jsonl``.

Emission policy
---------------
- OFF mode     : never emit.
- LIGHT+ modes : emit when an entity's ``active_project_kind`` changes
                 (including the first observation per entity, which always emits).
- DEBUG mode   : emit every tick for every strategic entity, regardless of change.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from src.core.state import AuthoritativeState
from src.observability.config import ObservabilityConfig, ObservabilityMode

logger = logging.getLogger(__name__)

# Sentinel: distinct from None so that the first observation always emits even
# when the entity has no active project (active_project_kind == None).
_UNSEEN = "__UNSEEN__"


class PersonalitySnapshotRecorder:
    """
    Post-commit recorder for lightweight per-entity personality snapshots.

    Thread-safety: each Kernel instance owns one recorder; single-threaded
    post-commit call site — no locking required.
    """

    def __init__(self, run_id: str, run_dir: Optional[str] = None) -> None:
        self.run_id = run_id
        self.run_dir = run_dir or f"data/runs/{run_id}"
        self._output_file = os.path.join(self.run_dir, "entity_personality_snapshots.jsonl")
        # {entity_id: last emitted active_project_kind string or None}
        self._prev_project_kind: Dict[int, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_tick(self, state: AuthoritativeState, tick: int) -> None:
        """
        Evaluate and emit personality snapshots for all strategic entities.

        Must be called strictly post-commit with no state mutations.
        """
        mode = ObservabilityConfig.get_mode()
        if mode == ObservabilityMode.OFF:
            return

        is_debug = mode == ObservabilityMode.DEBUG
        records = []

        for entity in state.entities.values():
            strat = getattr(entity, "strategic", None)
            if strat is None:
                continue

            eid = entity.id

            # Resolve current project kind string (or None when no active project)
            active_project_kind: Optional[str] = None
            if strat.current_project_id and strat.current_project_id in strat.projects:
                proj = strat.projects[strat.current_project_id]
                kind = proj.kind
                active_project_kind = kind.value if hasattr(kind, "value") else str(kind)

            # Determine whether to emit a record this tick
            prev_kind = self._prev_project_kind.get(eid, _UNSEEN)
            kind_changed = prev_kind != active_project_kind

            # Always update prev-state cache
            self._prev_project_kind[eid] = active_project_kind

            if not is_debug and not kind_changed:
                continue

            # Build snapshot record
            identity = getattr(entity, "identity", None)
            role: Optional[int] = None
            class_id: Optional[str] = None
            personality_dict: Dict[str, Any] = {}

            if identity is not None:
                role = identity.role
                class_id = identity.class_id
                pers = getattr(identity, "personality", None)
                if pers is not None:
                    personality_dict = pers.to_canonical_dict()

            records.append(
                {
                    "run_id": self.run_id,
                    "entity_id": eid,
                    "tick": tick,
                    "role": role,
                    "class_id": class_id,
                    "personality": personality_dict,
                    "active_project_kind": active_project_kind,
                }
            )

        if records:
            os.makedirs(self.run_dir, exist_ok=True)
            with open(self._output_file, "a", encoding="utf-8") as fh:
                for rec in records:
                    fh.write(json.dumps(rec) + "\n")
