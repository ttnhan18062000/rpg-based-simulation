from __future__ import annotations
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import EntityRole
from src.core.gameplay.faction import Faction

class IdentityAspect(Aspect):
    """Aspect handling entity name, faction, role, and tiering."""
    display_name: str = ""
    faction: Any = Faction.HERO_GUILD
    role: Any = EntityRole.MOB
    tier: int = 0
    difficulty_tier: int = 1
    is_world_boss: bool = False
    hero_class: Any = 0 # HeroClass.NONE
    reputation: float = 0.0
    
    # Pillar 1 & 5: Soul & Evolution
    life_directive: str = "EXPLORATION" # e.g. "CRAFTER", "MONSTER_HUNTER", "GOBLIN_BANE"
    kill_count: int = 0
    
    # Metadata & Traits
    death_count: int = 0
    generation: int = 1
    traits: list[Any] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    weakness: str = ""
    hero_familiarity: dict[int, float] = Field(default_factory=dict)
    known_recipes: list[str] = Field(default_factory=list)
    craft_target: str | None = None
    
    # Personality (OCEAN model, 0.0 - 1.0)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
