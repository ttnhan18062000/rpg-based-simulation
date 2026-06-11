# Compliance IDs: WORLD-SEM-003, WORLD-SEM-004
from __future__ import annotations

from typing import Optional
from src.core.enums import EntityRole
from src.content.repository import CatalogRepository


class RoleSemanticsService:
    """
    Code-based interpretation of Entity Role catalog definition meaning.
    Performs family queries, legacy mappings, and profile lookups.
    """

    def __init__(self, repo: CatalogRepository):
        self.repo = repo

    def get_legacy_entity_role(self, role_id: str) -> EntityRole:
        """Maps dynamic role string to legacy EntityRole enum."""
        defn = self.repo.get_role(role_id)
        if not defn:
            # Predictable fallback matching legacy string-to-enum mapper
            r = role_id.upper()
            if "HERO" in r:
                return EntityRole.HERO
            elif "SHOP" in r or "STORE" in r:
                return EntityRole.SHOPKEEPER
            elif "MONSTER" in r:
                return EntityRole.MONSTER
            elif "CITIZEN" in r or "CIVILIAN" in r:
                return EntityRole.CITIZEN
            elif "WORKER" in r or "PEASANT" in r:
                return EntityRole.WORKER
            elif "GUARD" in r:
                return EntityRole.GUARD
            return EntityRole.CITIZEN

        try:
            return EntityRole[defn.legacy_engine_role]
        except KeyError:
            return EntityRole.CITIZEN

    def get_role_family(self, role_id: str) -> str:
        """Returns the primary role family (e.g., combatant, worker, civilian)."""
        defn = self.repo.get_role(role_id)
        return defn.role_family if defn else "civilian"

    def get_default_stats_profile(self, role_id: str) -> Optional[str]:
        defn = self.repo.get_role(role_id)
        return defn.default_stats_profile if defn else None

    def get_default_inventory_profile(self, role_id: str) -> Optional[str]:
        defn = self.repo.get_role(role_id)
        return defn.default_inventory_profile if defn else None

    def get_default_cognition_profile(self, role_id: str) -> Optional[str]:
        defn = self.repo.get_role(role_id)
        return defn.default_cognition_profile if defn else None

    def is_combatant(self, role_id: str) -> bool:
        family = self.get_role_family(role_id)
        if family in ("combatant", "adventurer", "recon", "attacker", "ecological_predator", "ecological_leader"):
            return True
        legacy = self.get_legacy_entity_role(role_id)
        return legacy in (EntityRole.HERO, EntityRole.MONSTER, EntityRole.GUARD)

    def is_civilian(self, role_id: str) -> bool:
        family = self.get_role_family(role_id)
        if family in ("civilian", "service", "trade"):
            return True
        legacy = self.get_legacy_entity_role(role_id)
        return legacy in (EntityRole.CITIZEN, EntityRole.SHOPKEEPER)

    def is_worker(self, role_id: str) -> bool:
        family = self.get_role_family(role_id)
        if family in ("worker", "labor"):
            return True
        legacy = self.get_legacy_entity_role(role_id)
        return legacy == EntityRole.WORKER
