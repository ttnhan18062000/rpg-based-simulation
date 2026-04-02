from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pydantic import Field
from src.core.models.base import Aspect

if TYPE_CHECKING:
    from src.core.gameplay.classes import SkillInstance
    from src.core.gameplay.attributes import Attributes, AttributeCaps

class ProgressionAspect(Aspect):
    """Aspect handling levelling, XP, gold, skills, and attributes."""
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    fame: int = 0
    stamina: int = 50
    max_stamina: int = 50
    
    # Hero skills and class
    hero_class: int = 0                 # HeroClass enum value
    skills: list[Any] = Field(default_factory=list)
    class_mastery: float = 0.0
    
    # veterancy
    veterancy_points: int = 0
    veterancy_rank: int = 0
    
    # RPG attributes
    attributes: Any = None
    attribute_caps: Any = None
    
    # Genetic Pillar (The Body)
    genetic_seed: int = 0
    age_ticks: int = 0
    longevity_limit: int = 100000        # Max lifecycle in ticks
    aptitudes: dict[str, float] = Field(default_factory=dict)
    
    # Talents & Quests
    talent_points: int = 0
    talents: list[str] = Field(default_factory=list)
    quests: list[Any] = Field(default_factory=list)

    @property
    def stamina_ratio(self) -> float:
        return self.stamina / self.max_stamina if self.max_stamina > 0 else 0.0

    @property
    def xp_ratio(self) -> float:
        return self.xp / self.xp_to_next if self.xp_to_next > 0 else 0.0

    def model_copy(self, **kwargs) -> ProgressionAspect:
        """Ensure nested collections and attributes are copied even on shallow aspect copy."""
        copy_obj = super().model_copy(**kwargs)
        # Copy lists & dicts to ensure isolation
        # Elements in these lists (SkillInstance, Quest) also need to be copied
        copy_obj.skills = [s.copy() if hasattr(s, "copy") else s for s in self.skills]
        copy_obj.talents = list(self.talents)
        copy_obj.quests = [q.copy() if hasattr(q, "copy") else q for q in self.quests]
        copy_obj.aptitudes = dict(self.aptitudes)
        
        if self.attribute_caps and hasattr(self.attribute_caps, "copy"):
            copy_obj.attribute_caps = self.attribute_caps.copy()
        return copy_obj

    def validate(self) -> None:
        """Enforce stamina clamping and progression bounds."""
        if self.stamina > self.max_stamina:
            self.stamina = self.max_stamina
        if self.stamina < 0:
            self.stamina = 0
            
        self.gold = max(0, self.gold)
        self.xp = max(0, self.xp)
        self.level = max(1, self.level)
        self.max_stamina = max(1, self.max_stamina)

    def on_attach(self, owner: Any) -> None:
        """Called when the aspect is attached to an Entity."""
        super().on_attach(owner)
        if self.genetic_seed != 0 and not self.aptitudes:
            self.init_genetics()

    def init_genetics(self) -> None:
        """Initialize aptitudes and longevity from the genetic seed."""
        import random
        rng = random.Random(self.genetic_seed)
        attrs = ["str", "agi", "vit", "int", "spi", "wis", "end", "per", "cha"]
        self.aptitudes = {a: rng.uniform(0.8, 1.25) for a in attrs}
        self.longevity_limit = rng.randint(50000, 150000)


# Rebuild Model to finalize Pydantic setup
ProgressionAspect.model_rebuild()
