from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Dict

from src_v2.core.state import AuthoritativeState


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
            "movement_count": state.movement_count
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
                    "progress": ent.interaction.progress,
                    "start_tick": ent.interaction.start_tick
                },
                "identity": {
                    "role": ent.identity.role,
                    "faction": ent.identity.faction,
                    "known_recipes": sorted(list(ent.identity.known_recipes)),
                    "craft_target": ent.identity.craft_target or ""
                },
                "inventory": {
                    "gold": ent.inventory.gold,
                    "items": sorted(ent.inventory.items),
                    "max_slots": ent.inventory.max_slots,
                    "current_weight": ent.inventory.current_weight
                },
                "strategic": {
                    "blockers": {k: asdict(v) for k, v in sorted(ent.strategic.blockers.items())},
                    "leads": {k: asdict(v) for k, v in sorted(ent.strategic.leads.items())}
                },
                "social": {
                    "trust_history": {str(k): v for k, v in sorted(ent.social.trust_history.items())},
                    "betrayal_count": ent.social.betrayal_count,
                    "public_reputation": ent.social.public_reputation
                },
                "combat": {
                    "hp": ent.combat.hp,
                    "max_hp": ent.combat.max_hp,
                    "atk": ent.combat.atk,
                    "def_stat": ent.combat.def_stat,
                    "alive": ent.combat.alive
                },
                "navigation": {
                    "target": ent.navigation.target,
                    "path": ent.navigation.path,
                    "moved_recently": ent.navigation.moved_recently
                },
                "task": {
                    "work_kind": ent.task.work_kind,
                    "payload": dict(sorted(ent.task.payload.items()))
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
        data["rng_checkpoint"] = state.rng_checkpoint
        
        return data
