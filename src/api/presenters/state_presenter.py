from __future__ import annotations
from typing import Dict, Any, List
from src.core.state import AuthoritativeState, EntityState, RegionState

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
