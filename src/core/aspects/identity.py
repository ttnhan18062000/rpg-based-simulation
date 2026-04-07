from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import EntityRole, Archetype, ArchetypeSer
from src.core.gameplay.faction import Faction

class IdentityAspect(Aspect):
    """Aspect handling entity name, faction, role, and tiering. [AOA STABILIZATION]"""
    display_name: str = ""
    faction: Any = Faction.HERO_GUILD
    role: Any = EntityRole.MOB
    tier: int = 0
    difficulty_tier: int = 1
    is_world_boss: bool = False
    hero_class: Any = 0 # HeroClass.NONE
    
    # Pillar 1 & 5: Soul & Evolution
    archetype: ArchetypeSer = Archetype.BALANCED
    life_directive: str = "EXPLORATION" # e.g. "CRAFTER", "MONSTER_HUNTER", "GOBLIN_BANE"
    kill_count: int = 0
    
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
