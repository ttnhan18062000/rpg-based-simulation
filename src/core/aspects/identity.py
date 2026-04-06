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
    
    # Pillar 1: Behavioral Personality (OCEAN) [PHASE 1]
    openness: float = 0.5          # 0.0 (Routine) to 1.0 (Explorative)
    conscientiousness: float = 0.5 # 0.0 (Impulsive) to 1.0 (Dutiful)
    extraversion: float = 0.5      # 0.0 (Loner) to 1.0 (Social)
    agreeableness: float = 0.5     # 0.0 (Selfish) to 1.0 (Altruistic)
    neuroticism: float = 0.5       # 0.0 (Resilient) to 1.0 (Sensitive)

    def apply_archetype_template(self):
        """Seeds personality traits based on the chosen Archetype template."""
        from src.core.models.enums import Archetype
        
        if self.archetype == Archetype.BALANCED:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.5, 0.5, 0.5, 0.5, 0.5
        elif self.archetype == Archetype.CAUTIOUS_OPPORTUNIST:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.4, 0.7, 0.3, 0.4, 0.6
        elif self.archetype == Archetype.GLORY_SEEKER:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.8, 0.4, 0.9, 0.5, 0.2
        elif self.archetype == Archetype.HONORABLE_DEFENDER:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.3, 0.9, 0.6, 0.8, 0.3
        elif self.archetype == Archetype.GREEDY_SCAVENGER:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.6, 0.5, 0.4, 0.2, 0.4
        elif self.archetype == Archetype.BLOODTHIRSTY_SLAYER:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.5, 0.3, 0.4, 0.1, 0.3
        elif self.archetype == Archetype.COWARDLY_SURVIVOR:
            self.openness, self.conscientiousness, self.extraversion, self.agreeableness, self.neuroticism = 0.2, 0.6, 0.2, 0.4, 0.9

# Rebuild Model to finalize Pydantic setup
IdentityAspect.model_rebuild()
