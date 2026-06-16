# Compliance IDs: WORLD-ASM-003
from __future__ import annotations

from typing import Dict, Any, Optional
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
        self.perspectives: Dict[str, Any] = {}

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

    def register_perspective(self, perspective_id: str, resolved_def: Any) -> None:
        self.perspectives[perspective_id] = resolved_def if isinstance(resolved_def, dict) else resolved_def.model_dump()

    def set_provenance(self, provenance: Any) -> None:
        self.provenance = provenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": {k: v.model_dump(by_alias=True) for k, v in self.entities.items()},
            "buildings": {k: v.model_dump() for k, v in self.buildings.items()},
            "resources": {k: v.model_dump() for k, v in self.resources.items()},
            "factions": {k: v.model_dump() for k, v in self.factions.items()},
            "region_ownership": {k: int(v) for k, v in self.region_ownership.items()},
            "legacy_factions": {k: int(v) for k, v in self.legacy_factions.items()},
            "legacy_roles": {k: int(v) for k, v in self.legacy_roles.items()},
            "perspectives": dict(self.perspectives),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CompileContext:
        ctx = cls()
        from src.core.enums import EntityRole, Faction
        
        for k, v in data.get("entities", {}).items():
            ctx.register_entity(k, ResolvedEntityProfile.model_validate(v))
        for k, v in data.get("buildings", {}).items():
            ctx.register_building(k, ResolvedBuildingProfile.model_validate(v))
        for k, v in data.get("resources", {}).items():
            ctx.register_resource(k, ResolvedResourceProfile.model_validate(v))
        for k, v in data.get("factions", {}).items():
            ctx.register_faction(k, ResolvedFactionEconomyProfile.model_validate(v))
        for k, v in data.get("region_ownership", {}).items():
            ctx.region_ownership[k] = Faction(v)
        for k, v in data.get("legacy_factions", {}).items():
            ctx.legacy_factions[k] = Faction(v)
        for k, v in data.get("legacy_roles", {}).items():
            ctx.legacy_roles[k] = EntityRole(v)
        for k, v in data.get("perspectives", {}).items():
            ctx.perspectives[k] = v

        return ctx
