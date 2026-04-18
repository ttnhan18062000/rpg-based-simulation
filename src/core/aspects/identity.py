from __future__ import annotations
from typing import Any
from pydantic import Field, model_validator
from src.core.models.base import Aspect
from src.core.models.enums import EntityRole, Archetype, ArchetypeSer
from src.core.gameplay.faction import Faction
from src.core.models.life_events import ReputationProfile

class IdentityAspect(Aspect):
    """Aspect handling entity name, faction, role, and tiering. [AOA STABILIZATION]"""
    display_name: str = ""
    faction: Any = Faction.HERO_GUILD
    
    @model_validator(mode="before")
    @classmethod
    def _coerce_faction(cls, data: Any) -> Any:
        if isinstance(data, dict) and "faction" in data:
            from src.core.gameplay.faction import Faction
            val = data["faction"]
            if not isinstance(val, (Faction, int)):
                # Handle string names
                try:
                    data["faction"] = Faction[str(val).upper()]
                except (KeyError, ValueError):
                    pass
        return data
    role: Any = EntityRole.MOB
    tier: int = 0
    difficulty_tier: int = 1
    is_world_boss: bool = False
    hero_class: Any = 0 # HeroClass.NONE
    
    # Pillar 2: Roles & Social Anchoring [PHASE 3]
    world_role: Any = 0 # LifeRole.NONE
    cluster_id: str | None = None
    household_id: str | None = None
    home_building_id: int | None = None
    group_id: str | None = None
    
    # Pillar 1 & 5: Soul & Evolution
    archetype: ArchetypeSer = Archetype.BALANCED
    life_directive: str = "EXPLORATION" # e.g. "CRAFTER", "MONSTER_HUNTER", "GOBLIN_BANE"
    kill_count: int = 0
    
    # Public reputation system [PHASE 2]
    reputation: ReputationProfile = Field(default_factory=ReputationProfile)
    
    # Metadata & Traits
    death_count: int = 0
    generation: int = 1
    traits: list[Any] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    weakness: str = ""
    known_recipes: set[str] = Field(default_factory=set)
    craft_target: str | None = None
    
    # Personality traits removed [PHASE 1] - Moved to MindAspect.decision.personality

    # Archetype template logic moved to PersonalityService/Builder [PHASE 1]

# Rebuild Model to finalize Pydantic setup
IdentityAspect.model_rebuild()
