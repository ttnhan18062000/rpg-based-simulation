"""The canonical state with the death-record fields removed: the proof that recording a death changes no behaviour.

`LifecycleComponent.death_record` and `CombatComponent.last_attacker_id` sit in the canonical state, so a step that adds them moves every state
digest that has a death. The projection drops exactly those two keys per entity; the projected digest of a run on the new code must equal the full
digest of the same run on the code before the step. It tolerates a state that never had the fields (the earlier code), so both sides use it.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from src.engine.checkpoint import CanonicalStateHasher

DEATH_FIELDS = (("lifecycle", "death_record"), ("combat", "last_attacker_id"))


def projected_canonical(state: Any) -> Dict[str, Any]:
    """The canonical data with every entity's death-record fields removed (copies the two components; the cached canonical dicts are untouched)."""
    data = CanonicalStateHasher.to_canonical_data(state)
    entities = {}
    for eid, ent in data["entities"].items():
        ent = dict(ent)
        for component, key in DEATH_FIELDS:
            part = dict(ent[component])
            part.pop(key, None)
            ent[component] = part
        entities[eid] = ent
    return {**data, "entities": entities}


def projected_digest(state: Any) -> str:
    """SHA256 of the projected canonical data, in the hasher's own compact form."""
    return hashlib.sha256(json.dumps(projected_canonical(state), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
