# Compliance IDs: WORLD-ASM-003
from __future__ import annotations

from typing import Dict
from src.worldassembly.models import (
    ResolvedEntityProfile,
    ResolvedBuildingProfile,
    ResolvedResourceProfile,
    ResolvedFactionEconomyProfile,
)


class CompileContext:
    """
    Compilation context supplied to WorldCompiler to override legacy hardcoded default parameters
    with catalog-resolved semantic profiles and attributes.
    """

    def __init__(self):
        # Maps spec indices/ids to resolved internal profile definitions
        self.entities: Dict[str, ResolvedEntityProfile] = {}
        self.buildings: Dict[str, ResolvedBuildingProfile] = {}
        self.resources: Dict[str, ResolvedResourceProfile] = {}
        self.factions: Dict[str, ResolvedFactionEconomyProfile] = {}
        
        # Region ownership decisions and legacy mappings
        from src.core.enums import EntityRole, Faction
        self.region_ownership: Dict[str, Faction] = {}
        self.legacy_factions: Dict[str, Faction] = {}
        self.legacy_roles: Dict[str, EntityRole] = {}
        self.provenance: Optional[Any] = None

    def register_entity(self, key: str, profile: ResolvedEntityProfile) -> None:
        self.entities[key] = profile

    def register_building(self, key: str, profile: ResolvedBuildingProfile) -> None:
        self.buildings[key] = profile

    def register_resource(self, key: str, profile: ResolvedResourceProfile) -> None:
        self.resources[key] = profile

    def register_faction(self, key: str, profile: ResolvedFactionEconomyProfile) -> None:
        self.factions[key] = profile

    def register_region_ownership(self, region_id: str, faction: Any) -> None:
        self.region_ownership[region_id] = faction

    def register_legacy_faction(self, faction_str: str, faction: Any) -> None:
        self.legacy_factions[faction_str] = faction

    def register_legacy_role(self, role_str: str, role: Any) -> None:
        self.legacy_roles[role_str] = role

    def set_provenance(self, provenance: Any) -> None:
        self.provenance = provenance
