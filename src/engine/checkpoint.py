from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
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
            ent = state.entities[eid]
            sorted_entities[str(eid)] = {
                "id": ent.id,
                "kind": ent.kind,
                "position": ent.navigation.position,
                "readiness": ent.combat.readiness,
                "active": ent.lifecycle.active,
                "interaction": asdict(ent.interaction),
                "identity": {
                    "role": ent.identity.role,
                    "faction": ent.identity.faction,
                    "class_id": ent.identity.class_id,
                    "evolution_level": ent.identity.evolution_level,
                    "evolution_points": ent.identity.evolution_points,
                    "veterancy_rank": ent.identity.veterancy_rank,
                    "unspent_ap": ent.identity.unspent_ap,
                    "known_recipes": sorted(list(ent.identity.known_recipes)),
                    "learned_skills": sorted(list(ent.identity.learned_skills)),
                    "active_breakthroughs": sorted(list(ent.identity.active_breakthroughs)),
                    "personality": asdict(ent.identity.personality),
                    "life_stage": str(ent.identity.life_stage)
                },
                "attributes": asdict(ent.attributes),
                "aptitude": asdict(ent.aptitude),
                "inventory": {
                    "gold": ent.inventory.gold,
                    "items": [{"id": (i.item_id if hasattr(i, "item_id") else i), "q": (i.quantity if hasattr(i, "quantity") else 1)} for i in sorted(ent.inventory.items, key=lambda x: (x.item_id if hasattr(x, "item_id") else x))],
                    "max_slots": ent.inventory.max_slots
                },
                "equipment": {str(k): v for k, v in sorted(ent.equipment.slots.items())},
                "strategic": {
                    "current_project_id": ent.strategic.current_project_id,
                    "current_objective_id": ent.strategic.current_objective_id,
                    "projects": {k: {
                        "kind": v.kind, 
                        "status": str(v.status),
                        "active_objective_id": v.active_objective_id,
                        "objectives": [asdict(o) for o in v.objectives]
                    } for k, v in sorted(ent.strategic.projects.items())},
                    "directives": {k: asdict(v) for k, v in sorted(ent.strategic.directives.items())},
                    "blockers": {k: asdict(v) for k, v in sorted(ent.strategic.blockers.items())},
                    "leads": {k: asdict(v) for k, v in sorted(ent.strategic.leads.items())},
                    "concerns": {k: asdict(v) for k, v in sorted(ent.strategic.concerns.items())},
                    "boredom": dict(sorted(ent.strategic.boredom.items()))
                },
                "social": {
                    "trust_history": {str(k): v for k, v in sorted(ent.social.trust_history.items())},
                    "familiarity_history": {str(k): v for k, v in sorted(ent.social.familiarity_history.items())},
                    "fear_history": {str(k): v for k, v in sorted(ent.social.fear_history.items())},
                    "grudge_history": {str(k): v for k, v in sorted(ent.social.grudge_history.items())},
                    "bonds": {str(k): asdict(v) for k, v in sorted(ent.social.bonds.items())},
                    "betrayal_count": ent.social.betrayal_count,
                    "public_reputation": ent.social.public_reputation,
                    "heroism_score": ent.social.heroism_score,
                    "notoriety_score": ent.social.notoriety_score
                },
                "combat": asdict(ent.combat),
                "biological": asdict(ent.biological),
                "lifecycle": asdict(ent.lifecycle),
                "navigation": {
                    "target": ent.navigation.target,
                    "path": ent.navigation.path,
                    "moved_recently": ent.navigation.moved_recently
                },
                "task": {
                    "work_kind": ent.task.work_kind,
                    "payload": dict(sorted(ent.task.payload.items()))
                },
                "group_id": ent.identity.group_id,
                "properties": dict(sorted(ent.identity.properties.items()))
            }
        data["entities"] = sorted_entities
        
        # 3. Global collections (All sorted by key/id)
        data["regions"] = {k: asdict(v) for k, v in sorted(state.regions.items())}
        data["local_scars"] = {str(k): asdict(v) for k, v in sorted(state.local_scars.items())}
        data["resource_nodes"] = {str(k): asdict(v) for k, v in sorted(state.resource_nodes.items())}
        data["buildings"] = {str(k): asdict(v) for k, v in sorted(state.buildings.items())}
        data["corpses"] = {str(k): asdict(v) for k, v in sorted(state.corpses.items())}
        data["ground_items"] = {str(k): asdict(v) for k, v in sorted(state.ground_items.items())}
        data["chests"] = {str(k): asdict(v) for k, v in sorted(state.chests.items())}
        data["groups"] = {str(k): {
            "id": v.id,
            "leader_id": v.leader_id,
            "member_ids": sorted(list(v.member_ids)),
            "anchor": v.anchor,
            "cohesion_radius": v.cohesion_radius,
            "shared_target_id": v.shared_target_id,
            "contract_id": v.contract_id,
            "last_updated_tick": v.last_updated_tick,
            "roles": {str(eid): role for eid, role in sorted(v.roles.items())},
            "aptitudes": {
                "str": v.str_apt,
                "int": v.int_apt,
                "agi": v.agi_apt,
                "vit": v.vit_apt,
                "end": v.end_apt
            }
        } for k, v in sorted(state.groups.items())}
        data["home_storage"] = {str(k): asdict(v) for k, v in sorted(state.home_storage.items())}
        data["camps"] = {k: asdict(v) for k, v in sorted(state.camps.items())}
        
        data["global_resources"] = dict(sorted(state.global_resources.items()))
        data["periodic_due_ticks"] = dict(sorted(state.periodic_due_ticks.items()))
        data["work_debt"] = dict(sorted(state.work_debt.items()))
        
        data["blocked_tiles"] = sorted([str(t) for t in state.blocked_tiles])
        data["town_tiles"] = sorted([str(t) for t in state.town_tiles])
        data["building_tiles"] = {str(k): v for k, v in sorted(state.building_tiles.items(), key=lambda x: str(x[0]))}
        
        # 4. RNG Checkpoint
        data["rng_checkpoint"] = state.rng_checkpoint
        
        return data
