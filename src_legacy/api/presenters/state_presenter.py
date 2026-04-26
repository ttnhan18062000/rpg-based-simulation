from __future__ import annotations
from typing import Dict, Any, List
from src_legacy.core.state import AuthoritativeState, EntityState, RegionState

class StatePresenter:
    """
    Transforms authoritative state into read-only API models.
    M12 Law: API presenters MUST NOT mutate authoritative state.
    """

    @staticmethod
    def present_minimal(state: AuthoritativeState) -> Dict[str, Any]:
        """Summarized world view."""
        return {
            "tick": state.tick,
            "world_time": state.world_time,
            "entities_count": len(state.entities),
            "maturity": state.maturity,
            "seed": state.seed
        }

    @staticmethod
    def present_full(state: AuthoritativeState) -> Dict[str, Any]:
        """Complete inspectable world view."""
        return {
            "tick": state.tick,
            "world_time": state.world_time,
            "maturity": state.maturity,
            "entities": [StatePresenter.present_entity(e) for e in state.entities.values()],
            "regions": [StatePresenter.present_region(r) for r in state.regions.values()],
            "buildings": [StatePresenter.present_building(b) for b in state.buildings.values()],
            "resource_nodes": [StatePresenter.present_node(n) for n in state.resource_nodes.values()],
            "corpses": [StatePresenter.present_corpse(c) for c in state.corpses.values()],
            "ground_items": [StatePresenter.present_ground_item(i) for i in state.ground_items.values()],
            "local_scars": [StatePresenter.present_scar(s) for s in state.local_scars.values()],
            "global_resources": state.global_resources,
            "status": "ACTIVE"
        }

    @staticmethod
    def present_entity(entity: EntityState) -> Dict[str, Any]:
        """Detailed entity model."""
        return {
            "id": entity.id,
            "kind": entity.kind,
            "position": entity.position,
            "readiness": entity.readiness,
            "active": entity.active,
            "combat": {
                "hp": entity.combat.hp,
                "max_hp": entity.combat.max_hp,
                "atk": entity.combat.atk,
                "def": entity.combat.def_stat,
                "alive": entity.combat.alive
            },
            "inventory": {
                "gold": entity.inventory.gold,
                "item_count": len(entity.inventory.items)
            },
            "strategic": {
                "current_project": entity.strategic.current_project_id,
                "project_count": len(entity.strategic.projects),
                "boredom": entity.strategic.boredom
            },
            "identity": {
                "faction": entity.identity.faction,
                "role": entity.identity.role,
                "level": entity.identity.evolution_level,
                "class": entity.identity.class_id
            }
        }

    @staticmethod
    def present_region(region: RegionState) -> Dict[str, Any]:
        """Detailed regional model."""
        return {
            "id": region.id,
            "name": region.name,
            "owner": region.owner_faction_id,
            "influence": region.influence,
            "hazard": region.hazard_level,
            "kind": region.kind,
            "weather": region.weather
        }

    @staticmethod
    def present_building(building: Any) -> Dict[str, Any]:
        return {
            "id": building.id,
            "kind": building.kind,
            "position": building.position,
            "hp": building.hp,
            "max_hp": building.max_hp,
            "owner_faction_id": building.owner_faction_id,
            "is_destroyed": building.is_destroyed
        }

    @staticmethod
    def present_node(node: Any) -> Dict[str, Any]:
        return {
            "id": node.id,
            "kind": node.kind,
            "position": node.position,
            "remaining_charges": node.remaining_charges,
            "max_charges": node.max_charges,
            "cooldown_remaining": node.cooldown_remaining
        }

    @staticmethod
    def present_corpse(corpse: Any) -> Dict[str, Any]:
        return {
            "id": corpse.id,
            "kind": corpse.kind,
            "position": corpse.position,
            "decay_tick": corpse.decay_tick,
            "owner_id": corpse.owner_id
        }

    @staticmethod
    def present_ground_item(item: Any) -> Dict[str, Any]:
        return {
            "id": item.id,
            "kind": item.item_id,
            "position": item.position,
            "quantity": item.quantity
        }

    @staticmethod
    def present_scar(scar: Any) -> Dict[str, Any]:
        return {
            "id": scar.id,
            "kind": scar.kind,
            "position": scar.position,
            "severity": scar.severity,
            "decay_rate": scar.decay_rate
        }
