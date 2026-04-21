from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Dict

from src_v2.core.state import AuthoritativeState


class CanonicalStateHasher:
    """
    Deterministic hasher for AuthoritativeState.
    Isolation: hashing logic resides outside the core state models.
    """

    @staticmethod
    def get_hash(state: AuthoritativeState) -> str:
        """
        Produce a SHA256 hash of the compact canonical JSON representation.
        Locked by Milestone A Closure Contract.
        Truth: Governance, Replay, and Operational state are strictly EXCLUDED.
        """
        compact_json = CanonicalStateHasher.to_canonical_json(state, pretty=False)
        return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()

    @staticmethod
    def to_canonical_json(state: AuthoritativeState, pretty: bool = False) -> str:
        """
        Convert AuthoritativeState into a canonical JSON representation.
        - pretty=False: Compact format for hashing (Truth).
        - pretty=True: Indented format for debugging (Audit).
        """
        data = CanonicalStateHasher.to_canonical_data(state)
        
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def to_canonical_data(state: AuthoritativeState) -> Dict[str, Any]:
        """
        Convert AuthoritativeState into a sortable dictionary structure.
        Includes only authoritative fields defined by the Milestone A contract.
        Law: Non-authoritative state (governance, replay, transients) is EXCLUDED.
        """
        # 1. Scalar fields
        data = {
            "tick": state.tick,
            "seed": state.seed,
            "world_time": state.world_time
        }
        
        # 2. Entities (Sorted by ID)
        sorted_entities = {}
        for eid in sorted(state.entities.keys()):
            ent = state.entities[eid]
            sorted_entities[str(eid)] = {
                "id": ent.id,
                "kind": ent.kind,
                "position": ent.position,
                "readiness": ent.readiness,
                "active": ent.active,
                "interaction": {
                    "target_node_id": ent.interaction.target_node_id,
                    "progress": ent.interaction.progress
                },
                "identity": {
                    "role": ent.identity.role,
                    "faction": ent.identity.faction,
                    "known_recipes": sorted(list(ent.identity.known_recipes)),
                    "craft_target": ent.identity.craft_target
                },
                "inventory": {
                    "gold": ent.inventory.gold,
                    "items": sorted(ent.inventory.items),
                    "current_weight": ent.inventory.current_weight
                },
                "strategic": {
                    "blockers": {k: asdict(v) for k, v in sorted(ent.strategic.blockers.items())},
                    "leads": {k: asdict(v) for k, v in sorted(ent.strategic.leads.items())}
                },
                "properties": dict(sorted(ent.properties.items()))
            }
        data["entities"] = sorted_entities
        
        # 3. Global collections (All sorted by key/id)
        data["global_resources"] = dict(sorted(state.global_resources.items()))
        data["periodic_due_ticks"] = dict(sorted(state.periodic_due_ticks.items()))
        data["work_debt"] = dict(sorted(state.work_debt.items()))
        
        data["blocked_tiles"] = sorted([str(t) for t in state.blocked_tiles])
        data["town_tiles"] = sorted([str(t) for t in state.town_tiles])
        data["building_tiles"] = {str(k): v for k, v in sorted(state.building_tiles.items(), key=lambda x: str(x[0]))}
        
        # 4. RNG Checkpoint
        # Law: The internal RNG state must be captured exactly for reproducibility.
        # random.Random.getstate() returns a tuple; json.dumps will convert it to a list.
        data["rng_checkpoint"] = state.rng_checkpoint
        
        return data
