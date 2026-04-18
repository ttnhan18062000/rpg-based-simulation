from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Dict

from src_v2.core.state import AuthoritativeState


class CanonicalStateHasher:
    """
    Deterministic hasher for AuthoritativeState.
    Isolation: hacing logic resides outside the core state models.
    """

    @staticmethod
    def get_hash(state: AuthoritativeState) -> str:
        """
        Produce a SHA256 hash of the canonical state representation.
        """
        canonical_material = CanonicalStateHasher._canonicalize(state)
        json_bytes = json.dumps(
            canonical_material, 
            sort_keys=True, 
            separators=(",", ":")
        ).encode("utf-8")
        
        return hashlib.sha256(json_bytes).hexdigest()

    @staticmethod
    def _canonicalize(state: AuthoritativeState) -> Dict[str, Any]:
        """
        Convert AuthoritativeState into a sortable dictionary structure.
        Excludes non-authoritative logic or transient data (if any).
        """
        # We use asdict but must ensure sorting of keys in nested dicts
        # happens in the json.dumps stage with sort_keys=True.
        # Here we only need to handle non-serializable objects.
        raw = asdict(state)
        
        # Ensure entity keys (ints) are converted to strings for JSON
        raw["entities"] = {str(k): v for k, v in raw["entities"].items()}
        
        # Enums or other complex types should be simplified if they exist.
        # In Milestone 2, our state is purely primitives, dicts, and tuples.
        
        return raw
