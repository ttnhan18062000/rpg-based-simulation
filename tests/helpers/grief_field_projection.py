"""The canonical state with the grief-drain field removed: the proof that moving grief detection into authoritative state changes no behaviour.

`AuthoritativeState.grief_drained_tick` sits in the canonical data once a grief drain has happened (decision 80, grief as state), so a run with a
grief trigger gains that one key. The projection drops exactly that key; the projected digest of a run on the new code must equal the full digest
of the same run on the code before the step. It tolerates a state that never had the field, so both sides use it.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from src.engine.checkpoint import CanonicalStateHasher

GRIEF_FIELDS = ("grief_drained_tick",)


def projected_canonical(state: Any) -> Dict[str, Any]:
    """The canonical data with the grief-drain key removed (the cached canonical dict is untouched)."""
    data = CanonicalStateHasher.to_canonical_data(state)
    return {k: v for k, v in data.items() if k not in GRIEF_FIELDS}


def projected_digest(state: Any) -> str:
    """SHA256 of the projected canonical data, in the hasher's own compact form."""
    return hashlib.sha256(json.dumps(projected_canonical(state), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
