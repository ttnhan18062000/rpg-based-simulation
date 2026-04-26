# src/core/serialization.py
from __future__ import annotations
import json
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class StateSerializer:
    """
    Handles serialization of AuthoritativeState to/from JSON.
    Ensures that gameplay state is preserved accurately for replay and persistence.
    """

    @staticmethod
    def serialize(state: AuthoritativeState) -> str:
        # This is a simplified version; real V2 would use a more robust
        # serialization layer (like msgpack or custom byte-level)
        data = {
            "tick": state.tick,
            "seed": state.seed,
            "entities": {eid: e.to_dict() for eid, e in state.entities.items()},
            "regions": {rid: r.to_dict() for rid, r in state.regions.items()},
            "global_resources": state.global_resources
        }
        return json.dumps(data)

    @staticmethod
    def deserialize(json_str: str) -> Dict[str, Any]:
        return json.loads(json_str)
