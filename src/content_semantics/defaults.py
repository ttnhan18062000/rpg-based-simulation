# Compliance IDs: WORLD-SEM-005, WORLD-SEM-006
from __future__ import annotations

from typing import Dict, Any
from src.content.repository import CatalogRepository


class DefaultSemanticsService:
    """
    Code-based lookup API to retrieve baseline compilation fallback properties
    and metrics from default compile profiles in the catalog repository.
    """

    def __init__(self, repo: CatalogRepository):
        self.repo = repo

    def get_entity_combat_defaults(self) -> Dict[str, Any]:
        """Returns combat default values (hp, atk, def, range, readiness)."""
        defn = self._get_default_definition()
        if not defn:
            return {
                "hp": 100,
                "max_hp": 100,
                "atk": 10,
                "def": 0,
                "attack_range": 1,
                "readiness": 100.0
            }
        return {
            "hp": defn.default_entity_hp,
            "max_hp": defn.default_entity_hp,
            "atk": defn.default_entity_atk,
            "def": defn.default_entity_def,
            "attack_range": defn.default_entity_range,
            "readiness": defn.default_entity_readiness
        }

    def get_building_durability_defaults(self) -> Dict[str, Any]:
        defn = self._get_default_definition()
        if not defn:
            return {
                "hp": 500,
                "max_hp": 500
            }
        return {
            "hp": defn.default_building_hp,
            "max_hp": defn.default_building_hp
        }

    def get_resource_harvest_defaults(self) -> Dict[str, Any]:
        defn = self._get_default_definition()
        if not defn:
            return {
                "required_ticks": 10
            }
        return {
            "required_ticks": defn.default_resource_required_ticks
        }

    def get_faction_vault_defaults(self) -> Dict[str, Any]:
        defn = self._get_default_definition()
        if not defn:
            return {
                "starting_gold": 1000.0
            }
        return {
            "starting_gold": defn.default_faction_starting_gold
        }

    def _get_default_definition(self) -> Any:
        """Finds the first available compile defaults definition in the loaded catalog repository."""
        if not self.repo.defaults:
            return None
        return next(iter(self.repo.defaults.values()))
