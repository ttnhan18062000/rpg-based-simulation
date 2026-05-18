# Compliance IDs: INFRA-119, INFRA-120, INFRA-121, INFRA-122, INFRA-123, INFRA-124, INFRA-125, INFRA-126, INFRA-127, INFRA-128, INFRA-129, INFRA-130, INFRA-133
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from src.core.state import AuthoritativeState


class CanonicalStateHasher:
    """
    Deterministic hasher for AuthoritativeState.
    """

    @staticmethod
    def get_hash(state: AuthoritativeState) -> str:
        """
        Produce a SHA256 hash of the compact canonical JSON representation.
        """
        compact_json = CanonicalStateHasher.to_canonical_json(state, pretty=False)
        return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()

    @staticmethod
    def to_canonical_json(state: AuthoritativeState, pretty: bool = False) -> str:
        """
        Convert AuthoritativeState into a canonical JSON representation.
        """
        data = CanonicalStateHasher.to_canonical_data(state)
        
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def to_canonical_data(state: AuthoritativeState) -> Dict[str, Any]:
        """
        Convert AuthoritativeState into a sortable dictionary structure.
        """
        # 1. Scalar fields
        data = {
            "tick": state.tick,
            "seed": state.seed,
            "world_time": state.world_time,
            "movement_count": state.movement_count,
            "maturity": state.maturity,
            "last_calamity_tick": state.last_calamity_tick,
            "town_center": state.town_center
        }
        
        # 2. Entities (Sorted by ID)
        sorted_entities = {}
        for eid in sorted(state.entities.keys()):
            sorted_entities[str(eid)] = state.entities[eid].to_canonical_dict()
        data["entities"] = sorted_entities
        
        # 3. Global collections (All sorted by key/id)
        data["regions"] = {k: v.to_canonical_dict() for k, v in sorted(state.regions.items())}
        data["local_scars"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.local_scars.items())}
        data["resource_nodes"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.resource_nodes.items())}
        data["buildings"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.buildings.items())}
        data["corpses"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.corpses.items())}
        data["ground_items"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.ground_items.items())}
        data["chests"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.chests.items())}
        data["groups"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.groups.items())}
        data["home_storage"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.home_storage.items())}
        data["camps"] = {k: v.to_canonical_dict() for k, v in sorted(state.camps.items())}
        
        data["global_resources"] = dict(sorted(state.global_resources.items()))
        data["periodic_due_ticks"] = dict(sorted(state.periodic_due_ticks.items()))
        data["work_debt"] = dict(sorted(state.work_debt.items()))
        
        data["blocked_tiles"] = sorted([str(t) for t in state.blocked_tiles])
        data["town_tiles"] = sorted([str(t) for t in state.town_tiles])
        data["building_tiles"] = {str(k): v for k, v in sorted(state.building_tiles.items(), key=lambda x: str(x[0]))}
        
        # 4. RNG Checkpoint
        data["rng_checkpoint"] = state.rng_checkpoint
        
        return data
